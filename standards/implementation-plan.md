# Master Plan — AI-native Personal Knowledge Operating System

Mục tiêu của roadmap này:

* Build đúng foundation ngay từ đầu
* Không overengineering
* Có thể chạy local-first
* Có thể scale dần
* Có thể evolve thành:

  * AI memory system
  * research OS
  * agent memory platform
  * semantic knowledge graph

Roadmap này chia thành:

```text id="jlwm54"
Phase 0 → Foundation
Phase 1 → Knowledge Core
Phase 2 → Retrieval System
Phase 3 → AI Enrichment
Phase 4 → Knowledge Graph
Phase 5 → AI-native Workflows
Phase 6 → Sync & Desktop
```

---

# GLOBAL ENGINEERING PRINCIPLES

# Principle 1

Markdown vault là source of truth.

---

# Principle 2

Database chỉ là:

* indexing layer
* semantic layer
* AI layer

---

# Principle 3

Everything is a resource.

---

# Principle 4

Everything must be linkable.

---

# Principle 5

Event-driven architecture từ đầu.

---

# Principle 6

Optimize retrieval quality trước UI quality.

---

# PHASE 0 — FOUNDATIONS

# Goal

Build infrastructure foundation đúng.

---

# Duration

1–2 tuần.

---

# Deliverables

* local-first architecture
* vault structure
* postgres setup
* vector setup
* dockerized infra
* core schema
* event pipeline skeleton

---

# 0.1 Repository Setup

# Structure

```text id="jlwm55"
apps/
  api/
  web/

services/
  ingestion/
  retrieval/
  ai/

packages/
  shared/
  schemas/

vault/

infra/
```

---

# 0.2 Tech Setup

# Install

## Backend

```text id="jlwm56"
FastAPI
SQLAlchemy 2
Alembic
Pydantic
uv
```

---

## Database

```text id="jlwm57"
PostgreSQL
pgvector
Redis
```

---

## AI

```text id="jlwm58"
Ollama
sentence-transformers
LlamaIndex
```

---

## Frontend

```text id="jlwm59"
Next.js
Tailwind
shadcn/ui
Zustand
```

---

# 0.3 Docker Compose

Services:

```text id="jlwm60"
postgres
redis
ollama
api
worker
```

---

# 0.4 Vault Structure

```text id="jlwm61"
vault/
  notes/
  papers/
  youtube/
  concepts/
  daily/
  assets/
```

---

# 0.5 Core Database Schema

Build:

```text id="jlwm62"
vault_files
resources
resource_contents
resource_chunks
chunk_embeddings
notes
wiki_links
tags
resource_tags
```

---

# 0.6 Build Shared Event Bus

Simple initially:

```text id="jlwm63"
Redis pub/sub
```

Events:

```text id="jlwm64"
RESOURCE_CREATED
RESOURCE_UPDATED
NOTE_UPDATED
EMBEDDING_COMPLETED
SUMMARY_COMPLETED
```

---

# Output Of Phase 0

Bạn có:

* infra chạy local
* schema ready
* vault ready
* event architecture ready

---

# PHASE 1 — KNOWLEDGE CORE

# Goal

Build filesystem-native knowledge system.

---

# Duration

2–3 tuần.

---

# Deliverables

* markdown parser
* vault indexing
* wiki links
* metadata extraction
* DB sync

---

# 1.1 Markdown Parsing Engine

# Build

Parser:

* frontmatter
* markdown AST
* wiki links
* headings
* tags

---

# Tech

```text id="jlwm65"
markdown-it-py
python-frontmatter
```

---

# 1.2 File Watcher

# Build

Watch:

* create
* update
* rename
* delete

---

# Tech

```text id="jlwm66"
watchfiles
```

---

# 1.3 Resource Pipeline

Flow:

```text id="jlwm67"
file changed
 ↓
parse
 ↓
normalize
 ↓
upsert DB
```

---

# 1.4 Wiki Link Engine

Parse:

```text id="jlwm68"
[[RAG]]
[[Transformers]]
```

Store:

* forward links
* backlinks

---

# 1.5 Searchable Metadata

Extract:

* tags
* aliases
* headings
* references
* URLs

---

# 1.6 Build CLI Tools

Commands:

```bash id="jlwm69"
index vault
rebuild embeddings
search
graph
```

---

# Output Of Phase 1

Bạn có:

* Obsidian-compatible knowledge core
* filesystem sync
* graph-ready notes
* metadata indexing

---

# PHASE 2 — RETRIEVAL SYSTEM

# Goal

Build powerful retrieval engine.

---

# Duration

2–4 tuần.

---

# Deliverables

* semantic search
* hybrid retrieval
* chunking system
* reranking
* contextual retrieval

---

# 2.1 Chunking System

# Build

Markdown-aware chunking.

---

# Rules

Chunk by:

* headings
* semantic blocks
* sections

KHÔNG fixed-size only.

---

# 2.2 Embedding Pipeline

