from bot.prompts.system_prompt import MEMORY_CLASSIFIER_PROMPT
from bot.services.ollama_service import OllamaService


VALID_IMPORTANCE = {"NO_MEMORY", "LOW", "MEDIUM", "HIGH"}


class MemoryClassifier:
    def __init__(self, ollama_service: OllamaService) -> None:
        self.ollama_service = ollama_service

    def classify(self, user_message: str) -> dict[str, str]:
        messages = [
            {"role": "system", "content": MEMORY_CLASSIFIER_PROMPT},
            {"role": "user", "content": user_message},
        ]
        result = self.ollama_service.generate_json(messages)
        return self._normalize_result(result)

    def _normalize_result(
        self,
        result: dict[str, object],
    ) -> dict[str, str]:
        importance = str(result.get("importance", "NO_MEMORY")).strip().upper()
        if importance not in VALID_IMPORTANCE:
            return {"importance": "NO_MEMORY"}

        if importance == "NO_MEMORY":
            return {"importance": "NO_MEMORY"}

        memory = str(result.get("memory", "")).strip()
        reason = str(result.get("reason", "")).strip()

        if not memory:
            return {"importance": "NO_MEMORY"}

        normalized = {
            "importance": importance,
            "memory": memory,
        }
        if reason:
            normalized["reason"] = reason

        return normalized
