# Engineering Standards & Coding Policies

Mục tiêu của policy này:

* Build long-lived system
* Maintainable nhiều năm
* AI-system-ready
* Research-grade software engineering
* Production-grade architecture
* High signal / low entropy codebase
* Dễ scale team trong tương lai
* Dễ audit
* Dễ test
* Dễ refactor
* Dễ evolve architecture

Đây không phải:
“style guide”.

Đây là:
“engineering operating system”.

---

# 1. CORE ENGINEERING PRINCIPLES

# Principle 1 — Explicit > Implicit

KHÔNG:

* magic behavior
* hidden state
* implicit mutation
* dynamic monkey patching

MỌI behavior phải:

* traceable
* predictable
* observable

---

# Principle 2 — Architecture First

Code phải:

* phản ánh architecture
* phản ánh domain boundaries
* phản ánh data flow

KHÔNG organize theo:

* framework convenience
* technical grouping đơn thuần

---

# Principle 3 — Retrieval & AI Systems Are Data Systems

Mọi pipeline:

* deterministic nếu có thể
* reproducible
* observable
* replayable

---

# Principle 4 — Pure Core, Impure Edge

Business logic:

* pure
* side-effect free

I/O:

* isolated

---

# Principle 5 — Event-driven by Default

Long-running operations:

* async
* queued
* retryable
* idempotent

---

# Principle 6 — Markdown Is Canonical

Filesystem là source of truth.

DB chỉ là:

* projection
* index
* retrieval layer

---

# Principle 7 — Optimize for Readability Over Cleverness

Forbidden:

* clever abstractions
* meta-programming abuse
* premature genericization

---

# 2. CODE ORGANIZATION POLICIES

# 2.1 Structure by Domain, NOT by Technical Layer

KHÔNG:

```text id="jlwm80"
models/
controllers/
services/
utils/
```

Đây là architecture entropy.

---

# NÊN

Organize theo bounded context/domain:

```text id="jlwm81"
knowledge/
retrieval/
embedding/
graph/
memory/
ingestion/
notes/
search/
```

---

# 2.2 Internal Domain Structure

Mỗi domain nên có:

```text id="jlwm82"
domain/
    entities/
    value_objects/
    services/
    repositories/
    pipelines/
    events/
    schemas/
    tests/
```

---

# 2.3 Utilities Policy

`utils/` là dangerous anti-pattern.

---

# Rules

## Allowed

Small isolated helpers:

* date formatting
* hashing
* parsing primitives

---

## Forbidden

Generic business logic inside utils.

Ví dụ BAD:

```python id="jlwm83"
utils/process_resource.py
```

---

# 2.4 Shared Package Rules

Shared package chỉ chứa:

* stable primitives
* schemas
* interfaces
* constants

KHÔNG:

* business logic
* orchestration

---

# 3. FILE & MODULE DESIGN POLICIES

# 3.1 File Size Limits

| Type             | Limit    |
| ---------------- | -------- |
| Standard module  | <300 LOC |
| Complex pipeline | <500 LOC |
| Absolute max     | 800 LOC  |

Nếu vượt:

* split by responsibility

---

# 3.2 Function Size Limits

| Type                  | Limit   |
| --------------------- | ------- |
| Normal function       | <40 LOC |
| Complex orchestration | <80 LOC |

---

# 3.3 Nesting Rules

Max nesting:

```text id="jlwm84"
3 levels
```

Nếu sâu hơn:

* extract function
* invert logic

---

# 3.4 One File = One Responsibility

KHÔNG:

```text id="jlwm85"
file parsing
+ DB update
+ embeddings
+ retrieval
```

trong cùng file.

---

# 4. IMPLEMENTATION POLICIES

# 4.1 Business Logic Isolation

Business logic KHÔNG được nằm trong:

* FastAPI routes
* ORM models
* workers
* CLI handlers

---

# GOOD

```text id="jlwm86"
route
 ↓
service
 ↓
domain logic
 ↓
repository
```

---

# 4.2 No Framework Leakage

Core domain không được phụ thuộc:

* FastAPI
* SQLAlchemy
* Redis
* Ollama

---

# GOOD

Domain layer:

* pure Python
* interfaces only

---

# 4.3 Repository Pattern Rules

Repositories:

* ONLY persistence
* NO business logic

---

# BAD

```python id="jlwm87"
repository.generate_summary()
```

---

# GOOD

```python id="jlwm88"
summary_service.generate()
```

---

# 4.4 Service Layer Rules

Services:

* orchestrate workflows
* coordinate repositories
* emit events

KHÔNG:

* heavy data mutation inline
* raw SQL scattered

---

# 4.5 Pipeline Rules

Pipelines phải:

* deterministic
* retryable
* resumable
* idempotent

