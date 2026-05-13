# 1. Final Recommended Stack (Production Direction)

| Layer               | Tech                           |
| ------------------- | ------------------------------ |
| Canonical Storage   | Markdown Vault                 |
| Backend API         | FastAPI                        |
| Database            | PostgreSQL                     |
| Vector Search       | pgvector                       |
| Fulltext Search     | PostgreSQL FTS                 |
| ORM                 | SQLAlchemy 2                   |
| Migration           | Alembic                        |
| Queue               | Redis                          |
| Worker              | Celery hoặc Dramatiq           |
| File Watcher        | watchfiles                     |
| Markdown Parser     | markdown-it-py                 |
| Frontmatter Parser  | python-frontmatter             |
| Embeddings          | sentence-transformers / Ollama |
| LLM Runtime         | Ollama                         |
| Chunking/RAG        | LlamaIndex                     |
| Graph Visualization | React Flow / Cytoscape         |
| Desktop App         | Tauri                          |
| UI                  | Next.js                        |
| State Management    | Zustand                        |
| Search Reranking    | cross-encoder                  |
| Local Sync Future   | CRDT/Event Log                 |
| Package Management  | uv                             |
| Containerization    | Docker Compose                 |

---

# 2. Tổng Quan System Architecture

```text id="mq8b3m"
Markdown Vault
    ↓
watchfiles
    ↓
Parsing Pipeline
    ↓
PostgreSQL
    ↓
pgvector
    ↓
Hybrid Retrieval
    ↓
AI Pipeline
    ↓
Graph + UI
```

---

# 3. Canonical Storage Layer

# Tech: Markdown Vault + Filesystem

Đây là quyết định quan trọng nhất.

---

## Mục tiêu

* local-first
* Obsidian-compatible
* git-friendly
* portable
* human-readable
* future-proof

---

## Cách vận hành

```text id="lm9wfs"
vault/
  notes/
  papers/
  youtube/
  concepts/
  daily/
```

Mỗi resource:

* 1 markdown file
* YAML frontmatter
* assets riêng

Ví dụ:

```markdown id="i1v0z2"
---
id: xxx
type: paper
tags:
  - rag
  - llm
---

# Attention Is All You Need
```

---

## Constraint

Markdown vault phải là:

* immutable source of truth
* DB không overwrite trực tiếp
* AI write-back phải controlled

---

## Không nên

* lưu canonical content trong DB
* dùng SQLite làm canonical source
* binary serialization

---

# 4. File Watching Layer

# Tech: `watchfiles`

Khuyên dùng:

* nhẹ
* cực nhanh
* async-native
* tốt hơn watchdog

---

## Vai trò

Theo dõi:

* file create
* modify
* delete
* rename

---

## Flow

```text id="w4xk6f"
markdown changed
    ↓
event emitted
    ↓
parse pipeline
    ↓
reindex
```

---

## Constraint

KHÔNG:

* parse trực tiếp trong watcher
* embedding trực tiếp trong watcher

Watcher chỉ emit event.

---

# 5. Backend Layer

# Tech: FastAPI

Đây là lựa chọn tốt nhất cho use-case của bạn.

---

## Tại sao?

Bạn cần:

* async
* AI pipelines
* websocket
* streaming
* event-driven
* background jobs
* typed API
* local desktop/web hybrid

FastAPI fit hoàn hảo.

---

## Vai trò

### API Layer

```text id="m6vt1u"
search
notes
graph
resources
retrieval
ai memory
```

---

## Flow

```text id="fz41za"
UI
 ↓
FastAPI
 ↓
Retrieval Engine
 ↓
Postgres + pgvector
```

---

## Constraint

KHÔNG:

* business logic trong routes
* embedding logic trong controllers

Nên chia:

```text id="ozfxjr"
api/
services/
repositories/
workers/
pipelines/
```

---

# 6. Database Layer

# Tech: PostgreSQL

Đây là core system database.

---

## Tại sao PostgreSQL?

Bạn cần:

* relational
* graph-ish queries
* JSONB
* fulltext
* vector
* event sourcing
* indexing
* ACID

Postgres làm tốt tất cả.

---

