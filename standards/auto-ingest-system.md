# 0. Mục tiêu hệ thống

Build một:

```text id="t83kkh"
Personal Autonomous Research & Knowledge Operating System
```

Có khả năng:

* ingest mọi loại content
* autonomous research
* summarize
* knowledge extraction
* graph building
* long-term memory
* AI-agent runtime
* plugin/tool ecosystem
* Telegram/macOS/mobile integration

và hoạt động như một:

```text id="dq1f9z"
AI Agent CLI + Research Infrastructure
```

---

# 1. Kiến trúc cuối cùng (target architecture)

```text id="3j7iqd"
                    ┌─────────────────────┐
                    │ Telegram / Mobile   │
                    │ macOS / API         │
                    └──────────┬──────────┘
                               │
                      Ingestion Gateway
                               │
                    ┌──────────▼──────────┐
                    │ Event Queue         │
                    │ NATS / RedisStream  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Agent Runtime       │
                    │ (Fork OpenCode CLI) │
                    └──────────┬──────────┘
                               │
      ┌────────────────────────┼───────────────────────┐
      │                        │                       │
      ▼                        ▼                       ▼
Scraping Engine        Research Engine          Memory Engine
      │                        │                       │
      ▼                        ▼                       ▼
Playwright           Repo Discovery             PostgreSQL
Whisper              Entity Linking             Vector DB
OCR                  Deep Research              Neo4j
VLM                  Tool Execution             Retrieval
      │                        │                       │
      └────────────────────────┼───────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Summarization Layer │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Notification Layer  │
                    └─────────────────────┘
```

---

# 2. Triết lý implementation

KHÔNG build:

```text id="psuzlm"
URL -> summarize
```

PHẢI build:

```text id="ry16zb"
Persistent evolving AI knowledge infrastructure
```

---

# 3. Nguyên tắc hệ thống

## 3.1 Event-driven

Mọi thứ là event.

Ví dụ:

```text id="k9bn2y"
URL_RECEIVED
SCRAPE_COMPLETED
ENTITIES_EXTRACTED
REPO_FOUND
SUMMARY_CREATED
GRAPH_UPDATED
```

---

## 3.2 Tool-driven agent

Agent không hardcode logic.

Agent chỉ:

```text id="06ji0q"
observe
plan
tool_call
reflect
store_memory
```

---

## 3.3 Memory-first architecture

Memory là core.

Không phải summarize.

---

# 4. Stack đề xuất

## Backend Core

| Component | Tech              |
| --------- | ----------------- |
| API       | FastAPI           |
| Runtime   | Fork OpenCode CLI |
| Queue     | NATS              |
| ORM       | SQLAlchemy        |
| Async     | asyncio           |
| Scheduler | APScheduler       |

---

## AI Layer

| Component  | Tech           |
| ---------- | -------------- |
| LLM        | GPT-5 / Claude |
| Embeddings | bge-m3         |
| OCR        | PaddleOCR      |
| ASR        | Whisper        |
| VLM        | Gemini / GPT   |

---

## Data Layer

| Component  | Tech       |
| ---------- | ---------- |
| Primary DB | PostgreSQL |
| Vector DB  | Qdrant     |
| Graph DB   | Neo4j      |
| Cache      | Redis      |

---

## Scraping Layer

| Component          | Tech        |
| ------------------ | ----------- |
| Browser automation | Playwright  |
| HTML extraction    | trafilatura |
| Video processing   | ffmpeg      |
| Youtube transcript | yt-dlp      |

---

## Deployment

| Component     | Tech           |
| ------------- | -------------- |
| Containers    | Docker         |
| Orchestration | Docker Compose |
| Future        | Kubernetes     |

---

# 5. Folder structure chuẩn

