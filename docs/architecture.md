# Architecture

HeyKanka is organized around an assistant-first flow:

Telegram -> Message Handler -> Memory Service -> SQLite -> Context Builder -> Agent -> Tool Router -> Ollama

Layer responsibilities:

- `bot/database/database.py`: opens SQLite connections and creates tables.
- `bot/database/models.py`: owns SQL queries such as save, load, clear, and pruning.
- `bot/services/memory_service.py`: exposes a stable memory API without SQL knowledge.
- `bot/services/search_service.py`: fetches live web results for current questions.
- `bot/memory/retriever.py`: performs semantic memory retrieval behind the existing `memory.search(...)` API.
- `bot/memory/adapters/`: embedding adapter layer for future backends such as sentence-transformers, FAISS, Chroma, and Qdrant.
- `bot/core/context_builder.py`: builds the full prompt in one place.
- `bot/core/memory_classifier.py`: decides whether a user message deserves long-term memory.
- `bot/core/memory_lifecycle.py`: decides whether memory should be inserted, updated, merged, overwritten, or ignored.
- `bot/core/reflection.py`: reviews draft answers and returns PASS, RETRY, or USE_TOOL.
- `bot/core/tool_router.py`: describes tools, parses tool calls, and executes tools.
- `bot/core/agent.py`: never sees SQL and only works with prepared assistant context.

Storage strategy:

- `messages` stores the full conversation history.
- `memories` is created now for future long-term memory features.
- SQLite keeps all records, while the context builder loads only recent messages and relevant memories for inference.
- Long-term memory is gated by a classifier that returns `NO_MEMORY`, `LOW`, `MEDIUM`, or `HIGH`.
- Memory lifecycle now prevents naive duplication by searching existing memories before saving.
- Semantic retrieval now sits behind `memory.search(...)`, so Agent and Context Builder do not depend on the retrieval backend.
- Reflection reviews draft answers after generation and can request one retry or one extra tool execution.
- Tool calling is currently implemented as a two-step loop: model decides -> tool runs -> model writes the final answer.
- Web search is handled separately: the agent first decides if search is needed, then injects the results back into the final answer prompt.
