# Final Database & System Architecture Design

## System Goal

Xây dựng một:

* Local-first AI-native Knowledge Operating System
* Obsidian-compatible Second Brain
* Research-oriented Knowledge Graph
* Long-term AI Memory Infrastructure
* Semantic Retrieval Engine
* AI-ready Markdown Vault

Hệ thống phải support:

* paper
* youtube
* github repo
* docs
* article
* facebook/tiktok/medium posts
* markdown notes
* AI memory
* semantic retrieval
* graph traversal
* auto summarization
* auto tagging
* future sync
* future AI agents
* hundreds of thousands resources

---

# 1. Core Architecture Philosophy

## Source of Truth

Markdown Vault là canonical source.

Database KHÔNG phải nơi lưu content chính.

Database chỉ là:

* indexing layer
* retrieval layer
* semantic layer
* graph layer
* AI layer

---

# 2. High-Level Architecture

```text id="8fy4wd"
Markdown Vault
    ↓
File Watcher
    ↓
Parsing Pipeline
    ↓
PostgreSQL Index DB
    ↓
Embedding Pipeline
    ↓
Semantic + Graph Retrieval
```

---

# 3. Storage Architecture

| Layer             | Technology          |
| ----------------- | ------------------- |
| Canonical content | Markdown filesystem |
| Metadata DB       | PostgreSQL          |
| Vector Search     | pgvector            |
| Fulltext Search   | PostgreSQL FTS      |
| Queue             | Redis               |
| Async Workers     | Celery/RQ           |
| Object Storage    | Local filesystem    |
| File Watcher      | watchfiles          |

---

# 4. Vault Filesystem Structure

```text id="my4dlo"
vault/
├── resources/
│   ├── papers/
│   ├── youtube/
│   ├── github/
│   ├── articles/
│   ├── docs/
│   └── social/
│
├── notes/
│
├── concepts/
│
├── daily/
│
├── assets/
│
└── templates/
```

---

# 5. Final Database Schema

# 5.1 vault_files

Filesystem indexing layer.

```sql id="otz9s9"
vault_files
-----------
id UUID PRIMARY KEY

relative_path TEXT UNIQUE
absolute_path TEXT

file_type TEXT

file_hash TEXT

file_size BIGINT

sync_status TEXT

created_at TIMESTAMP
updated_at TIMESTAMP
last_modified_at TIMESTAMP
```

---

# 5.2 resources

Universal knowledge object.

```sql id="20yr0m"
resources
---------
id UUID PRIMARY KEY

vault_file_id UUID FK

resource_type TEXT

title TEXT
canonical_title TEXT

url TEXT
canonical_url TEXT

source_platform TEXT

author TEXT

language TEXT

published_at TIMESTAMP
saved_at TIMESTAMP

thumbnail_url TEXT

content_hash TEXT
semantic_hash TEXT

importance_score FLOAT
quality_score FLOAT
relevance_score FLOAT

is_favorite BOOLEAN
is_archived BOOLEAN

metadata JSONB

created_at TIMESTAMP
updated_at TIMESTAMP
deleted_at TIMESTAMP
```

---

# Resource Types

```text id="hclv1f"
paper
youtube_video
github_repo
article
documentation
tweet
facebook_post
tiktok_video
note
concept
daily_note
```

---

# 5.3 resource_contents

Normalized parsed content.

```sql id="gq5k1c"
resource_contents
-----------------
id UUID PRIMARY KEY

resource_id UUID FK

content_type TEXT

raw_markdown TEXT

clean_text TEXT

html_content TEXT

transcript_content TEXT

token_count INT
char_count INT

reading_time_minutes INT

version INT

parsed_at TIMESTAMP
created_at TIMESTAMP
```

---

# 5.4 resource_chunks

Chunking layer for RAG + semantic retrieval.

```sql id="75a9qd"
resource_chunks
---------------
id UUID PRIMARY KEY

resource_id UUID FK

chunk_index INT

content TEXT

semantic_label TEXT

token_count INT

start_offset INT
end_offset INT

created_at TIMESTAMP
```

---

# 5.5 chunk_embeddings

Semantic vector layer.

```sql id="xvh5ca"
chunk_embeddings
----------------
chunk_id UUID PRIMARY KEY

embedding VECTOR(1536)

embedding_model TEXT

created_at TIMESTAMP
```

