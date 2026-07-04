from dataclasses import dataclass

from bot.core.context_builder import ContextBuilder
from bot.core.memory_classifier import MemoryClassifier
from bot.core.memory_lifecycle import MemoryLifecycle
from bot.core.reflection import ReflectionLayer
from bot.core.response_formatter import ResponseFormatter
from bot.core.tool_policy import ToolPolicyEngine
from bot.core.tool_router import ToolRouter
from bot.services.ollama_service import OllamaService
from bot.utils.logger import logger


@dataclass
class DraftResult:
    answer: str
    context_messages: list[dict[str, str]]
    used_tool: str | None = None
    final_response: bool = False
    raw_tool_output: str | None = None


class AssistantAgent:
    def __init__(
        self,
        context_builder: ContextBuilder,
        memory_classifier: MemoryClassifier,
        memory_lifecycle: MemoryLifecycle,
        reflection: ReflectionLayer,
        response_formatter: ResponseFormatter,
        tool_policy: ToolPolicyEngine,
        tool_router: ToolRouter,
        ollama_service: OllamaService,
    ) -> None:
        self.context_builder = context_builder
        self.memory_classifier = memory_classifier
        self.memory_lifecycle = memory_lifecycle
        self.reflection = reflection
        self.response_formatter = response_formatter
        self.tool_policy = tool_policy
        self.tool_router = tool_router
        self.ollama_service = ollama_service

    def generate_reply(
        self,
        user_id: int,
        current_user_message: str,
    ) -> str:
        self._store_long_term_memory_if_needed(
            user_id=user_id,
            current_user_message=current_user_message,
        )

        draft = self._generate_draft(
            user_id=user_id,
            current_user_message=current_user_message,
        )
        return self._reflect_and_finalize(
            user_id=user_id,
            current_user_message=current_user_message,
            draft=draft,
        )

    def _generate_draft(
        self,
        user_id: int,
        current_user_message: str,
    ) -> DraftResult:
        forced_tool = self.tool_policy.decide(current_user_message)
        logger.info("Router decision: forced_tool=%s", forced_tool)
        if forced_tool is not None:
            return self._handle_tool_execution(
                user_id=user_id,
                current_user_message=current_user_message,
                tool_name=forced_tool["tool"],
                tool_input=forced_tool["input"],
            )

        if self._needs_web_search(user_id, current_user_message):
            return self._handle_tool_execution(
                user_id=user_id,
                current_user_message=current_user_message,
                tool_name="search_web",
                tool_input=current_user_message,
            )

        initial_messages = self.context_builder.build_messages(
            user_id=user_id,
            current_user_message=current_user_message,
            tool_instructions=(
                self.tool_router.build_non_search_tool_instructions()
            ),
        )
        initial_response = self.ollama_service.generate(initial_messages)
        tool_call = self.tool_router.parse_tool_call(initial_response)
        logger.info("LLM tool selection result: %s", tool_call)

        if tool_call is None:
            return DraftResult(
                answer=initial_response.strip(),
                context_messages=initial_messages,
            )

        return self._handle_tool_execution(
            user_id=user_id,
            current_user_message=current_user_message,
            tool_name=tool_call["tool"],
            tool_input=tool_call["input"],
        )

    def _needs_web_search(
        self,
        user_id: int,
        current_user_message: str,
    ) -> bool:
        decision_messages = (
            self.context_builder.build_search_decision_messages(
                user_id=user_id,
                current_user_message=current_user_message,
            )
        )
        return self.ollama_service.generate_yes_no(decision_messages)

    def _store_long_term_memory_if_needed(
        self,
        user_id: int,
        current_user_message: str,
    ) -> None:
        classification = self.memory_classifier.classify(
            current_user_message
        )
        if classification.get("importance") == "NO_MEMORY":
            return

        self.memory_lifecycle.apply(
            user_id=user_id,
            memory_payload=classification,
        )

    def _handle_tool_execution(
        self,
        user_id: int,
        current_user_message: str,
        tool_name: str,
        tool_input: str,
    ) -> DraftResult:
        tool_output = self.tool_router.execute(
            tool_name=tool_name,
            tool_input=tool_input,
            user_id=user_id,
        )
        logger.info(
            "Serialized tool result: tool=%s output=%s",
            tool_name,
            tool_output,
        )
        tool_context = self.context_builder.build_tool_followup_messages(
            user_id=user_id,
            current_user_message=current_user_message,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
        )
        logger.info("Tool followup context: %s", tool_context)
        if self.tool_router.is_final_response_tool(tool_name):
            formatted_output = self.response_formatter.format_tool_response(
                tool_name=tool_name,
                raw_output=tool_output,
            )
            draft = DraftResult(
                answer=formatted_output,
                context_messages=tool_context,
                used_tool=tool_name,
                final_response=True,
                raw_tool_output=tool_output,
            )
            logger.info(
                "Final deterministic answer: %s",
                draft.answer,
            )
            return draft

        if tool_name == "search_web":
            search_messages = (
                self.context_builder.build_search_followup_messages(
                    user_id=user_id,
                    current_user_message=current_user_message,
                    search_results=tool_output,
                )
            )
            logger.info("Search followup context: %s", search_messages)
            draft = DraftResult(
                answer=self.ollama_service.generate(search_messages).strip(),
                context_messages=search_messages,
                used_tool=tool_name,
            )
            logger.info("Draft answer after search tool: %s", draft.answer)
            return draft

        final_response = self.ollama_service.generate(tool_context)
        draft = DraftResult(
            answer=final_response.strip(),
            context_messages=tool_context,
            used_tool=tool_name,
        )
        logger.info("Draft answer after tool followup: %s", draft.answer)
        return draft

    def _reflect_and_finalize(
        self,
        user_id: int,
        current_user_message: str,
        draft: DraftResult,
    ) -> str:
        if draft.final_response:
            logger.info(
                "Skipping reflection for deterministic final response."
            )
            logger.info("Final answer: %s", draft.answer)
            return draft.answer

        retry_count = 0
        tool_count = 0
        current_draft = draft

        while True:
            review = self.reflection.review(
                user_message=current_user_message,
                context=current_draft.context_messages,
                draft_answer=current_draft.answer,
            )
            status = review.get("status", "PASS")

            if status == "PASS":
                logger.info("Final answer: %s", current_draft.answer)
                return current_draft.answer

            if status == "RETRY":
                if retry_count >= 1 or current_draft.final_response:
                    logger.info(
                        "Reflection requested retry but returning current answer."
                    )
                    return current_draft.answer
                retry_count += 1
                current_draft = self._retry_draft(
                    context_messages=current_draft.context_messages,
                    reflection_reason=review.get("reason", ""),
                )
                continue

            if status == "USE_TOOL":
                suggested_tool = review.get("tool", "")
                if (
                    tool_count >= 1
                    or not suggested_tool
                    or not self.tool_router.has_tool(suggested_tool)
                ):
                    logger.info(
                        "Reflection requested tool but request cannot be applied."
                    )
                    return current_draft.answer

                tool_count += 1
                current_draft = self._handle_tool_execution(
                    user_id=user_id,
                    current_user_message=current_user_message,
                    tool_name=suggested_tool,
                    tool_input=current_user_message,
                )
                continue

            return current_draft.answer

    def _retry_draft(
        self,
        context_messages: list[dict[str, str]],
        reflection_reason: str,
    ) -> DraftResult:
        feedback = reflection_reason.strip() or "Improve the answer."
        retry_messages = context_messages[:-1] + [
            {
                "role": "system",
                "content": (
                    "Review feedback on the previous draft: "
                    f"{feedback} "
                    "Rewrite the answer to fix the issue. "
                    "Do not mention the review process."
                ),
            },
            context_messages[-1],
        ]
        retry_answer = self.ollama_service.generate(retry_messages).strip()
        return DraftResult(
            answer=retry_answer,
            context_messages=retry_messages,
        )
