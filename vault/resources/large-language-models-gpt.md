---
title: "Large Language Models and the GPT Lineage"
type: article
author: "Research Notes"
published_at: 2024-01-15
tags: [llm, gpt, scaling, few-shot-learning, fine-tuning, gemini]
---

# Large Language Models and the GPT Lineage

Large Language Models (LLMs) are neural language models trained on massive text corpora at unprecedented scale. The GPT (Generative Pre-trained Transformer) series, developed by OpenAI, pioneered the modern LLM paradigm.

## The Scaling Laws Insight

OpenAI's 2020 paper "Scaling Laws for Neural Language Models" (Kaplan et al.) showed that model performance scales predictably with three factors:
- **Model size** (parameters)
- **Dataset size** (tokens)
- **Compute budget** (FLOPs)

This empirical finding justified the trend toward ever-larger models and suggested that performance improvements were reliably predictable through scaling alone.

## GPT Evolution

### GPT-1 (2018)
- 117M parameters, trained on BooksCorpus
- First demonstration of large-scale **Transformer decoder** pre-training
- Showed transferability: one pre-trained model fine-tuned for many tasks

### GPT-2 (2019)
- 1.5B parameters, trained on WebText (40GB)
- Introduced **zero-shot** task performance — no fine-tuning needed for some tasks
- Famous for its story generation capabilities
- OpenAI initially withheld it citing "misuse concerns"

### GPT-3 (2020)
- 175B parameters, trained on 570GB of filtered Common Crawl
- Breakthrough **few-shot learning**: given 3-5 examples in the prompt, the model generalizes without gradient updates
- Introduced "in-context learning" as a new paradigm
- Basis for the commercial API

### GPT-4 (2023)
- Multimodal (text + images)
- Significantly improved reasoning, coding, and factual accuracy
- Architecture undisclosed (GPT-4 Technical Report)

## Other Major LLM Families

### Google Gemini
- Multimodal from the ground up (text, images, audio, video, code)
- **Gemini 2.0 Flash** is the recommended model for production use — fast, capable, available via API
- Vertex AI integration allows enterprise-grade deployment with service accounts

### Meta LLaMA
- Open-weights models, enabling local deployment
- LLaMA 3 (70B, 8B variants) achieves competitive performance with GPT-3.5
- Basis for local inference via **Ollama**

### Anthropic Claude
- Constitutional AI training for safety alignment
- Long context windows (200K tokens in Claude 3)

## Fine-tuning vs. In-Context Learning

| Approach | Method | Cost | When to use |
|---|---|---|---|
| Fine-tuning | Gradient updates on task data | High (GPU) | Specific domain, consistent task |
| RLHF | Reward model + PPO | Very high | Instruction following, alignment |
| In-context (few-shot) | Examples in prompt | None | General tasks, quick prototyping |
| RAG | Retrieval augmentation | Low | Knowledge-intensive tasks |

## Hallucination and Mitigation

LLMs hallucinate because they optimize for fluency, not factual accuracy. Key mitigations:
- **RAG** ([[Retrieval-Augmented Generation]]) — ground outputs in retrieved documents
- **Knowledge graphs** — verify claims against a structured fact base
- **Chain-of-thought prompting** — force step-by-step reasoning
- **Self-consistency** — sample multiple outputs and select the majority answer

See also: [[Attention Is All You Need]], [[BERT and Bidirectional Encoders]], [[Retrieval-Augmented Generation]], [[Vector Embeddings and Semantic Search]]