```text id="kx9zgo"
backend/
├── apps/
│   ├── api/
│   ├── worker/
│   ├── telegram/
│   └── scheduler/
│
├── agent/
│   ├── runtime/
│   ├── planner/
│   ├── memory/
│   ├── context/
│   ├── prompts/
│   ├── reflection/
│   └── execution/
│
├── tools/
│   ├── scraping/
│   ├── github/
│   ├── web/
│   ├── graph/
│   ├── embeddings/
│   ├── summarization/
│   └── research/
│
├── ingestion/
│   ├── telegram/
│   ├── youtube/
│   ├── facebook/
│   ├── reddit/
│   ├── medium/
│   └── generic/
│
├── memory/
│   ├── postgres/
│   ├── qdrant/
│   ├── neo4j/
│   └── retrieval/
│
├── pipelines/
│   ├── ingest_pipeline/
│   ├── summarize_pipeline/
│   ├── graph_pipeline/
│   └── research_pipeline/
│
├── plugins/
├── shared/
├── infra/
└── tests/
```

---

# 6. Database design

## 6.1 PostgreSQL tables

### contents

```sql id="aot5m2"
id
source_type
source_url
raw_content
cleaned_content
summary
created_at
updated_at
```

---

### entities

```sql id="vx2q7n"
id
name
type
aliases
metadata
```

---

### relationships

```sql id="a4kgqm"
id
source_entity_id
target_entity_id
relationship_type
confidence
```

---

### memories

```sql id="h2r6k5"
id
memory_type
content
embedding_id
importance_score
```

---

### agent_runs

```sql id="9x79yb"
id
task_type
status
reasoning_trace
started_at
completed_at
```

---

# 7. Vector DB strategy

KHÔNG chỉ lưu summary.

Lưu:

* chunks
* transcript
* comments
* extracted claims
* repo README
* documentation
* prior analyses

---

# 8. Neo4j graph design

## Node types

```text id="13t85o"
Person
Company
Tool
Repository
Paper
Framework
Topic
Post
Video
Concept
```

---

## Edge types

```text id="7th4i7"
CREATED_BY
USES
RELATED_TO
MENTIONED_IN
COMPARED_WITH
INSPIRED_BY
```

---

# 9. Agent Runtime

## 9.1 Fork OpenCode CLI

REMOVE:

* filesystem assumptions
* coding-only prompts
* code editing flows

KEEP:

* execution loop
* streaming
* model abstraction
* session management
* tool execution
* retries

---

# 10. Agent loop chuẩn

```python id="1a7owr"
while not done:
    observe()
    retrieve_memory()
    plan()
    select_tool()
    execute()
    reflect()
    update_memory()
```

---

# 11. Tool System

## Base tool interface

```python id="mvcz7p"
class BaseTool:
    name: str
    description: str

    async def run(self, input):
        pass
```

---

# 12. Tool categories

## Scraping

```text id="f9lm3z"
scrape_url
extract_article
extract_comments
extract_video_frames
```

---

## Research

```text id="4gn6ik"
search_web
find_repo
search_reddit
search_hackernews
```

---

## Knowledge

```text id="72b6f8"
extract_entities
build_graph
query_memory
store_memory
```

---

## Summarization

```text id="1hfh9i"
summarize_short
summarize_technical
summarize_research
```

---

# 13. Ingestion Layer

## Telegram bot

Commands:

```text id="m13eyz"
/analyze
/update
/research
/memory
/graph
/plugin
```

---

## Telegram flow

```text id="33xzzd"
message
 -> parse command
 -> enqueue event
 -> worker execute
 -> response stream
```

---

# 14. Scraping System

## 14.1 Generic extractor

Flow:

```text id="9ew0c5"
URL
 -> detect source
 -> choose adapter
 -> scrape
 -> normalize
```

---

## 14.2 Source adapters

### Facebook

* Playwright
* OCR
* comment extraction

---

### YouTube

* transcript
* metadata
* comments

---

### Medium

* article extraction

---

### GitHub

* README
* stars
* issues
* commit activity

---

# 15. Normalized document schema

