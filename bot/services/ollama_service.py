import json

import ollama
from bot.utils.logger import logger


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
        start = response.find("{")
        if start == -1:
            return json.loads(response)
        payload, _ = json.JSONDecoder().raw_decode(response, start)
        return payload
