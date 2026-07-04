from bot.prompts.system_prompt import MEMORY_LIFECYCLE_PROMPT
from bot.services.memory_service import MemoryService
from bot.services.ollama_service import OllamaService


VALID_ACTIONS = {"INSERT", "UPDATE", "MERGE", "OVERWRITE", "IGNORE"}


class MemoryLifecycle:
    def __init__(
        self,
        memory_service: MemoryService,
        ollama_service: OllamaService,
    ) -> None:
        self.memory_service = memory_service
        self.ollama_service = ollama_service

    def apply(
        self,
        user_id: int,
        memory_payload: dict[str, str],
    ) -> dict[str, str | int | bool]:
        candidate_memory = memory_payload.get("memory", "").strip()
        if not candidate_memory:
            return {"action": "IGNORE", "stored": False}

        existing_memories = self.memory_service.search(
            user_id=user_id,
            query=candidate_memory,
            limit=5,
        )

        if not existing_memories:
            self.memory_service.remember(
                user_id=user_id,
                memory=memory_payload,
            )
            return {"action": "INSERT", "stored": True}

        decision = self._decide(memory_payload, existing_memories)
        return self._apply_decision(user_id, memory_payload, decision)

    def _decide(
        self,
        memory_payload: dict[str, str],
        existing_memories: list[dict[str, str | int]],
    ) -> dict[str, str | int]:
        messages = [
            {"role": "system", "content": MEMORY_LIFECYCLE_PROMPT},
            {
                "role": "system",
                "content": self._format_existing_memories(existing_memories),
            },
            {
                "role": "user",
                "content": (
                    "New candidate memory:\n"
                    f"importance={memory_payload.get('importance', 'LOW')}\n"
                    f"memory={memory_payload.get('memory', '')}\n"
                    f"reason={memory_payload.get('reason', '')}"
                ),
            },
        ]
        result = self.ollama_service.generate_json(messages)
        return self._normalize_decision(result, memory_payload)

    def _apply_decision(
        self,
        user_id: int,
        memory_payload: dict[str, str],
        decision: dict[str, str | int],
    ) -> dict[str, str | int | bool]:
        action = str(decision.get("action", "IGNORE")).upper()

        if action == "IGNORE":
            return {"action": "IGNORE", "stored": False}

        if action == "INSERT":
            self.memory_service.remember(
                user_id=user_id,
                memory={
                    **memory_payload,
                    "memory": str(
                        decision.get("memory", memory_payload["memory"])
                    ),
                },
            )
            return {"action": "INSERT", "stored": True}

        memory_id = int(decision.get("memory_id", 0))
        if memory_id <= 0:
            self.memory_service.remember(
                user_id=user_id,
                memory=memory_payload,
            )
            return {"action": "INSERT", "stored": True}

        updated = self.memory_service.update_memory(
            user_id=user_id,
            memory_id=memory_id,
            memory={
                **memory_payload,
                "memory": str(
                    decision.get("memory", memory_payload["memory"])
                ),
            },
        )
        if not updated:
            self.memory_service.remember(
                user_id=user_id,
                memory=memory_payload,
            )
            return {"action": "INSERT", "stored": True}

        return {"action": action, "stored": True, "memory_id": memory_id}

    def _normalize_decision(
        self,
        result: dict[str, object],
        memory_payload: dict[str, str],
    ) -> dict[str, str | int]:
        action = str(result.get("action", "IGNORE")).strip().upper()
        if action not in VALID_ACTIONS:
            return {"action": "IGNORE"}

        if action == "IGNORE":
            return {"action": "IGNORE"}

        if action == "INSERT":
            memory = str(
                result.get("memory", memory_payload.get("memory", ""))
            ).strip()
            if not memory:
                return {"action": "IGNORE"}
            return {"action": "INSERT", "memory": memory}

        memory_id = self._safe_int(result.get("memory_id"))
        memory = str(
            result.get("memory", memory_payload.get("memory", ""))
        ).strip()
        if memory_id <= 0 or not memory:
            return {"action": "IGNORE"}

        return {
            "action": action,
            "memory_id": memory_id,
            "memory": memory,
        }

    def _format_existing_memories(
        self,
        existing_memories: list[dict[str, str | int]],
    ) -> str:
        lines = ["Existing memories:"]
        for memory in existing_memories:
            lines.append(
                f"- id={memory['id']} key={memory['key']} "
                f"value={memory['value']} importance={memory['importance']}"
            )
        return "\n".join(lines)

    def _safe_int(self, value: object) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
