# Phase 5 — AI-native Workflows: Implementation Record

## Overview

Phase 5 turns Minoverse into an AI Memory OS. It adds four memory layers on top of the knowledge graph built in Phase 4:

| Memory type | What it stores |
|---|---|
| **Conversational** | Sessions + turn-by-turn chat history with the AI copilot |
| **Episodic** | Research sessions distilled by AI into compact narrative memories |
| **Semantic** | Durable, reusable knowledge concepts extracted from any resource |
| **Contextual retrieval** | Runtime assembly of relevant vault context for copilot answers |

The AI Copilot (`/copilot/ask`) ties it all together: it retrieves relevant context from the vault, calls the LLM, saves the conversation, and returns a sourced answer.

---

## New Database Tables

### `memory_sessions`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | gen_random_uuid() |
| title | TEXT | Session display title |
| context | JSONB | Free-form metadata |
| created_at / updated_at | TIMESTAMPTZ | Auto-managed |

### `memory_turns`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| session_id | UUID FK → memory_sessions | CASCADE |
| role | VARCHAR(20) | `user` or `assistant` |
| content | TEXT | Turn text |
| sources | JSONB | Retrieved sources list (nullable) |
| created_at | TIMESTAMPTZ | |

### `episodic_memories`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| title | TEXT | Short episode title |
| content | TEXT | AI-distilled narrative |
| resource_ids | JSONB | Related resource UUIDs |
| session_id | UUID FK → memory_sessions | SET NULL on delete |
| created_at / updated_at | TIMESTAMPTZ | |

### `semantic_memories`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| concept | TEXT | Concept name (e.g. "Attention mechanism") |
| content | TEXT | Durable knowledge about the concept |
| source_resource_id | UUID FK → resources | SET NULL on delete |
| created_at / updated_at | TIMESTAMPTZ | |

---

## Migration

`apps/api/alembic/versions/006_add_memory_phase5.py`

---

## New Backend Files

### ORM Entities (`src/memory/entities/`)
- `memory_session.py` — MemorySession
- `memory_turn.py` — MemoryTurn (FK → memory_sessions)
- `episodic_memory.py` — EpisodicMemory
- `semantic_memory.py` — SemanticMemory

### Schemas (`src/memory/schemas/memory_schemas.py`)
- `MemorySessionOut`, `MemoryTurnOut`, `MemorySessionDetail`
- `EpisodicMemoryOut`, `SemanticMemoryOut`
- `AskRequest`, `AskResponse`

### Repositories (`src/memory/repositories/`)
- `session_repository.py` — create_session, add_turn, get_session_with_turns, list_sessions
- `episodic_repository.py` — create_episode, get_episode, list_episodes
- `semantic_repository.py` — create_semantic, get_semantic, list_semantic, list_for_resource

### Retrieval (`src/retrieval/services/contextual_retrieval_service.py`)
Lightweight ILIKE keyword search across `resource_contents.clean_text` and `ai_enrichments` summaries. Returns ranked list of `{resource_id, title, excerpt, score}` dicts. (Full pgvector retrieval is Phase 2.)

### AI Prompts (`src/ai/prompts/tasks/`)
- `copilot_ask.yaml` — Q&A over vault context; returns `{answer, confidence, cited_resources}`
- `synthesize_episode.yaml` — distils a conversation into `{title, content}`
- `synthesize_semantic.yaml` — extracts durable knowledge as `{concept, content}`

### AI Skills (`src/ai/skills/`)
- `copilot_ask.py` — `run_copilot_ask(question, context, runtime)` → dict
- `synthesize_episode.py` — `run_synthesize_episode(conversation, runtime)` → dict
- `synthesize_semantic.py` — `run_synthesize_semantic(content, runtime)` → dict

All skills follow the existing pattern: graceful error handling, structured logging, JSON extraction.

### Services (`src/memory/services/`)
- `conversation_service.py` — session/turn CRUD
- `episodic_memory_service.py` — `distill_session_to_episode()` via AI
- `semantic_memory_service.py` — `extract_semantic_from_resource()` via AI
- `copilot_service.py` — orchestrator: retrieve context → call AI → save turns → return AskResponse

### Routes (`src/memory/routes.py`)
Two routers registered in `src/main.py`:

| Router | Prefix |
|--------|--------|
| `copilot_router` | `/copilot` |
| `memory_router` | `/memory` |

---

## Modified Files

| File | Change |
|------|--------|
| `src/main.py` | Register `memory_router` and `copilot_router` |
| `alembic/env.py` | Import 4 new ORM models |

---

## Frontend Changes

| File | Change |
|------|--------|
| `src/lib/types.ts` | Add `MemorySession`, `MemoryTurn`, `MemorySessionDetail`, `EpisodicMemory`, `SemanticMemory`, `AskResponse` |
| `src/lib/api.ts` | Add 10 new API functions (copilot + memory) |
| `src/components/layout/sidebar.tsx` | Add 🧠 Copilot and 💡 Memory nav links |
| `src/components/copilot/copilot-chat.tsx` | New: chat UI with session selector, sources panel |
| `src/components/memory/memory-browser.tsx` | New: tabbed episodic + semantic memory browser |
| `src/app/copilot/page.tsx` | New: `/copilot` page |
| `src/app/memory/page.tsx` | New: `/memory` page |

---

## Tests

- **22 backend unit tests** in `src/memory/tests/test_phase5.py` — all passing
- **12 new frontend tests** in `src/__tests__/lib/memory.test.ts` — all passing
- Total: **43/43 frontend tests pass**, **22/22 backend tests pass**
