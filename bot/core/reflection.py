from bot.prompts.system_prompt import REFLECTION_PROMPT
from bot.services.ollama_service import OllamaService
from bot.utils.logger import logger


VALID_STATUSES = {"PASS", "RETRY", "USE_TOOL"}


class ReflectionLayer:
    def __init__(self, ollama_service: OllamaService) -> None:
        self.ollama_service = ollama_service

    def review(
        self,
        user_message: str,
        context: list[dict[str, str]],
        draft_answer: str,
    ) -> dict[str, str]:
        messages = [
            {"role": "system", "content": REFLECTION_PROMPT},
            {
                "role": "system",
                "content": self._serialize_context(context),
            },
            {
                "role": "user",
                "content": (
                    f"User Message:\n{user_message}\n\n"
                    f"Draft Answer:\n{draft_answer}"
                ),
            },
        ]
        result = self.ollama_service.generate_json(messages)
        decision = self._normalize_result(result)
        logger.info("Reflection decision: %s", decision)
        return decision

    def _normalize_result(
        self,
        result: dict[str, object],
    ) -> dict[str, str]:
        status = str(
            result.get("status", result.get("decision", "PASS"))
        ).strip().upper()
        if status not in VALID_STATUSES:
            return {"status": "PASS"}

        if status == "PASS":
            return {"status": "PASS"}

        if status == "RETRY":
            reason = str(result.get("reason", "")).strip()
            if not reason:
                reason = "The answer should be improved."
            return {
                "status": "RETRY",
                "reason": reason,
            }

        tool = str(result.get("tool", "")).strip()
        reason = str(result.get("reason", "")).strip()
        if not tool:
            return {"status": "PASS"}

        normalized = {
            "status": "USE_TOOL",
            "tool": tool,
        }
        if reason:
            normalized["reason"] = reason
        return normalized

    def _serialize_context(
        self,
        context: list[dict[str, str]],
    ) -> str:
        if not context:
            return "Context:\n(no context provided)"

        lines = ["Context:"]
        for index, message in enumerate(context, start=1):
            role = message.get("role", "unknown").upper()
            content = message.get("content", "")
            lines.append(f"{index}. {role}: {content}")
        return "\n".join(lines)