# Build

Generate:

* chunk embeddings
* note embeddings

---

# Model

Start:

```text id="jlwm70"
bge-small
```

Later:

```text id="jlwm71"
bge-m3
```

---

# 2.3 Vector Search

# Build

pgvector similarity search.

---

# 2.4 Fulltext Search

# Build

Postgres FTS:

* BM25
* ranking
* filters

---

# 2.5 Hybrid Retrieval

# Formula

```text id="jlwm72"
final_score =
semantic_score
+ keyword_score
+ recency_score
+ graph_score
```

---

# 2.6 Reranking

# Add

Cross encoder reranker.

---

# Models

```text id="jlwm73"
bge-reranker
ms-marco
```

---

# 2.7 Context Assembly

Build:

* related chunks
* neighboring notes
* contextual expansion

---

# Output Of Phase 2

Bạn có:

* AI-quality retrieval
* semantic search
* contextual search
* high-quality ranking

---

# PHASE 3 — AI ENRICHMENT

# Goal

Make system AI-native.

---

# Duration

2–3 tuần.

---

# Deliverables

* summaries
* auto tagging
* topic extraction
* entity extraction
* AI artifacts

---

# 3.1 AI Job System

# Build

Async AI workers.

---

# Pipeline

```text id="jlwm74"
resource indexed
 ↓
enqueue AI jobs
 ↓
workers process
```

---

# 3.2 Summary Generation

Generate:

* concise summary
* detailed summary
* key insights

---

# 3.3 Auto Tagging

Generate:

* topics
* concepts
* domains

---

# 3.4 Entity Extraction

Extract:

* tools
* frameworks
* papers
* methodologies

---

# 3.5 Related Resource Generation

Generate:

* semantic neighbors
* related papers
* related notes

---

# 3.6 AI Artifact Storage

Store:

* prompts
* outputs
* versions
* metadata

---

# Output Of Phase 3

Bạn có:

* AI-enriched knowledge base
* automatic organization
* semantic understanding layer

---

# PHASE 4 — KNOWLEDGE GRAPH

# Goal

Build navigable semantic graph.

---

# Duration

2–4 tuần.

---

# Deliverables

* concept graph
* entity graph
* semantic relations
* graph traversal
* graph UI

---

# 4.1 Memory Entities

Build:

* concepts
* technologies
* frameworks
* people

---

# 4.2 Relation Generation

Generate:

* related_to
* inspired_by
* references
* extends

---

# 4.3 Graph Traversal Engine

Queries:

* neighbors
* paths
* backlinks
* concept expansion

---

# 4.4 Graph UI

# Tech

```text id="jlwm75"
React Flow
```

---

# Features

* zoom
* cluster
* neighborhood expansion
* concept navigation

---

# Output Of Phase 4

Bạn có:

* semantic knowledge graph
* concept exploration
* graph-native navigation

---

# PHASE 5 — AI-NATIVE WORKFLOWS

# Goal

Turn system into AI memory OS.

---

# Duration

3–6 tuần.

---

# Deliverables

* conversational memory
* episodic memory
* semantic memory
* AI copilot
* contextual synthesis

---

# 5.1 Conversational Memory

Store:

* sessions
* summaries
* context

---

# 5.2 Episodic Memory

Distill:

* research sessions
* workflows
* discoveries

---

# 5.3 Semantic Memory

Distill:

* reusable knowledge
* durable concepts

---

# 5.4 AI Copilot

Capabilities:

* ask vault
* summarize research
* find contradictions
* synthesize concepts

---

# 5.5 Contextual Retrieval

Build:

* long-context assembly
* adaptive context
* retrieval memory fusion

---

# Output Of Phase 5

Bạn có:

* long-term AI memory
* AI research assistant
* semantic knowledge engine

---

# PHASE 6 — DESKTOP + SYNC

# Goal

Production-grade UX.

---

# Duration

4–8 tuần.

---

# Deliverables

* desktop app
* local sync
* multi-device foundation
* CRDT/event sourcing prep

---

# 6.1 Desktop App

# Tech

```text id="jlwm76"
Tauri
```

---

# 6.2 Local Database Packaging

Bundle:

* postgres
* redis
* ollama

---

# 6.3 Event Sourcing

Add:

* sync events
* operation logs
* replay support

---

# 6.4 Future Sync Layer

Prepare:

* CRDT
* multi-device
* cloud backup

---

# Output Of Phase 6

Bạn có:

* production-ready local-first knowledge OS

---

# PARALLEL TRACKS (IMPORTANT)

# A. Retrieval Evaluation

Liên tục evaluate:

* precision@k
* recall
* hallucination reduction
* context quality

---

# B. Knowledge Density

Optimize:

* graph usefulness
* note linkage
* semantic coherence

---

# C. AI Prompt Engineering

Version:

* prompts
* extraction pipelines
* summaries

---

# D. Performance

Track:

* embedding latency
* retrieval latency
* indexing throughput