---

# REQUIRED

Mỗi pipeline step:

* isolated
* testable independently

---

# 5. FUNCTION DESIGN POLICIES

# 5.1 Function Naming

Functions phải:

* explicit
* verb-oriented
* intention-revealing

---

# GOOD

```python id="jlwm89"
extract_wiki_links()
generate_chunk_embeddings()
retrieve_related_resources()
```

---

# BAD

```python id="jlwm90"
handle()
process()
run()
execute()
```

---

# 5.2 Parameter Rules

Max:

```text id="jlwm91"
4 parameters
```

Nếu nhiều hơn:

* use DTO
* use config object

---

# 5.3 Return Rules

KHÔNG:

* return mixed types
* return ambiguous tuples

---

# GOOD

```python id="jlwm92"
SearchResult
EmbeddingResult
ChunkingResult
```

---

# 5.4 Side Effect Rules

Function names phải indicate side effects.

---

# GOOD

```python id="jlwm93"
save_resource()
enqueue_embedding_job()
```

---

# BAD

```python id="jlwm94"
get_resource()
```

nhưng lại mutate DB.

---

# 6. VARIABLE POLICIES

# 6.1 Naming

Variables:

* descriptive
* domain-specific

---

# BAD

```python id="jlwm95"
data
obj
temp
x
res
```

---

# GOOD

```python id="jlwm96"
resource_metadata
semantic_similarity_score
embedding_vector
```

---

# 6.2 Boolean Naming

Must start with:

* is_
* has_
* should_
* can_

---

# GOOD

```python id="jlwm97"
is_archived
has_embeddings
should_reindex
```

---

# 6.3 Immutability Preference

Prefer:

* immutable data
* frozen models
* explicit mutation

---

# 7. TYPE SYSTEM POLICIES

# REQUIRED

Strict typing everywhere.

---

# Python Rules

MUST use:

* mypy strict mode
* typed returns
* typed collections

---

# Forbidden

```python id="jlwm98"
Any
dict
list
```

tràn lan.

---

# GOOD

```python id="jlwm99"
list[ResourceChunk]
dict[str, float]
```

---

# 8. PYDANTIC POLICIES

# REQUIRED

External boundary data:

* always validated

---

# Use For

* API input
* API output
* pipeline contracts
* event payloads

---

# 9. COMMENT POLICIES

# Most Important Rule

Comments giải thích:

* WHY
* invariants
* constraints
* architectural reasoning

KHÔNG explain obvious code.

---

# BAD

```python id="jlwm100"
# Increment counter
counter += 1
```

---

# GOOD

```python id="jlwm101"
# Chunk overlap is required to preserve semantic continuity
# across heading boundaries during retrieval.
```

---

# 10. DOCSTRING POLICIES

# REQUIRED

Public APIs MUST have docstrings.

---

# Style

Google-style docstrings.

---

# REQUIRED CONTENT

* purpose
* invariants
* side effects
* performance implications
* failure modes

---

# GOOD

```python id="jlwm102"
def generate_chunk_embeddings(...) -> EmbeddingResult:
    """
    Generate embeddings for semantic retrieval.

    This function performs markdown-aware chunk embedding generation
    optimized for hybrid retrieval pipelines.

    Side Effects:
        - Persists embeddings to vector storage.

    Constraints:
        - Input chunks must already be normalized.
        - Embedding model must match configured vector dimensions.

    Raises:
        EmbeddingModelUnavailableError:
            If embedding runtime is unavailable.
    """
```

---

# 11. ERROR HANDLING POLICIES

# Forbidden

```python id="jlwm103"
except Exception:
    pass
```

---

# REQUIRED

Use:

* domain-specific exceptions
* structured errors
* contextual logging

---

# GOOD

```python id="jlwm104"
except EmbeddingTimeoutError as error:
```

---

# 12. LOGGING POLICIES

# REQUIRED

Structured logging only.

---

# NEVER

```python id="jlwm105"
print()
```

---

# REQUIRED

Include:

* correlation_id
* resource_id
* pipeline_step
* duration

---

# GOOD

```python id="jlwm106"
logger.info(
    "embedding_generation_completed",
    resource_id=resource_id,
    duration_ms=duration_ms,
)
```

---

# 13. TESTING POLICIES

# MOST IMPORTANT SECTION

---

# 13.1 Testing Pyramid

| Type              | Ratio |
| ----------------- | ----- |
| Unit Tests        | 60%   |
| Integration Tests | 30%   |
| System/E2E Tests  | 10%   |

---

# 13.2 Unit Test Rules

Unit tests MUST:

* isolate business logic
* avoid DB
* avoid network
* avoid filesystem

---

# REQUIRED

Fast:

```text id="jlwm107"
<100ms/test
```

---

