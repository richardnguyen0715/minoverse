# AI/LLM Infrastructure Standards & Architecture

Bạn KHÔNG nên nghĩ:
“gọi OpenAI API”.

Bạn đang build:

```text id="k8z0u9"
AI Runtime Infrastructure
```

cho:

* multi-provider
* multi-model
* multi-phase
* multi-agent
* retrieval-native
* production-grade
* fault-tolerant
* configurable AI system

Mục tiêu:

* dễ swap model
* dễ routing
* dễ scaling
* dễ debug
* dễ benchmark
* dễ orchestration
* không vendor lock-in
* deterministic behavior tối đa có thể

---

# 1. CORE AI ARCHITECTURE PRINCIPLES

# Principle 1 — Provider-Agnostic

Core system KHÔNG được phụ thuộc:

* OpenAI SDK
* Gemini SDK
* Claude SDK

---

# REQUIRED

Application chỉ biết:

```text id="jlwm163"
LLMRuntime
EmbeddingRuntime
RerankerRuntime
```

---

# Principle 2 — Config-Driven AI

KHÔNG hardcode:

* model names
* API providers
* prompts
* temperatures
* token limits

MỌI THỨ phải:

* declarative
* config-driven

---

# Principle 3 — Separation of Concerns

Tách biệt:

* providers
* models
* prompts
* skills
* orchestration
* pipelines
* memory
* retrieval

---

# Principle 4 — AI Is Infrastructure

AI calls phải được xem như:

* distributed systems
* unreliable systems
* async systems
* retryable systems

---

# Principle 5 — Every AI Call Must Be Observable

Mọi generation:

* traceable
* reproducible
* debuggable

---

# 2. HIGH-LEVEL AI ARCHITECTURE

```text id="jlwm164"
Application Layer
    ↓
AI Orchestrator
    ↓
Skill Runtime
    ↓
Prompt Engine
    ↓
Model Router
    ↓
Provider Runtime
    ↓
LLM APIs / Local Models
```

---

# 3. RECOMMENDED DIRECTORY STRUCTURE

KHÔNG structure theo vendor.

---

# GOOD

```text id="’wini165"
ai/
├── providers/
├── runtimes/
├── models/
├── prompts/
├── skills/
├── agents/
├── orchestration/
├── pipelines/
├── memory/
├── retrieval/
├── evaluation/
├── telemetry/
├── configs/
└── tests/
```

---

# 4. PROVIDER ABSTRACTION

# REQUIRED INTERFACE

```python id="’wini166"
class LLMProvider(Protocol):
    async def generate(...)
    async def stream(...)
    async def embeddings(...)
```

---

# Providers

```text id="’wini167"
openai/
gemini/
anthropic/
ollama/
vllm/
openrouter/
```

---

# RULE

Application KHÔNG biết:

* OpenAI
* Gemini
* Claude

Application chỉ biết:

```text id="’wini168"
provider.generate()
```

---

# 5. MODEL REGISTRY SYSTEM

# MOST IMPORTANT ARCHITECTURE

Bạn cần:

* logical models
* physical models

---

# Logical Model

```yaml id="’wini169"
reasoning_model:
  provider: anthropic
  model: claude-sonnet-4
```

---

# Application chỉ gọi

```python id="’wini170"
runtime.generate(model="reasoning_model")
```

---

# NEVER

```python id="’wini171"
model="gpt-4o"
```

trong business logic.

---

# 6. CONFIGURATION SYSTEM

# REQUIRED

Hierarchical config system.

---

# Structure

```text id="’wini172"
configs/
├── environments/
├── models/
├── providers/
├── prompts/
├── skills/
├── pipelines/
├── retrieval/
└── routing/
```

---

# 7. PROVIDER CONFIGS

# Example

```yaml id="’wini173"
provider:
  name: openai

authentication:
  api_keys:
    - ${OPENAI_KEY_1}
    - ${OPENAI_KEY_2}
    - ${OPENAI_KEY_3}

timeouts:
  connect: 10
  read: 120

retry:
  max_attempts: 5
  exponential_backoff: true

rate_limits:
  requests_per_minute: 500

fallback:
  providers:
    - anthropic
    - gemini
```

---

# 8. MODEL CONFIGS

# Example

```yaml id="’wini174"
model:
  name: reasoning_model

provider: anthropic

api_model: claude-sonnet-4

capabilities:
  reasoning: true
  vision: false
  function_calling: true
  streaming: true

limits:
  context_window: 200000
  max_output_tokens: 8192

generation:
  temperature: 0.2
  top_p: 0.95

fallback_models:
  - gpt_4_1
  - gemini_pro
```

