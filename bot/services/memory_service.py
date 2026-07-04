from bot.database.database import Database
from bot.database import models
from bot.memory.retriever import SemanticMemoryRetriever

MAX_MEMORY_VALUE_LENGTH = 500


class MemoryService:
    def __init__(
        self,
        database: Database,
        history_limit: int = 15,
        message_retention: int = 50,
        memory_limit: int = 5,
    ) -> None:
        self.database = database
        self.history_limit = history_limit
        self.message_retention = message_retention
        self.memory_limit = memory_limit
        self.memory_retriever = SemanticMemoryRetriever(database)

    def save_message(
        self,
        user_id: int,
        role: str,
        content: str,
    ) -> None:
        models.save_message(self.database, user_id, role, content)

    def load_history(
        self,
        user_id: int,
        limit: int | None = None,
    ) -> list[dict[str, str]]:
        return models.get_last_messages(
            self.database,
            user_id,
            limit=limit or self.history_limit,
        )

    def clear_history(self, user_id: int) -> None:
        models.clear_history(self.database, user_id)

    def delete_old_messages(
        self,
        user_id: int,
        keep: int | None = None,
    ) -> None:
        models.delete_old_messages(
            self.database,
            user_id,
            keep=keep or self.message_retention,
        )

    def remember(
        self,
        user_id: int,
        memory: dict[str, str] | str | None = None,
        *,
        key: str | None = None,
        value: str | None = None,
        importance: int = 1,
    ) -> None:
        resolved_key, resolved_value, resolved_importance = (
            self._resolve_memory_payload(
                memory=memory,
                key=key,
                value=value,
                importance=importance,
            )
        )
        models.save_memory(
            self.database,
            user_id,
            key=resolved_key,
            value=resolved_value,
            importance=resolved_importance,
        )

    def recall(
        self,
        user_id: int,
        query: str = "",
        limit: int | None = None,
    ) -> list[dict[str, str | int]]:
        if query.strip():
            return self.search(
                user_id=user_id,
                query=query,
                limit=limit,
            )

        return models.get_recent_memories(
            self.database,
            user_id,
            limit=limit or self.memory_limit,
        )

    def search(
        self,
        user_id: int,
        query: str,
        limit: int | None = None,
    ) -> list[dict[str, str | int]]:
        return self.memory_retriever.search(
            user_id,
            query,
            limit=limit or self.memory_limit,
        )

    def clear_memories(self, user_id: int) -> None:
        models.clear_memories(self.database, user_id)

    def update_memory(
        self,
        user_id: int,
        memory_id: int,
        memory: dict[str, str] | str | None = None,
        *,
        key: str | None = None,
        value: str | None = None,
        importance: int = 1,
    ) -> bool:
        resolved_key, resolved_value, resolved_importance = (
            self._resolve_memory_payload(
                memory=memory,
                key=key,
                value=value,
                importance=importance,
            )
        )
        return models.update_memory(
            self.database,
            user_id=user_id,
            memory_id=memory_id,
            key=resolved_key,
            value=resolved_value,
            importance=resolved_importance,
        )

    def _resolve_memory_payload(
        self,
        memory: dict[str, str] | str | None,
        key: str | None,
        value: str | None,
        importance: int,
    ) -> tuple[str, str, int]:
        if isinstance(memory, dict):
            memory_text = memory.get("memory", "").strip()
            memory_importance = self._map_importance(
                memory.get("importance", ""),
            )
            return ("fact", self._truncate(memory_text), memory_importance)

        if isinstance(memory, str):
            return ("fact", self._truncate(memory.strip()), importance)

        resolved_key = (key or "fact").strip().lower() or "fact"
        resolved_value = self._truncate((value or "").strip())
        return (resolved_key, resolved_value, importance)

    def _truncate(self, value: str, limit: int = MAX_MEMORY_VALUE_LENGTH) -> str:
        if len(value) <= limit:
            return value
        return value[:limit]

    def _map_importance(self, importance: str) -> int:
        normalized = importance.strip().upper()
        return {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
        }.get(normalized, 1)