# REQUIRED COVERAGE

| Layer             | Coverage |
| ----------------- | -------- |
| Domain logic      | 95%      |
| Retrieval scoring | 95%      |
| Chunking logic    | 95%      |
| Ranking logic     | 95%      |

---

# 13.3 Integration Tests

Test:

* DB
* Redis
* vector retrieval
* pipelines
* file indexing

---

# REQUIRED

Use:

* real Postgres
* real pgvector
* real Redis

KHÔNG mock infra toàn bộ.

---

# 13.4 System Tests

Validate:

* end-to-end workflows
* retrieval quality
* indexing correctness

---

# Example

```text id="jlwm108"
save markdown
 ↓
index
 ↓
embed
 ↓
retrieve semantically
 ↓
validate ranking
```

---

# 13.5 Retrieval Quality Tests

CRITICAL.

---

# MUST TEST

## Semantic Retrieval

Query:

```text id="jlwm109"
agent memory retrieval
```

Expected:

* semantically related resources
* not keyword-only

---

# MUST MEASURE

| Metric            | Minimum |
| ----------------- | ------- |
| Precision@5       | >0.8    |
| Recall@10         | >0.85   |
| Retrieval latency | <300ms  |

---

# 13.6 Graph Tests

Validate:

* backlinks
* traversal correctness
* relation consistency

---

# 13.7 Pipeline Tests

Every pipeline must prove:

* idempotency
* retry safety
* partial failure recovery

---

# REQUIRED TEST

Run same ingestion twice:

* no duplication
* no corruption

---

# 13.8 Mutation Testing

Strongly recommended.

---

# Tools

```text id="jlwm110"
mutmut
cosmic-ray
```

---

# 14. QUALITY GATES

# NOTHING MERGES unless:

---

# REQUIRED

## Static Analysis

Must pass:

* ruff
* mypy
* pytest
* security scan

---

# REQUIRED

## Test Coverage

| Type      | Minimum |
| --------- | ------- |
| Domain    | 95%     |
| Services  | 90%     |
| Pipelines | 90%     |

---

# REQUIRED

## Performance

Semantic retrieval:

```text id="jlwm111"
<300ms
```

---

# REQUIRED

## No Architecture Violations

Use:

* import-linter
* dependency rules

---

# 15. ARCHITECTURE ENFORCEMENT

# REQUIRED

Define dependency directions.

---

# Example

```text id="jlwm112"
domain
 ↑
services
 ↑
api
```

NOT reverse.

---

# Forbidden

```text id="jlwm113"
domain imports FastAPI
domain imports SQLAlchemy
```

---

# 16. DOCUMENTATION POLICIES

# REQUIRED DOCUMENTS

---

# 16.1 ADRs

Architecture Decision Records.

Every major decision:

* context
* tradeoffs
* alternatives
* consequences

---

# REQUIRED

Examples:

* Why markdown-first
* Why pgvector
* Why event-driven

---

# 16.2 Pipeline Specs

Every pipeline:

* inputs
* outputs
* invariants
* retries
* failure modes

---

# 16.3 Retrieval Specs

Document:

* ranking formula
* chunking strategy
* reranking strategy

---

# 17. GIT POLICIES

# Commit Rules

Format:

```text id="jlwm114"
<type>(<scope>): <summary>
```

---

# Examples

```text id="jlwm115"
feat(retrieval): add hybrid reranking pipeline
fix(chunking): preserve heading hierarchy
```

---

# Forbidden

```text id="jlwm116"
fix stuff
update code
```

---

# 18. PR POLICIES

Every PR must include:

* architectural impact
* performance impact
* retrieval impact
* migration impact
* testing evidence

---

# 19. PERFORMANCE POLICIES

# REQUIRED

Benchmark:

* indexing
* retrieval
* embedding
* graph traversal

---

# REQUIRED

Track:

* P50
* P95
* P99 latency

---

# 20. AI-SPECIFIC POLICIES

# NEVER

* hardcode prompts inline
* mix prompts with orchestration
* mutate AI outputs silently

---

# REQUIRED

Version:

* prompts
* models
* retrieval configs

---

# 21. FINAL ENGINEERING STANDARD

Codebase phải đạt:

```text id="jlwm117"
Research-grade architecture
+
Production-grade reliability
+
AI-native extensibility
+
Long-term maintainability
```

KHÔNG chỉ:
“works on my machine”.

---

# 22. FINAL MINDSET

Bạn đang build:

```text id="jlwm118"
knowledge infrastructure
```

không phải:

* CRUD app
* note app
* AI wrapper

Nên mọi tiêu chuẩn phải optimize cho:

* longevity
* semantic integrity
* retrieval quality
* architectural clarity
* evolvability
* observability
* correctness
* reproducibility
