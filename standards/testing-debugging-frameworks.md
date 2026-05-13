# Enterprise-Grade Testing & Debugging Standards

Đây là:

* testing operating system
* debugging operating system
* quality governance framework

cho:

* AI-native systems
* retrieval systems
* knowledge systems
* event-driven architectures
* semantic infrastructures

Mục tiêu:

```text id="jlwm119"
Correctness
Reliability
Observability
Determinism
Recoverability
Maintainability
Regression resistance
```

---

# 1. CORE TESTING PHILOSOPHY

# Principle 1 — Testing Is Specification

Tests không phải:

* “check code chạy”

Tests là:

* executable system specification

---

# Principle 2 — Every Bug Becomes A Permanent Test

Mỗi bug:

* phải có regression test
* trước khi fix được merge

---

# Principle 3 — Test Behavior, Not Implementation

KHÔNG test:

* private methods
* ORM internals
* framework behavior

Test:

* observable outcomes
* contracts
* invariants

---

# Principle 4 — Critical Paths Must Be Deterministic

AI systems có stochasticity.

Nhưng:

* pipelines
* indexing
* retrieval scoring
* event flows

phải deterministic nếu có thể.

---

# Principle 5 — High Signal Testing

KHÔNG:

* snapshot spam
* meaningless assertions
* coverage theater

---

# Principle 6 — Production-Like Testing

Integration/system tests:

* dùng real infra
* real Postgres
* real Redis
* real pgvector

KHÔNG over-mock.

---

# 2. TESTING ARCHITECTURE

# Testing Pyramid

| Layer         | Ratio | Purpose              |
| ------------- | ----- | -------------------- |
| Unit          | 60%   | business correctness |
| Integration   | 25%   | infra correctness    |
| System/E2E    | 10%   | workflow correctness |
| Performance   | 3%    | latency/scaling      |
| Chaos/Failure | 2%    | resilience           |

---

# 3. REQUIRED TEST CATEGORIES

# 3.1 Unit Tests

# Scope

Test:

* pure business logic
* retrieval formulas
* ranking
* chunking
* parsers
* graph traversal logic

---

# MUST NOT

* DB
* filesystem
* network
* Redis
* Ollama

---

# REQUIRED

Fast:

```text id="jlwm120"
<100ms/test
```

---

# REQUIRED CHARACTERISTICS

| Requirement      | Mandatory |
| ---------------- | --------- |
| deterministic    | YES       |
| isolated         | YES       |
| reproducible     | YES       |
| side-effect free | YES       |

---

# Example

```python id="’wini121"
def test_hybrid_score_prioritizes_semantic_similarity():
```

---

# 3.2 Integration Tests

# Scope

Test:

* DB
* vector search
* Redis
* file watcher
* pipelines
* repositories

---

# MUST USE

* real Postgres
* real pgvector
* real Redis

---

# MUST TEST

| System            | Required |
| ----------------- | -------- |
| migrations        | YES      |
| indexes           | YES      |
| constraints       | YES      |
| transactions      | YES      |
| rollback behavior | YES      |

---

# Example

```text id="jlwm122"
save resource
→ generate embeddings
→ retrieve resource
```

---

# 3.3 System / E2E Tests

# Scope

Validate:

* full workflows
* business scenarios
* AI retrieval flows
* indexing lifecycle

---

# Example

```text id="jlwm123"
markdown added
 ↓
watcher detects
 ↓
parse
 ↓
chunk
 ↓
embed
 ↓
index
 ↓
searchable
```

---

# REQUIRED

Test:

* async workflows
* retries
* event ordering
* pipeline orchestration

---

# 3.4 Retrieval Quality Tests

CRITICAL CATEGORY.

---

# MUST TEST

## Semantic Retrieval

Query:

```text id="’wini124"
agent memory retrieval
```

Expected:

* semantically relevant results
* not keyword-only matches

---

# MUST TEST

## Synonym Recall

```text id="
```


memory

````

must retrieve:
- context storage
- episodic recall
- long-term memory

---

# MUST TEST

## Conceptual Similarity

