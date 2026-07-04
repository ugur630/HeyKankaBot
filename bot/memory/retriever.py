import math

from bot.database.database import Database
from bot.database import models
from bot.memory.adapters.base import EmbeddingAdapter
from bot.memory.adapters.hashing import HashingEmbeddingAdapter


class SemanticMemoryRetriever:
    def __init__(
        self,
        database: Database,
        embedding_adapter: EmbeddingAdapter | None = None,
        candidate_limit: int = 250,
    ) -> None:
        self.database = database
        self.embedding_adapter = embedding_adapter or (
            HashingEmbeddingAdapter()
        )
        self.candidate_limit = candidate_limit

    def search(
        self,
        user_id: int,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, str | int]]:
        normalized = query.strip()
        if not normalized:
            return models.get_recent_memories(
                self.database,
                user_id,
                limit=limit,
            )

        memories = models.get_all_memories(
            self.database,
            user_id,
            limit=self.candidate_limit,
        )
        if not memories:
            return []

        query_vector = self.embedding_adapter.embed(normalized)
        scored_memories: list[tuple[float, dict[str, str | int]]] = []

        for memory in memories:
            text = self._serialize_memory(memory)
            memory_vector = self.embedding_adapter.embed(text)
            similarity = self._cosine_similarity(
                query_vector,
                memory_vector,
            )
            lexical_bonus = self._lexical_overlap(normalized, text)
            importance_bonus = float(memory["importance"]) * 0.03
            score = similarity + lexical_bonus + importance_bonus

            if score <= 0:
                continue

            scored_memories.append((score, memory))

        scored_memories.sort(
            key=lambda item: (item[0], item[1]["importance"], item[1]["id"]),
            reverse=True,
        )

        return [memory for _, memory in scored_memories[:limit]]

    def _serialize_memory(
        self,
        memory: dict[str, str | int],
    ) -> str:
        return f"{memory['key']} {memory['value']}"

    def _cosine_similarity(
        self,
        left: list[float],
        right: list[float],
    ) -> float:
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return numerator / (left_norm * right_norm)

    def _lexical_overlap(self, query: str, memory_text: str) -> float:
        query_terms = {
            part.lower()
            for part in query.replace(".", " ").split()
            if len(part.strip()) >= 3
        }
        memory_terms = {
            part.lower()
            for part in memory_text.replace(".", " ").split()
            if len(part.strip()) >= 3
        }

        if not query_terms or not memory_terms:
            return 0.0

        overlap = len(query_terms & memory_terms)
        return overlap * 0.08
