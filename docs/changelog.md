# Changelog

## 2026-07-03

- Reorganized the project around a `bot/` package.
- Added `core`, `database`, `prompts`, `tools`, `utils`, and `docs` layers.
- Moved conversation memory to SQLite-backed persistence.
- Added v0.5 tool-calling foundations with `clock` and `calculator`.

## 2026-07-04

- Added long-term memory APIs with `remember`, `recall`, and `search`.
- Upgraded the context builder to include relevant memories.
- Added `search_web` and a search-decision step before final response generation.
- Added `MemoryClassifier` and a memory-importance layer for selective long-term storage.
- Added `MemoryLifecycle` to support INSERT, UPDATE, MERGE, OVERWRITE, and IGNORE decisions.
- Replaced SQLite LIKE-based memory search with adapter-ready semantic retrieval behind the same `memory.search(...)` API.
- Added a Reflection Layer that can PASS, RETRY once, or request one additional tool execution.