```text id="’wini126"
reranking
````

must retrieve:

* cross encoder
* late interaction retrieval
* ColBERT

---

# REQUIRED METRICS

| Metric      | Minimum |
| ----------- | ------- |
| Precision@5 | >0.80   |
| Recall@10   | >0.85   |
| MRR         | >0.75   |
| NDCG        | >0.80   |

---

# 3.5 AI Pipeline Tests

# MUST VALIDATE

| Concern                  | Required |
| ------------------------ | -------- |
| idempotency              | YES      |
| retry safety             | YES      |
| timeout handling         | YES      |
| partial failure recovery | YES      |
| duplicate event handling | YES      |

---

# REQUIRED TESTS

## Reprocessing

Run ingestion twice:

* no duplicates
* no corruption

---

## Failure Recovery

Kill worker mid-pipeline:

* recovery successful?

---

## Timeout Recovery

Embedding timeout:

* retry behavior correct?

---

# 3.6 Graph Tests

# MUST TEST

| Concern               | Required |
| --------------------- | -------- |
| backlinks             | YES      |
| relation integrity    | YES      |
| traversal correctness | YES      |
| orphan handling       | YES      |

---

# Example

```text id="’wini127"
[[RAG]]
[[Embeddings]]
```

Must:

* generate graph edges
* maintain backlinks

---

# 3.7 Migration Tests

EVERY migration must be tested.

---

# REQUIRED

## Forward Migration

Old DB → new schema.

---

## Rollback Migration

New schema → old schema.

---

## Data Integrity

No corruption.

---

# 3.8 Concurrency Tests

# MUST TEST

| Concern            | Required |
| ------------------ | -------- |
| concurrent writes  | YES      |
| duplicate indexing | YES      |
| race conditions    | YES      |
| locking behavior   | YES      |

---

# Example

100 simultaneous markdown updates.

Expected:

* no corruption
* no duplicate chunks

---

# 3.9 Performance Tests

# REQUIRED

Benchmark:

| Operation          | Target   |
| ------------------ | -------- |
| semantic retrieval | <300ms   |
| FTS retrieval      | <100ms   |
| graph traversal    | <200ms   |
| indexing           | scalable |
| embedding queue    | stable   |

---

# REQUIRED

Measure:

* P50
* P95
* P99

---

# 3.10 Chaos / Failure Tests

Advanced but important.

---

# MUST TEST

| Failure            | Required |
| ------------------ | -------- |
| Redis unavailable  | YES      |
| DB restart         | YES      |
| worker crash       | YES      |
| Ollama unavailable | YES      |

---

# REQUIRED

System:

* degrades gracefully
* recovers automatically

---

# 4. TEST WRITING RULES

# 4.1 Naming Convention

Pattern:

```text id="’wini128"
test_<behavior>_<expected_result>
```

---

# GOOD

```python id="’wini129"
test_semantic_search_returns_related_concepts()
```

---

# BAD

```python id="’wini130"
test_search()
```

---

# 4.2 Arrange / Act / Assert

Mandatory structure.

---

# GOOD

```python id="’wini131"
# Arrange
resource = ...

# Act
result = search(...)

# Assert
assert ...
```

---

# 4.3 One Assertion Domain Per Test

Test:

* one behavior
* one invariant

---

# BAD

Huge mixed tests.

---

# 4.4 Deterministic Fixtures

Fixtures MUST:

* isolated
* reproducible
* immutable where possible

---

# NEVER

Depend on:

* production DB
* internet
* external APIs

---

# 5. TEST DATA POLICIES

# REQUIRED

Use:

* realistic data
* markdown samples
* real retrieval scenarios

---

# BAD

```text id="’wini132"
foo
bar
test document
```

---

# GOOD

Real:

* papers
* notes
* markdown vault samples

---

# 6. MOCKING POLICIES

# Mock ONLY:

| Allowed           | Example    |
| ----------------- | ---------- |
| external APIs     | OpenAI     |
| payment providers | Stripe     |
| unstable services | cloud APIs |

---

# NEVER OVER-MOCK

Do NOT mock:

* Postgres
* Redis
* vector retrieval
* repositories

---

# 7. QUALITY GATES

# NOTHING MERGES unless:

---

# REQUIRED

## Static Analysis Passes

Must pass:

* ruff
* mypy strict
* pytest
* security scan

---

# REQUIRED

## Coverage

| Layer     | Minimum |
| --------- | ------- |
| Domain    | 95%     |
| Services  | 90%     |
| Pipelines | 90%     |

---

# REQUIRED

## Retrieval Metrics

Must not regress.

---

# REQUIRED

## Performance Budgets

Must stay within:

* latency budgets
* memory budgets

---

# 8. REGRESSION TESTING POLICY

Every bug:

* reproduce
* create failing test
* fix
* verify regression test passes

---

# REQUIRED PROCESS

```text id="’wini133"
bug found
 ↓
write failing test
 ↓
fix implementation
 ↓
verify pass
 ↓
