import json
import re

from bot.tools.registry import ToolDefinition
from bot.utils.logger import logger


TOOL_CALL_PATTERN = re.compile(
    r"<tool_call>\s*(\{.*?\})\s*</tool_call>",
    re.DOTALL,
)


class ToolRouter:
    def __init__(self, registry: dict[str, ToolDefinition]) -> None:
        self.registry = registry

    def get_tool_definitions(self) -> list[ToolDefinition]:
        return list(self.registry.values())

    def build_tool_instructions(self) -> str:
        tool_lines = []
        for tool in self.get_tool_definitions():
            tool_lines.append(
                f"- {tool.name}: {tool.description} Input: {tool.input_hint}"
            )

        available_tools = "\n".join(tool_lines)
        return (
            "You may use tools when needed.\n"
            "If a tool is required, respond with ONLY this exact XML form:\n"
            '<tool_call>{"tool":"clock","input":"saat kac"}</tool_call>\n'
            "Do not add any other text when calling a tool.\n"
            "If no tool is needed, answer the user normally.\n"
            "Available tools:\n"
            f"{available_tools}"
        )

    def build_non_search_tool_instructions(self) -> str:
        tool_lines = []
        for tool in self.get_tool_definitions():
            if tool.name == "search_web":
                continue
            tool_lines.append(
                f"- {tool.name}: {tool.description} Input: {tool.input_hint}"
            )

        available_tools = "\n".join(tool_lines)
        return (
            "You may use tools when needed.\n"
            "Do not use the search_web tool in this step because web search "
            "is handled separately.\n"
            "If a tool is required, respond with ONLY this exact XML form:\n"
            '<tool_call>{"tool":"clock","input":"saat kac"}</tool_call>\n'
            "Do not add any other text when calling a tool.\n"
            "If no tool is needed, answer the user normally.\n"
            "Available tools:\n"
            f"{available_tools}"
        )

    def parse_tool_call(self, response: str) -> dict[str, str] | None:
        match = TOOL_CALL_PATTERN.search(response)
        if match is None:
            return None

        payload = json.loads(match.group(1))
        tool_name = payload.get("tool", "").strip()
        tool_input = payload.get("input", "").strip()

        if tool_name not in self.registry:
            raise ValueError(f"Unknown tool: {tool_name}")

        return {
            "tool": tool_name,
            "input": tool_input,
        }

    def execute(
        self,
        tool_name: str,
        tool_input: str,
        user_id: int | None = None,
    ) -> str:
        logger.info(
            "Tool execution requested: tool=%s input=%s user_id=%s",
            tool_name,
            tool_input,
            user_id,
        )
        tool = self.registry[tool_name]
        output = tool.handler(tool_input, user_id)
        logger.info("Tool raw result: tool=%s output=%s", tool_name, output)
        return output

    def is_final_response_tool(self, tool_name: str) -> bool:
        return self.registry[tool_name].final_response

    def has_tool(self, tool_name: str) -> bool:
        return tool_name in self.registry