```json id="s76dvc"
{
  "title": "",
  "author": "",
  "content": "",
  "comments": [],
  "links": [],
  "media": [],
  "entities": [],
  "metadata": {}
}
```

---

# 16. Research Engine

## Repo discovery flow

```text id="mckqtn"
content
 -> entity extraction
 -> keyword extraction
 -> github search
 -> ranking
 -> confidence scoring
```

---

# 17. Entity Extraction

Extract:

```text id="4zvm5z"
companies
repositories
frameworks
tools
papers
people
concepts
```

---

# 18. Summarization Modes

## Quick

```text id="g6uy8u"
TLDR
```

---

## Technical

```text id="8qkl1s"
architecture
performance
use cases
limitations
```

---

## Research

```text id="pzk8jb"
novelty
comparison
impact
future directions
```

---

# 19. Memory System

## 19.1 Episodic memory

What happened.

---

## 19.2 Semantic memory

Facts/concepts.

---

## 19.3 Procedural memory

How tasks were solved.

---

# 20. Retrieval Strategy

Context assembly:

```text id="p7s2m1"
current task
 + related entities
 + relevant summaries
 + graph neighbors
 + prior memories
```

---

# 21. Reflection System

Sau mỗi task:

```text id="43vw4n"
what was learned?
what entities were discovered?
should graph update?
should long-term memory update?
```

---

# 22. Plugin Architecture

## Plugin manifest

```yaml id="g8r3p0"
name: github_research
version: 1.0.0
tools:
  - github_search
  - repo_analysis
```

---

## Plugin loading

```text id="y57nws"
plugins/
 -> dynamic discovery
 -> registry injection
```

---

# 23. Queue Design

## Events

```text id="8nx7ml"
URL_RECEIVED
SCRAPE_FINISHED
SUMMARY_FINISHED
GRAPH_UPDATED
MEMORY_UPDATED
```

---

# 24. Pipeline breakdown

## 24.1 Analyze pipeline

```text id="x7dfq4"
URL
 -> scrape
 -> normalize
 -> extract entities
 -> find repo
 -> summarize
 -> store
 -> graph update
 -> notify
```

---

## 24.2 Update pipeline

```text id="6v6m5p"
URL
 -> scrape
 -> enrich DB
 -> update graph
```

---

## 24.3 Deep research pipeline

```text id="tjlwmv"
topic
 -> multi-source search
 -> compare
 -> synthesize
 -> generate report
```

---

# 25. AI prompts structure

## Planner prompt

Responsible for:

* task decomposition
* tool selection
* execution planning

---

## Research prompt

Responsible for:

* entity linking
* repo finding
* source validation

---

## Summarizer prompt

Responsible for:

* concise technical output
* structured analysis

---

# 26. macOS app roadmap

## Features

```text id="1fevnr"
share link
clipboard watcher
global hotkey
quick summarize
```

---

## Stack

* Tauri
* React
* Rust backend

---

# 27. Mobile roadmap

## Strategy

Mobile chỉ là thin client.

Cloud xử lý toàn bộ.

---

# 28. Security

## Secrets

* Vault
* env encryption

---

## Sandboxing

Tool execution isolation.

---

## Rate limits

Per-source throttling.

---

# 29. Observability

## Logging

* structured logs

---

## Tracing

* OpenTelemetry

---

## Monitoring

* Prometheus
* Grafana

---

# 30. Testing strategy

## Unit tests

* tools
* extraction
* memory

---

## Integration tests

* pipelines
* queue
* graph updates

---

## Evaluation tests

* summarize quality
* repo matching accuracy
* hallucination checks

---

# 31. CI/CD

## GitHub Actions

```text id="4gk31y"
lint
test
docker build
deploy
```

---

# 32. Deployment phases

## Phase 1 — Local

Docker Compose.

---

## Phase 2 — VPS

Single-node production.

---

## Phase 3 — Kubernetes

Distributed scaling.