Index:

```sql id="b11j6w"
CREATE INDEX chunk_embedding_idx
ON chunk_embeddings
USING ivfflat (embedding vector_cosine_ops);
```

---

# 5.6 notes

Obsidian-native note system.

```sql id="yz42k6"
notes
-----
id UUID PRIMARY KEY

vault_file_id UUID FK

title TEXT

note_type TEXT

frontmatter JSONB

created_at TIMESTAMP
updated_at TIMESTAMP
```

---

# Note Types

```text id="k6q9gp"
atomic_note
permanent_note
literature_note
fleeting_note
daily_note
concept_note
```

---

# 5.7 wiki_links

Obsidian wiki-link graph.

```sql id="h63pju"
wiki_links
----------
id UUID PRIMARY KEY

source_note_id UUID FK
target_note_id UUID FK

anchor_text TEXT

resolved_resource_id UUID

created_at TIMESTAMP
```

Ví dụ:

```text id="ycit7w"
[[RAG]]
[[Transformers]]
[[Attention Mechanism]]
```

---

# 5.8 tags

Hierarchical tagging system.

```sql id="smjlwm"
tags
----
id UUID PRIMARY KEY

name TEXT UNIQUE

slug TEXT UNIQUE

description TEXT

parent_tag_id UUID
```

---

# 5.9 resource_tags

Hybrid manual + AI tagging.

```sql id="8lgvtj"
resource_tags
-------------
resource_id UUID FK
tag_id UUID FK

generated_by_ai BOOLEAN

confidence_score FLOAT

created_at TIMESTAMP
```

---

# 5.10 ai_artifacts

AI-generated outputs.

```sql id="76mjlwm"
ai_artifacts
------------
id UUID PRIMARY KEY

resource_id UUID FK

artifact_type TEXT

model_name TEXT

content TEXT

metadata JSONB

created_at TIMESTAMP
```

---

# Artifact Types

```text id="g0jlwm"
summary
key_insights
topics
flashcards
questions
mindmap
entity_extraction
auto_tags
```

---

# 5.11 memory_entities

Semantic knowledge graph entities.

```sql id="onjlwm"
memory_entities
---------------
id UUID PRIMARY KEY

name TEXT

entity_type TEXT

canonical_name TEXT

description TEXT

embedding VECTOR(1536)

metadata JSONB

created_at TIMESTAMP
```

---

# Entity Types

```text id="zjlwm0"
concept
technology
paper
framework
research_topic
person
organization
tool
library
methodology
```

---

# 5.12 memory_relations

Simple semantic graph.

```sql id="jlwm1a"
memory_relations
----------------
id UUID PRIMARY KEY

source_entity_id UUID FK
target_entity_id UUID FK

relation_type TEXT

weight FLOAT

generated_by TEXT

created_at TIMESTAMP
```

---

# Relation Types

```text id="jlwm2b"
related_to
mentions
extends
implements
contradicts
references
inspired_by
about
similar_to
```

---

# 5.13 episodic_memories

AI episodic memory layer.

```sql id="jlwm3c"
episodic_memories
-----------------
id UUID PRIMARY KEY

session_id TEXT

memory_type TEXT

summary TEXT

importance_score FLOAT

embedding VECTOR(1536)

occurred_at TIMESTAMP

created_at TIMESTAMP
```

---

# Memory Types

```text id="jlwm4d"
conversation
agent_action
learning_event
research_session
decision
insight
```

---

# 5.14 semantic_memories

Long-term distilled memory.

```sql id="jlwm5e"
semantic_memories
-----------------
id UUID PRIMARY KEY

title TEXT

content TEXT

source_resource_id UUID

confidence_score FLOAT

embedding VECTOR(1536)

created_at TIMESTAMP
```

---

# 5.15 collections

Logical grouping system.

```sql id="jlwm6f"
collections
-----------
id UUID PRIMARY KEY

name TEXT

description TEXT

collection_type TEXT

created_at TIMESTAMP
```

---

# 5.16 collection_resources

```sql id="jlwm7g"
collection_resources
--------------------
collection_id UUID FK
resource_id UUID FK

position INT

created_at TIMESTAMP
```

---

# 5.17 ingestion_jobs

Async ingestion pipeline.