merge
```

---

# 9. TEST EXECUTION STRATEGY

# CI Pipeline Order

---

# Stage 1

Static analysis:

* ruff
* mypy
* imports
* formatting

---

# Stage 2

Unit tests.

---

# Stage 3

Integration tests.

---

# Stage 4

System tests.

---

# Stage 5

Performance smoke tests.

---

# Stage 6

Security scans.

---

# 10. REQUIRED REPORTING

# Every Test Run Must Report

| Metric      | Required |
| ----------- | -------- |
| passed      | YES      |
| failed      | YES      |
| skipped     | YES      |
| duration    | YES      |
| coverage    | YES      |
| flaky tests | YES      |

---

# REQUIRED

Performance regression report.

---

# REQUIRED

Retrieval quality regression report.

---

# 11. FLAKY TEST POLICY

Flaky tests are:

* production bugs
* architecture bugs
* determinism bugs

NOT acceptable.

---

# REQUIRED

Every flaky test:

* quarantined
* root-caused
* fixed immediately

---

# 12. DEBUGGING OPERATING SYSTEM

# Core Principle

Debugging is:

* system investigation
* evidence collection
* hypothesis validation

NOT:

* random trial/error

---

# 13. DEBUGGING METHODOLOGY

# Step 1 — Reproduce

Must reproduce:

* consistently
* minimally

---

# Step 2 — Isolate

Determine:

* layer
* component
* dependency
* event chain

---

# Step 3 — Observe

Collect:

* logs
* metrics
* traces
* DB state
* queue state

---

# Step 4 — Hypothesize

Form:

* explicit hypothesis
* measurable expectations

---

# Step 5 — Validate

Run:

* targeted experiments
* instrumentation
* state inspection

---

# Step 6 — Permanent Fix

Fix:

* root cause
* not symptoms

---

# Step 7 — Regression Test

Mandatory.

---

# 14. DEBUGGING RULES

# NEVER

* debug blindly
* add random sleeps
* “fix” race conditions accidentally
* suppress exceptions

---

# NEVER

```python id="’wini134"
except Exception:
    pass
```

---

# 15. REQUIRED OBSERVABILITY

# System MUST expose:

| Signal           | Required |
| ---------------- | -------- |
| structured logs  | YES      |
| metrics          | YES      |
| tracing          | YES      |
| correlation IDs  | YES      |
| queue visibility | YES      |

---

# 16. LOGGING STANDARDS

# REQUIRED

Structured logs only.

---

# Every log MUST include

| Field          | Required |
| -------------- | -------- |
| timestamp      | YES      |
| correlation_id | YES      |
| resource_id    | YES      |
| pipeline_step  | YES      |
| duration       | YES      |

---

# GOOD

```python id="’wini135"
logger.info(
    "chunk_embedding_completed",
    resource_id=resource_id,
    chunk_count=chunk_count,
    duration_ms=duration_ms,
)
```

---

# 17. RETRIEVAL DEBUGGING

CRITICAL FOR YOUR SYSTEM.

---

# MUST DEBUG

| Concern             | Required |
| ------------------- | -------- |
| missing retrievals  | YES      |
| poor ranking        | YES      |
| semantic drift      | YES      |
| chunk fragmentation | YES      |

---

# REQUIRED TOOLS

Build:

* retrieval explainability
* score breakdowns
* embedding inspection
* reranking inspection

---

# Example

```text id="’wini136"
semantic_score = 0.82
keyword_score = 0.30
graph_score = 0.15
final = 1.27
```

---

# 18. PIPELINE DEBUGGING

# REQUIRED

Every pipeline step:

* independently executable
* replayable
* inspectable

---

# MUST SUPPORT

```text id="’wini137"
re-run chunking
re-run embeddings
re-run summaries
```

without full reindex.

---

# 19. DATABASE DEBUGGING

# REQUIRED

Tools:

* slow query analysis
* index analysis
* query plans
* lock inspection

---

# REQUIRED

Track:

* N+1 queries
* sequential scans
* vector scan latency

---

# 20. AI SYSTEM DEBUGGING

# MUST TRACK

| Concern           | Required |
| ----------------- | -------- |
| prompt version    | YES      |
| model version     | YES      |
| embedding model   | YES      |
| retrieval context | YES      |

---

# REQUIRED

Store:

* prompts
* retrieved context
* outputs
* latency

---

# 21. INCIDENT RESPONSE POLICY

# Severity Levels

| Severity | Description          |
| -------- | -------------------- |
| P0       | data corruption      |
| P1       | retrieval broken     |
| P2       | degraded performance |
| P3       | minor bugs           |

---

# REQUIRED

Every incident:

* root cause analysis
* remediation
* regression tests
* documentation

---

# 22. ROOT CAUSE ANALYSIS TEMPLATE

Every serious bug must document:

```text id="’wini138"
What happened?
Why did it happen?
Why was it not detected?
What invariant failed?
How do we prevent recurrence?
```

---

# 23. FINAL TESTING STANDARD

System chỉ được xem là:
production-grade nếu:

```text id="’wini139"
Correctness
+
Determinism
+
Observability
+
Recoverability
+
Regression Resistance
+
Retrieval Quality Stability
```

được đảm bảo đồng thời.

---

# 24. FINAL ENGINEERING INSIGHT

Trong AI-native systems:

Bug nguy hiểm nhất KHÔNG phải:

* crashes
* exceptions

mà là:

```text id="’wini140"
silent semantic corruption
```

Ví dụ:

* retrieval sai
* graph sai
* chunking sai
* ranking drift
* memory pollution

nhưng hệ thống vẫn “trông như hoạt động bình thường”.

Nên testing + observability cho:

* retrieval
* semantics
* ranking
* graph integrity

phải được xem là:
first-class engineering discipline.