## Vai trò

Lưu:

* metadata
* graph edges
* wiki links
* retrieval indexes
* AI artifacts
* sync events
* episodic memory

---

## Constraint

KHÔNG:

* lưu raw embeddings trong JSON
* lưu large markdown blobs everywhere
* over-normalize

---

## Rất quan trọng

Use:

```sql id="e7b4zy"
JSONB
GIN indexes
Partial indexes
Materialized views
```

---

# 7. Vector Search Layer

# Tech: pgvector

KHÔNG cần Qdrant giai đoạn đầu.

---

## Tại sao pgvector?

Bạn scale:

* vài trăm nghìn resources
* local-first
* single-user initially

pgvector đủ mạnh.

---

## Vai trò

Semantic retrieval:

* chunks
* notes
* semantic memories
* entities

---

## Flow

```text id="x4m8g8"
query
 ↓
embedding
 ↓
vector similarity
 ↓
reranking
```

---

## Constraint

KHÔNG:

* embedding full documents only
* store one vector/resource

Nên:

* chunk-level embeddings
* note-level embeddings
* entity embeddings

---

## Khi nào migrate khỏi pgvector?

Khi:

* > 10M vectors
* distributed retrieval
* multi-tenant massive scale

Lúc đó:

* Qdrant
* Weaviate

---

# 8. Fulltext Search Layer

# Tech: PostgreSQL FTS

---

## Vai trò

Keyword retrieval:

* titles
* tags
* markdown
* summaries

---

## Vì sao không Elasticsearch/OpenSearch ngay?

Overkill.

Postgres FTS:

* đủ nhanh
* zero infra
* local-first friendly

---

## Hybrid Retrieval

Bạn cần:

```text id="h76x5j"
BM25 + Semantic + Graph
```

---

# 9. Embedding Layer

# Tech: sentence-transformers + Ollama

---

## Giai đoạn đầu

Dùng local embeddings.

---

## Recommended Models

### Fast

```text id="waw5om"
bge-small
e5-small
```

---

## Balanced

```text id="snx8b2"
bge-base
bge-m3
```

---

## Strong

```text id="mjlwm9"
nomic-embed-text
bge-large
```

---

## Runtime

# Tech: Ollama

---

## Vai trò

Local:

* embeddings
* summarization
* retrieval
* agent memory

---

## Tại sao Ollama?

* local-first
* simple
* open-source
* standardized API
* dễ replace

---

## Constraint

Tách:

* embedding models
* chat models

KHÔNG reuse 1 model cho mọi task.

---

# 10. Chunking + RAG Layer

# Tech: LlamaIndex

---

## Vai trò

* chunking
* indexing
* retrieval pipelines
* recursive retrieval
* metadata-aware retrieval

---

## Tại sao không LangChain?

LangChain:

* abstraction quá dày
* unstable
* overengineered

LlamaIndex phù hợp hơn cho:

* knowledge systems
* retrieval systems

---

## Constraint

KHÔNG:

* chunk fixed-size only

Nên:

* semantic chunking
* markdown-aware chunking
* heading-aware chunking

---

# 11. Queue Layer

# Tech: Redis + Dramatiq

Tôi recommend Dramatiq thay vì Celery.

---

## Tại sao?

Celery:

* mạnh
* nhưng rất phức tạp

Dramatiq:

* đơn giản
* modern
* đủ dùng
* maintain dễ hơn

---

## Vai trò

Async jobs:

* embeddings
* summaries
* entity extraction
* graph generation

---

## Flow

```text id="xjlwm0"
resource_saved
 ↓
enqueue
 ↓
worker
 ↓
artifact update
```

---

# 12. AI Pipeline Architecture

# Pattern: Event-Driven Pipeline

---

## Flow

```text id="jlwm1x"
markdown changed
 ↓
parse
 ↓
normalize
 ↓
chunk
 ↓
embed
 ↓
summarize
 ↓
extract entities
 ↓
generate graph edges
 ↓
update retrieval indexes
```

---

## Constraint

Mỗi step:

* idempotent
* retryable
* isolated

---

# 13. Graph Layer

# Giai đoạn đầu: PostgreSQL Graph Tables