---

# 9. MODEL ROUTING SYSTEM

CRITICAL ARCHITECTURE.

---

# Required

Logical routing.

---

# Example

```yaml id="’wini175"
routing:
  summarization:
    primary: fast_summary_model
    fallback:
      - cheap_summary_model

  reasoning:
    primary: reasoning_model
    fallback:
      - secondary_reasoning_model

  embeddings:
    primary: bge_m3
```

---

# Application

```python id="’wini176"
runtime.generate(task="summarization")
```

NOT:

```python id="’wini177"
model="gpt-4"
```

---

# 10. PROMPT SYSTEM STANDARDS

# MOST IMPORTANT SECTION

---

# NEVER

Inline prompts.

---

# BAD

```python id="’wini178"
prompt = "Summarize this text"
```

---

# REQUIRED

Versioned prompt files.

---

# Structure

```text id="’wini179"
prompts/
├── system/
├── tasks/
├── agents/
├── retrieval/
├── memory/
└── evaluation/
```

---

# 11. PROMPT FILE FORMAT

# Recommended

YAML + markdown hybrid.

---

# Example

```yaml id="’wini180"
name: summarize_paper
version: v1

system: |
  You are a research summarization assistant.

user_template: |
  Summarize the following paper:

  {{content}}

constraints:
  max_tokens: 1000
  temperature: 0.2
```

---

# 12. SYSTEM PROMPT RULES

# MUST DEFINE

| Concern          | Required |
| ---------------- | -------- |
| role             | YES      |
| constraints      | YES      |
| output format    | YES      |
| safety           | YES      |
| style            | YES      |
| refusal behavior | YES      |

---

# System prompts MUST BE

* deterministic
* composable
* reusable

---

# 13. SKILL ARCHITECTURE

VERY IMPORTANT.

---

# Skills ≠ prompts

Skills:

* orchestrate prompts
* retrieval
* tools
* memory
* post-processing

---

# Example

```text id="’wini181"
skills/
├── summarize_resource/
├── extract_entities/
├── build_graph_relations/
├── semantic_search/
└── synthesize_research/
```

---

# Skill Structure

```text id="’wini182"
skill/
├── config.yaml
├── prompt.md
├── executor.py
├── schemas.py
└── tests/
```

---

# 14. SKILL CONFIG

```yaml id="’wini183"
name: summarize_resource

model: reasoning_model

retrieval:
  enabled: true
  top_k: 8

generation:
  temperature: 0.2

streaming: true

fallback:
  enabled: true
```

---

# 15. AI PIPELINE DESIGN

# REQUIRED

Every AI workflow:

* declarative
* resumable
* retryable

---

# Example

```yaml id="’wini184"
pipeline:
  steps:
    - chunk
    - embeddings
    - summarize
    - extract_entities
    - generate_tags
```

---

# 16. STREAMING STANDARDS

# REQUIRED

Streaming abstraction layer.

---

# NEVER

Expose raw provider stream APIs directly.

---

# REQUIRED INTERFACE

```python id="’wini185"
async for chunk in runtime.stream(...):
```

---

# Stream Event Types

```text id="’wini186"
token
tool_call
metadata
error
complete
```

---

# 17. ASYNC STANDARDS

# REQUIRED

ALL AI operations:

* async
* cancellable
* timeout-aware

---

# REQUIRED

```python id="’wini187"
asyncio.TaskGroup
```

for orchestration.

---

# NEVER

Blocking synchronous AI calls.

---

# 18. RETRY POLICIES

# REQUIRED

Exponential backoff.

---

# REQUIRED

Retryable errors:

* timeouts
* rate limits
* transient failures

---

# NEVER RETRY

* invalid prompts
* schema failures
* authentication errors

---

# 19. FALLBACK ARCHITECTURE

CRITICAL.

---

# Level 1 — API Key Rotation

```yaml id="’wini188"
api_keys:
  strategy: round_robin
```

---

# Level 2 — Model Fallback

```yaml id="’wini189"
fallback_models:
  - gpt_4_1
  - claude_sonnet
```

---

# Level 3 — Provider Fallback

```yaml id="’wini190"
fallback_providers:
  - anthropic
  - openrouter
```

---

# Level 4 — Local Model Fallback

