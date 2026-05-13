---
title: "LLM Evaluation — Benchmarks and Techniques"
type: note
tags: [llm, evaluation, benchmarks, mmlu, reasoning, alignment]
---

# LLM Evaluation: Benchmarks and Techniques

Evaluating **large language models** is one of the most contentious and evolving topics in AI research. The challenge: LLMs are general-purpose systems capable of a vast range of tasks, so no single benchmark captures their full capability — or failure modes.

## Standard Benchmarks

### MMLU (Massive Multitask Language Understanding)
- 57 subjects: mathematics, law, medicine, history, coding, ethics
- 4-choice multiple-choice format
- Tests breadth of world knowledge
- GPT-4: ~86%, Gemini Ultra: ~90%, Human expert: ~89%

### HumanEval
- 164 Python programming problems
- Measures functional correctness by running tests
- GPT-4: ~67%, Claude 3 Opus: ~73%

### GSM8K
- 8,500 grade-school math word problems
- Tests multi-step numerical reasoning
- Chain-of-thought prompting dramatically improves scores

### BIG-Bench Hard
- 23 tasks designed to be beyond GPT-4's capability at time of creation
- Many are now solved, raising questions about benchmark saturation

### HELM (Holistic Evaluation of Language Models)
- Multi-metric evaluation: accuracy + calibration + robustness + fairness + efficiency
- More realistic than single-number leaderboards

## Chain-of-Thought (CoT) Prompting

Wei et al. (2022) showed that prompting LLMs to reason step-by-step dramatically improves performance on reasoning tasks:

```
Prompt: "Q: Roger has 5 tennis balls. He buys 2 more cans of 3 balls each. 
         How many tennis balls does he have now? 
         Let's think step by step."

Response: "Roger starts with 5 balls. He buys 2×3=6 more. 5+6=11 balls."
```

CoT works because it forces the model to decompose problems into manageable steps — similar to how humans approach difficult reasoning tasks.

## Hallucination Evaluation

LLMs hallucinate — generate plausible but factually incorrect statements. Measuring this:
- **TruthfulQA**: 817 questions humans often answer incorrectly; tests whether LLMs can avoid mimicking human misconceptions
- **FactScore**: breaks generated text into atomic claims and verifies each against Wikipedia
- **RAGAS**: evaluates RAG pipelines for faithfulness, answer relevance, context recall

## Alignment Evaluation

Beyond capability, alignment benchmarks test whether models are safe and helpful:
- **HHH** (Helpful, Harmless, Honest) — Anthropic's framework
- **MT-Bench** — multi-turn conversation quality judged by GPT-4
- **LMSYS Chatbot Arena** — human pairwise preference judgments at scale

## Critique: The Benchmark Gaming Problem

As benchmarks become targets, models may overfit to them. Issues:
1. **Contamination**: training data may include benchmark questions
2. **Teaching to the test**: RL fine-tuning for specific benchmarks inflates scores
3. **Distribution shift**: high benchmark scores don't guarantee real-world utility

The field is moving toward more diverse, dynamic, and hard-to-game evaluation — including human red-teaming and capability elicitation.

## Evaluation in the Minoverse Context

For the AI enrichment pipeline using **Gemini** (and previously **Ollama/qwen3**), informal quality checks:
- Summary coherence: does the summary capture key ideas?
- Entity recall: are important concepts extracted?
- Tag precision: are tags topically correct?
- Relation accuracy: do generated relations make semantic sense?

Formal benchmarking of the enrichment pipeline is future work.

See also: [[Large Language Models and GPT]], [[Retrieval-Augmented Generation]], [[Transformer Architecture]]
