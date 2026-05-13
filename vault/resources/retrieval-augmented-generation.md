---
title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
type: paper
author: "Lewis et al., Facebook AI"
published_at: 2020-05-22
tags: [rag, retrieval, llm, knowledge-base, vector-search]
url: https://arxiv.org/abs/2005.11401
---

# Retrieval-Augmented Generation (RAG)

RAG, introduced by Lewis et al. at Facebook AI Research in 2020, combines the parametric knowledge stored in **large language models** with non-parametric retrieval from an external knowledge base. This allows LLMs to ground their generations in retrieved evidence — drastically reducing hallucinations.

## Problem: LLMs Have Stale, Bounded Knowledge

Large language models like GPT store world knowledge in their parameters during pre-training. This creates two problems:
1. **Staleness** — knowledge is frozen at training cutoff; models don't know recent events
2. **Hallucination** — models sometimes generate plausible-sounding but factually wrong information with high confidence

RAG solves both by making the LLM consult a **live retrieval corpus** at inference time.

## Architecture

RAG combines two components:

### Retriever
- **DPR (Dense Passage Retrieval)**: encodes question and documents with separate **BERT**-based encoders into dense vector representations
- At inference: the query is encoded → top-k most similar document passages retrieved via **approximate nearest-neighbor search** (e.g., FAISS)
- These retrieved passages form the context for generation

### Generator
- A **seq2seq** model (originally BART) that takes the concatenation of query + retrieved passages as input
- Generates the final answer conditioned on this augmented context

```
Query → Retriever (BERT encoder + FAISS) → top-k passages
                                        ↓
                           Generator (BART/LLM)
                                        ↓
                              Grounded answer
```

## RAG Variants

- **RAG-Sequence**: retrieve once; generate full sequence conditioned on each retrieved document, then marginalize
- **RAG-Token**: can retrieve different documents for different parts of the generated sequence

## Why RAG Matters for Personal Knowledge Management

RAG is the foundation for AI-powered second brains. A system like minoverse:
1. Indexes your vault as a **vector database** (using BERT/bge-m3 **embeddings**)
2. At query time, retrieves the most relevant notes via **semantic search**
3. Feeds them to a **large language model** (Gemini, GPT, etc.) as context
4. The LLM generates a grounded answer based on *your* actual notes

This pattern eliminates hallucination while personalizing responses to the user's actual knowledge graph.

## Modern RAG Systems

Since the original paper, RAG has evolved significantly:
- **HyDE** — generate a hypothetical document to improve retrieval
- **Self-RAG** — LLM decides when to retrieve and critiques its own outputs
- **Graph RAG** — retrieve from a **knowledge graph** instead of flat documents
- **Corrective RAG** — grades retrieved documents and self-corrects

See also: [[Vector Embeddings and Semantic Search]], [[Knowledge Graphs as Semantic Infrastructure]], [[Building a Personal RAG System]]
