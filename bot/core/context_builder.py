import json

from bot.prompts.system_prompt import (
    BASE_SYSTEM_PROMPT,
    SEARCH_DECISION_PROMPT,
)
from bot.services.memory_service import MemoryService


class ContextBuilder:
    def __init__(self, memory_service: MemoryService) -> None:
        self.memory_service = memory_service

    def build_messages(
        self,
        user_id: int,
        current_user_message: str,
        tool_instructions: str,
    ) -> list[dict[str, str]]:
        history = self.memory_service.load_history(user_id)
        memories = self._get_relevant_memories(
            user_id=user_id,
            query=current_user_message,
        )
        system_prompt = self._build_system_prompt(tool_instructions)

        return [
            {"role": "system", "content": system_prompt},
            *self._build_memory_messages(memories),
            *history,
            {"role": "user", "content": current_user_message},
        ]

    def build_tool_followup_messages(
        self,
        user_id: int,
        current_user_message: str,
        tool_name: str,
        tool_input: str,
        tool_output: str,
    ) -> list[dict[str, str]]:
        history = self.memory_service.load_history(user_id)
        memories = self._get_relevant_memories(
            user_id=user_id,
            query=current_user_message,
        )

        return [
            {
                "role": "system",
                "content": (
                    f"{BASE_SYSTEM_PROMPT} "
                    "A tool has already been executed for this turn. "
                    "Trusted tool results are the source of truth. "
                    "You must use them exactly as provided. "
                    "Do not guess, replace, override, or contradict tool values. "
                    "If the tool output is missing required data or contains an error, "
                    "say the information is currently unavailable. "
                    "Do not ask for another tool call."
                ),
            },
            *self._build_tool_result_messages(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_output,
            ),
            *self._build_memory_messages(memories),
            *history,
            {"role": "user", "content": current_user_message},
        ]

    def build_search_decision_messages(
        self,
        user_id: int,
        current_user_message: str,
    ) -> list[dict[str, str]]:
        history = self.memory_service.load_history(user_id, limit=5)
        memories = self._get_relevant_memories(
            user_id=user_id,
            query=current_user_message,
        )

        return [
            {"role": "system", "content": SEARCH_DECISION_PROMPT},
            *self._build_memory_messages(memories),
            *history,
            {"role": "user", "content": current_user_message},
        ]

    def build_search_followup_messages(
        self,
        user_id: int,
        current_user_message: str,
        search_results: str,
    ) -> list[dict[str, str]]:
        history = self.memory_service.load_history(user_id)
        memories = self._get_relevant_memories(
            user_id=user_id,
            query=current_user_message,
        )

        return [
            {
                "role": "system",
                "content": (
                    f"{BASE_SYSTEM_PROMPT} "
                    "The provided web search results come from a trusted tool. "
                    "Use only facts that are explicitly present in the trusted search output. "
                    "Do not invent fresher facts, dates, prices, temperatures, or details "
                    "that are not present in the tool output. "
                    "If the exact requested fact is missing or the tool returned an error, "
                    "say the information is currently unavailable. "
                    "Do not call another tool in this step."
                ),
            },
            {
                "role": "system",
                "content": (
                    "Trusted web search tool output:\n"
                    f"{search_results}"
                ),
            },
            *self._build_memory_messages(memories),
            *history,
            {"role": "user", "content": current_user_message},
        ]

    def _build_system_prompt(self, tool_instructions: str) -> str:
        return f"{BASE_SYSTEM_PROMPT} {tool_instructions}"

    def _build_memory_messages(
        self,
        memories: list[dict[str, str | int]],
    ) -> list[dict[str, str]]:
        if not memories:
            return []

        memory_lines = ["Relevant long-term memories:"]
        for memory in memories:
            memory_lines.append(
                f"- {memory['key']}: {memory['value']}"
            )

        return [
            {
                "role": "system",
                "content": "\n".join(memory_lines),
            }
        ]

    def _build_tool_result_messages(
        self,
        tool_name: str,
        tool_input: str,
        tool_output: str,
    ) -> list[dict[str, str]]:
        trusted_lines = [
            "The following information comes from a trusted system tool.",
            "Always use these values exactly as provided.",
            "Do not guess or replace them.",
        ]

        parsed_output = self._parse_tool_output(tool_output)

        if tool_name == "clock" and parsed_output is not None:
            if "date" in parsed_output:
                trusted_lines.append(
                    f"Current Date: {parsed_output['date']}"
                )
            if "time" in parsed_output:
                trusted_lines.append(
                    f"Current Time: {parsed_output['time']}"
                )
            if "datetime" in parsed_output:
                trusted_lines.append(
                    f"Current Datetime: {parsed_output['datetime']}"
                )
            if "error" in parsed_output:
                trusted_lines.append(
                    f"Tool Error: {parsed_output['error']}"
                )
        elif tool_name == "date" and parsed_output is not None:
            if "date" in parsed_output:
                trusted_lines.append(
                    f"Current Date: {parsed_output['date']}"
                )
            if "error" in parsed_output:
                trusted_lines.append(
                    f"Tool Error: {parsed_output['error']}"
                )
        elif tool_name == "weather" and parsed_output is not None:
            for key in (
                "city",
                "temperature_c",
                "feels_like_c",
                "humidity",
                "condition",
                "observation_time_utc",
                "source",
                "error",
            ):
                if key in parsed_output:
                    trusted_lines.append(f"{key}: {parsed_output[key]}")
        else:
            trusted_lines.append(f"Tool Name: {tool_name}")
            trusted_lines.append(f"Tool Input: {tool_input}")
            if parsed_output is not None:
                trusted_lines.append("Structured Tool Output:")
                trusted_lines.append(json.dumps(parsed_output))
            else:
                trusted_lines.append(f"Tool Output: {tool_output}")

        trusted_lines.append(
            "Base the final answer on this trusted tool output."
        )

        return [
            {
                "role": "system",
                "content": "\n".join(trusted_lines),
            }
        ]

    def _parse_tool_output(
        self,
        tool_output: str,
    ) -> dict[str, str] | None:
        try:
            parsed = json.loads(tool_output)
        except json.JSONDecodeError:
            return None

        if not isinstance(parsed, dict):
            return None

        normalized: dict[str, str] = {}
        for key, value in parsed.items():
            normalized[str(key)] = str(value)
        return normalized

    def _get_relevant_memories(
        self,
        user_id: int,
        query: str,
    ) -> list[dict[str, str | int]]:
        memories = self.memory_service.search(
            user_id=user_id,
            query=query,
        )
        if memories:
            return memories

        return self.memory_service.recall(user_id=user_id)