KHÔNG dùng Neo4j.

---

## Vì sao?

Bạn chỉ cần:

* backlinks
* semantic relations
* entity links
* note graph

Postgres đủ.

---

## Tables

```text id="jlwm2y"
wiki_links
memory_relations
resource_entities
```

---

## Query

Recursive CTE.

---

## Khi nào dùng Neo4j?

Khi:

* deep graph analytics
* graph ML
* path optimization
* massive relation traversal

---

# 14. Frontend Layer

# Tech: Next.js + Tauri

---

# UI Layer

## Next.js

Vai trò:

* document UI
* search UI
* graph UI
* AI chat UI

---

## Tại sao?

* ecosystem mạnh
* React ecosystem
* graph libs mạnh
* desktop compatible

---

# Desktop Layer

## Tauri

KHÔNG Electron.

---

## Tại sao Tauri?

* nhẹ hơn Electron cực nhiều
* Rust backend
* local-first tốt
* filesystem access tốt

---

## Constraint

Tauri chỉ là shell.

Business logic:

* nằm FastAPI backend

---

# 15. State Management

# Tech: Zustand

KHÔNG Redux.

---

## Vì sao?

* lightweight
* local-first apps rất hợp
* graph state tốt

---

# 16. Graph Visualization

# Tech: React Flow

---

## Vai trò

* note graph
* concept graph
* resource graph

---

## Alternative

Cytoscape nếu graph lớn.

---

# 17. Markdown Parsing

# Tech:

* markdown-it-py
* python-frontmatter

---

## Vai trò

Parse:

* frontmatter
* wiki links
* headings
* metadata

---

## Constraint

KHÔNG regex markdown parsing.

---

# 18. Package Manager

# Tech: uv

KHÔNG pip.

---

## Vì sao?

* cực nhanh
* modern
* deterministic
* tốt hơn poetry/pip

---

# 19. Containerization

# Tech: Docker Compose

---

## Giai đoạn đầu

```text id="jlwm3z"
postgres
redis
backend
worker
ollama
```

---

## Constraint

KHÔNG:

* Kubernetes
* microservices
* distributed infra

quá sớm.

---

# 20. Recommended Repository Structure

```text id="jlwm40"
apps/
  desktop/
  web/
  api/

services/
  ingestion/
  retrieval/
  ai/

packages/
  shared/
  schemas/
  prompts/

vault/

infra/
```

---

# 21. Final Recommended Retrieval Stack

# Hybrid Retrieval Pipeline

```text id="jlwm41"
query
 ↓
FTS retrieval
 ↓
semantic retrieval
 ↓
graph expansion
 ↓
reranking
 ↓
context assembly
```

---

# 22. Recommended Reranking

# Tech:

* cross-encoder/ms-marco
* bge-reranker

---

## Vai trò

Rerank:

* semantic candidates
* keyword candidates

---

## Cực kỳ quan trọng

Reranking thường improve retrieval quality nhiều hơn:

* model upgrade
* vector DB upgrade

---

# 23. Local AI Stack

# Recommended

| Purpose            | Model        |
| ------------------ | ------------ |
| Embedding          | bge-m3       |
| Small chat         | qwen3        |
| Reasoning          | deepseek-r1  |
| Fast summarization | phi          |
| Reranking          | bge-reranker |

Run qua:

* Ollama

---

# 24. Final Scaling Strategy

# Phase 1

Local-first monolith:

```text id="jlwm42"
FastAPI
Postgres
pgvector
Redis
Ollama
Markdown Vault
```

---

# Phase 2

Add:

* sync
* cloud backup
* multi-device

---

# Phase 3

Add:

* distributed retrieval
* Qdrant
* OpenSearch
* agent orchestration

---

# 25. Strong Recommendations

## Strongly Recommended

* markdown-first
* postgres-first
* event-driven
* local embeddings
* hybrid retrieval
* chunk-level vectors
* async AI pipeline

---

## Strongly Avoid

* MongoDB-first
* Neo4j-first
* microservices too early
* Electron
* Elasticsearch too early
* LangChain-heavy architecture
* cloud dependency early
* storing canonical content only in DB