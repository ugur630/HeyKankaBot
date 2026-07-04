import json
import re

import ollama
from bot.utils.logger import logger


JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


class OllamaService:
    def __init__(self, model: str) -> None:
        self.model = model

    def generate(self, messages: list[dict[str, str]]) -> str:
        logger.info(
            "LLM input messages: %s",
            json.dumps(messages),
        )
        response = ollama.chat(
            model=self.model,
            messages=messages,
        )
        content = response["message"]["content"]
        logger.info("LLM raw output: %s", content)
        return content

    def generate_yes_no(
        self,
        messages: list[dict[str, str]],
    ) -> bool:
        response = self.generate(messages).strip().upper()
        return response.startswith("YES")

    def generate_json(
        self,
        messages: list[dict[str, str]],
    ) -> dict[str, object]:
        response = self.generate(messages).strip()
        match = JSON_OBJECT_PATTERN.search(response)
        payload = match.group(0) if match else response
        return json.loads(payload)
