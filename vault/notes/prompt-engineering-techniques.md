---
title: "Prompt Engineering Techniques"
type: note
tags: [prompt-engineering, llm, chain-of-thought, few-shot, system-prompts]
---

# Prompt Engineering Techniques

**Prompt engineering** is the discipline of designing inputs to large language models to elicit desired outputs. As LLMs become more capable, prompt design has emerged as a high-leverage skill — and a source of competitive advantage.

## Why Prompts Matter

LLMs are sensitive to phrasing, formatting, and context. The same model with different prompts can:
- Produce a confident, coherent answer **or** hallucinate plausibly
- Generate working code **or** subtly buggy code
- Give a nuanced analysis **or** a superficial summary

Prompt engineering is essentially UX design for language models.

## Core Techniques

### Zero-Shot Prompting
The simplest form: ask the question directly.
```
Prompt: "Translate the following English text to French: 'The Transformer architecture uses self-attention.'"
```
Works well for tasks within the model's training distribution.

### Few-Shot Prompting
Provide examples (shots) before the actual query to demonstrate the desired format and reasoning:
```
Prompt:
Q: What type of architecture is BERT?
A: Transformer encoder (bidirectional)

Q: What type of architecture is GPT?
A: Transformer decoder (autoregressive)

Q: What type of architecture is T5?
A:
```
Few-shot learning is one of the breakthrough capabilities of **GPT-3** ([[Large Language Models and GPT]]).

### Chain-of-Thought (CoT)
Append "Let's think step by step" or show reasoning examples. Forces intermediate reasoning steps, which dramatically improves math and logic tasks.

### System Prompts
Modern LLMs (GPT-4, Gemini, Claude) support a **system** role that sets persistent instructions:
```
System: "You are a research assistant specializing in NLP. Always cite sources. 
         Respond with structured markdown. When uncertain, say so."
User: "Explain how BERT handles bidirectionality."
```

In minoverse's prompt YAML files (`src/ai/prompts/tasks/*.yaml`), the `system` field serves this purpose.

### Role Prompting
```
"You are an expert knowledge graph engineer with 10 years of experience 
in ontology design. Extract all named entities and their relationships 
from the following text..."
```
Persona assignment improves output quality for specialized tasks.

### Structured Output Prompting
For pipelines consuming LLM output programmatically, request specific formats:
```
"Return your response as valid JSON with this schema:
{
  'entities': [{'name': str, 'type': str}],
  'relations': [{'subject': str, 'predicate': str, 'object': str}]
}
Do not include any text outside the JSON."
```
This is exactly the pattern used in minoverse's entity extraction and relation generation prompts.

## Advanced Techniques

### ReAct (Reasoning + Acting)
Interleaves reasoning ("Thought:") with tool use ("Action:") and observation ("Observation:"). Foundation of modern AI agents.

### Self-Consistency
Generate multiple independent reasoning chains for the same problem; take the majority answer. Reduces variance on reasoning tasks.

### Tree of Thoughts
Explore multiple reasoning paths in a tree structure, with backtracking. Better than linear CoT for complex multi-step problems.

### RAG + Prompting
Combine **Retrieval-Augmented Generation** with structured prompts:
```
System: "Answer only using the provided context. If the answer isn't in the context, say 'I don't know'."
Context: {retrieved_chunks}
User: {question}
```
This is the architecture that eliminates hallucinations in production RAG systems ([[Retrieval-Augmented Generation]]).

## Prompt Versioning

As prompt quality matters, treat prompts as code:
- Version them (v1, v2, ...)
- Store in files (not hardcoded strings)
- A/B test different versions
- Track performance per version

Minoverse stores all prompts in `src/ai/prompts/tasks/*.yaml` with explicit version fields — following this principle exactly.

See also: [[Large Language Models and GPT]], [[Retrieval-Augmented Generation]], [[LLM Evaluation — Benchmarks and Techniques]]