```yaml id="’wini191"
local_fallback:
  provider: ollama
  model: qwen3
```

---

# 20. MULTI-MODEL ORCHESTRATION

# REQUIRED

Composable model workflows.

---

# Example

```yaml id="’wini192"
research_synthesis:
  retrieval_model: bge_m3
  reranker: bge_reranker
  reasoning_model: claude_sonnet
  summarizer: gpt_4_1_mini
```

---

# 21. OBSERVABILITY STANDARDS

EVERY AI CALL MUST TRACK:

| Concern           | Required |
| ----------------- | -------- |
| prompt version    | YES      |
| model             | YES      |
| provider          | YES      |
| latency           | YES      |
| token usage       | YES      |
| retries           | YES      |
| retrieval context | YES      |

---

# REQUIRED

Correlation IDs.

---

# 22. AI TELEMETRY STORAGE

# Store

```text id="’wini193"
prompts
responses
retrieval context
token usage
latency
cost
failures
fallback chains
```

---

# 23. OUTPUT VALIDATION

# REQUIRED

Structured outputs only where possible.

---

# Use

```text id="’wini194"
Pydantic
JSON schemas
```

---

# NEVER TRUST RAW MODEL OUTPUT

Always validate.

---

# 24. CONTEXT MANAGEMENT

CRITICAL FOR LARGE SYSTEMS.

---

# Context Layers

```text id="’wini195"
system prompt
+ memory
+ retrieval context
+ user input
+ tool results
```

---

# REQUIRED

Context builders.

---

# NEVER

Manual string concatenation.

---

# 25. MEMORY ARCHITECTURE

# Separate:

| Type           | Purpose             |
| -------------- | ------------------- |
| conversational | chat continuity     |
| episodic       | workflows           |
| semantic       | distilled knowledge |
| retrieval      | relevant chunks     |

---

# 26. TOOL CALLING STANDARDS

# REQUIRED

Unified tool abstraction.

---

# Tool Interface

```python id="’wini196"
class Tool(Protocol):
    async def execute(...)
```

---

# REQUIRED

Tool:

* schemas
* validation
* telemetry
* retries

---

# 27. LOCAL MODEL STANDARDS

# Recommended Runtime

```text id="’wini197"
Ollama
vLLM
llama.cpp
```

---

# Local Model Registry

```yaml id="’wini198"
local_models:
  reasoning:
    provider: ollama
    model: qwen3:32b
```

---

# 28. EVALUATION SYSTEM

VERY IMPORTANT.

---

# REQUIRED

Evaluation pipelines for:

* retrieval quality
* hallucinations
* summarization quality
* ranking quality

---

# REQUIRED

Golden datasets.

---

# 29. COST CONTROL

# REQUIRED

Track:

* cost/request
* token/request
* latency/request

---

# REQUIRED

Budget limits.

---

# Example

```yaml id="’wini199"
budgets:
  daily_limit_usd: 20
```

---

# 30. SECURITY POLICIES

# NEVER

* hardcode API keys
* log secrets
* expose prompts publicly

---

# REQUIRED

Secret manager abstraction.

---

# 31. TESTING AI SYSTEMS

# REQUIRED

Test:

* prompt regressions
* retrieval regressions
* model fallback
* timeout handling
* malformed outputs

---

# REQUIRED

Mock providers at unit layer.

Real providers at integration layer.

---

# 32. RECOMMENDED INITIAL STACK

# Local-first

| Purpose         | Tech           |
| --------------- | -------------- |
| orchestration   | custom runtime |
| local inference | Ollama         |
| embeddings      | bge-m3         |
| reranking       | bge-reranker   |
| reasoning       | Claude/GPT     |
| fallback        | OpenRouter     |
| async           | asyncio        |
| validation      | Pydantic       |

---

# 33. FINAL AI INFRASTRUCTURE ARCHITECTURE

```text id="’wini200"
Application
    ↓
Skills
    ↓
Prompt Engine
    ↓
AI Runtime
    ↓
Routing Layer
    ↓
Provider Abstraction
    ↓
LLM APIs / Local Models
```

---

# 34. MOST IMPORTANT INSIGHT

Sai lầm lớn nhất:

```text id="’wini201"
business logic coupled directly to model providers
```

Bạn phải architect sao cho:

```text id="’wini202"
models become replaceable infrastructure
```

giống như:

* database drivers
* HTTP clients
* storage backends

thì hệ thống mới:

* scalable
* maintainable
* future-proof
* AI-evolution-proof.