```sql id="jlwm8h"
ingestion_jobs
--------------
id UUID PRIMARY KEY

source_type TEXT

source_url TEXT

status TEXT

raw_payload JSONB

started_at TIMESTAMP
completed_at TIMESTAMP

error_message TEXT
```

---

# 5.18 ai_jobs

Async AI processing.

```sql id="jlwm9i"
ai_jobs
-------
id UUID PRIMARY KEY

resource_id UUID FK

job_type TEXT

status TEXT

priority INT

started_at TIMESTAMP
completed_at TIMESTAMP

error_message TEXT
```

---

# Job Types

```text id="jlwm0j"
chunking
embedding
summarization
tagging
entity_extraction
relation_generation
memory_distillation
```

---

# 5.19 sync_events

Future sync/event sourcing layer.

```sql id="jlwm1k"
sync_events
-----------
id UUID PRIMARY KEY

event_type TEXT

entity_type TEXT

entity_id UUID

payload JSONB

created_at TIMESTAMP
```

---

# 5.20 resource_interactions

Behavior + ranking layer.

```sql id="jlwm2l"
resource_interactions
---------------------
id UUID PRIMARY KEY

resource_id UUID FK

interaction_type TEXT

duration_seconds INT

interaction_score FLOAT

last_accessed_at TIMESTAMP

created_at TIMESTAMP
```

---

# Interaction Types

```text id="jlwm3m"
view
read
highlight
search_click
ai_reference
note_reference
review
favorite
```

---

# 6. Retrieval Architecture

## Hybrid Retrieval System

---

## 6.1 Fulltext Retrieval

PostgreSQL FTS:

* title
* markdown
* summaries
* notes
* AI outputs

---

## 6.2 Semantic Retrieval

pgvector on:

* chunk_embeddings
* semantic_memories
* memory_entities
* episodic_memories

---

## 6.3 Graph Retrieval

Using:

* wiki_links
* memory_relations

---

## 6.4 Temporal Retrieval

Using:

* daily notes
* timestamps
* interaction history

---

# 7. AI Memory Architecture

## Multi-layer Memory System

---

## Layer 1 — Raw Knowledge

```text id="jlwm4n"
markdown
resources
notes
```

---

## Layer 2 — Episodic Memory

```text id="jlwm5o"
research sessions
conversations
agent actions
```

---

## Layer 3 — Semantic Memory

```text id="jlwm6p"
distilled reusable knowledge
```

---

## Layer 4 — Knowledge Graph

```text id="jlwm7q"
concept relations
entity relations
note graph
```

---

# 8. File Watcher Pipeline

```text id="jlwm8r"
markdown changed
    ↓
parse frontmatter
    ↓
extract links
    ↓
normalize content
    ↓
chunk content
    ↓
generate embeddings
    ↓
generate summary
    ↓
generate tags
    ↓
extract entities
    ↓
update retrieval indexes
```

---

# 9. Event-Driven AI Pipeline

```text id="jlwm9s"
resource_saved
    ↓
enqueue_ai_jobs
    ↓
worker_processing
    ↓
artifact_generation
    ↓
memory_update
    ↓
relation_update
```

---

# 10. Search Modes Supported

| Search Type                     | Supported |
| ------------------------------- | --------- |
| Keyword search                  | YES       |
| Semantic search                 | YES       |
| Graph traversal                 | YES       |
| Time-based retrieval            | YES       |
| Contextual AI retrieval         | YES       |
| Related-resource recommendation | YES       |
| Note backlink traversal         | YES       |

---

# 11. Final Design Principles

## Principle 1

Everything is a resource.

---

## Principle 2

Everything is linkable.

---

## Principle 3

Markdown vault is canonical.

---

## Principle 4

Database is an intelligence layer.

---

## Principle 5

AI outputs are replaceable artifacts.

---

## Principle 6

Retrieval quality > storage complexity.

---

# 12. Recommended Tech Stack

| Layer        | Recommended         |
| ------------ | ------------------- |
| Backend      | FastAPI             |
| ORM          | SQLAlchemy 2        |
| Database     | PostgreSQL          |
| Vector DB    | pgvector            |
| Queue        | Redis               |
| Workers      | Celery/RQ           |
| File Watcher | watchfiles          |
| Parsing      | markdown-it-py      |
| Embeddings   | OpenAI/local model  |
| Storage      | Local filesystem    |
| Sync Future  | CRDT/event sourcing |