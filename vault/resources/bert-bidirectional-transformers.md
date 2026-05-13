---
title: "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding"
type: paper
author: "Devlin et al., Google AI"
published_at: 2018-10-11
tags: [bert, transformer, pre-training, nlp, fine-tuning]
url: https://arxiv.org/abs/1810.04805
---

# BERT: Pre-training of Deep Bidirectional Transformers

BERT (Bidirectional Encoder Representations from Transformers) was introduced by Google AI in 2018 and became one of the most influential NLP models ever. It demonstrated that a single pre-trained model could be fine-tuned for a wide range of downstream tasks with minimal task-specific architecture changes.

## Key Insight: Bidirectionality

Previous language models like GPT were unidirectional — they predicted tokens left-to-right only. BERT's insight: use a **masked language model (MLM)** objective that randomly masks 15% of tokens and trains the model to predict them from both left and right context.

This bidirectionality is crucial for language understanding tasks where context from both sides matters (e.g., reading comprehension, named entity recognition).

## Pre-training Objectives

### 1. Masked Language Modeling (MLM)
- Randomly mask 15% of input tokens
- 80% replaced with `[MASK]`, 10% random token, 10% unchanged
- Model predicts original tokens from surrounding context

### 2. Next Sentence Prediction (NSP)
- Model receives two sentences A and B
- 50% of the time B is the actual next sentence (IsNext)
- 50% of the time B is a random sentence (NotNext)
- Helps learn cross-sentence relationships

## Architecture

BERT uses only the **Transformer encoder** (not the decoder) from [[Attention Is All You Need]]:
- **BERT-base**: 12 layers, 768 hidden, 12 heads, 110M parameters
- **BERT-large**: 24 layers, 1024 hidden, 16 heads, 340M parameters

Special tokens: `[CLS]` (classification), `[SEP]` (sentence separator), `[MASK]`.

## Fine-tuning

BERT fine-tuning is remarkably simple — add a task-specific head on top of the `[CLS]` token and fine-tune all parameters:
- **Classification**: linear layer on `[CLS]`
- **Token classification** (NER): linear layer on each token output
- **Question answering**: predict start/end span positions

## Embeddings

BERT produces rich contextual **embeddings** where the representation of each token depends on its full context. These embeddings are widely used for:
- Semantic search via cosine similarity
- Information retrieval with vector databases
- Input to knowledge graph construction pipelines

BERT representations are foundational to sentence encoders like `sentence-transformers`, which power tools like [[Vector Embeddings and Semantic Search]].

## Legacy

BERT spawned a lineage of improved models:
- **RoBERTa** — removes NSP, trains longer with more data
- **ALBERT** — parameter sharing for efficiency
- **DeBERTa** — disentangled attention
- **mBERT / XLM-R** — multilingual variants

See also: [[Attention Is All You Need]], [[Transformer Architecture]], [[Large Language Models and GPT]]
