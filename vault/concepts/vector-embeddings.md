---
title: "Vector Embeddings and Semantic Search"
type: concept
tags: [embeddings, vector-database, semantic-search, pgvector, cosine-similarity]
---

# Vector Embeddings and Semantic Search

**Vector embeddings** are dense numerical representations of text (or images, audio, etc.) where semantic similarity corresponds to geometric proximity in high-dimensional space. They are the foundation of modern semantic search, recommendation systems, and **Retrieval-Augmented Generation (RAG)**.

## What Are Embeddings?

An embedding model maps text to a fixed-length vector of floats:
```
"Attention is all you need" → [0.023, -0.142, 0.881, ..., 0.034]  (768 dimensions)
```

The key property: semantically similar texts produce similar vectors. Synonyms, paraphrases, and related concepts cluster together in the embedding space.

## Embedding Models

| Model | Dimensions | Notes |
|---|---|---|
| `bge-m3` | 1024 | Best open-source multilingual model (FlagEmbedding) |
| `text-embedding-004` (Google) | 768 | Production-grade, Gemini ecosystem |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | Fast, good baseline |
| `text-embedding-ada-002` (OpenAI) | 1536 | Strong, but proprietary |

BERT-derived models are most commonly used as embedding models because their contextual representations capture nuance unavailable to bag-of-words approaches.

## Similarity Metrics

**Cosine similarity** is the standard metric for embedding comparison:
```
similarity(A, B) = cos(θ) = (A · B) / (|A| |B|)
```

Cosine similarity ranges from -1 (opposite meaning) to 1 (identical). Typical thresholds:
- > 0.9: near-duplicate
- 0.7–0.9: highly related
- 0.5–0.7: related
- < 0.5: unrelated

## Vector Databases

To search millions of embeddings efficiently, **approximate nearest neighbor (ANN)** indexes are used:

- **pgvector** (PostgreSQL extension) — HNSW and IVFFlat indexes; integrates with SQL; used in minoverse
- **FAISS** (Facebook AI) — CPU/GPU, highly optimized for research
- **Chroma** — lightweight, embedded, good for prototyping
- **Weaviate / Pinecone / Qdrant** — managed cloud vector databases

## How Semantic Search Works

```
User query: "how does self-attention work?"
     ↓
Embed query with same model used to index documents
     ↓
Compute cosine similarity against all stored embeddings
     ↓
Return top-k most similar documents
     ↓
Documents about: "multi-head attention", "scaled dot-product attention",
                 "Transformer architecture", "BERT"
```

This fundamentally differs from keyword search (BM25) — it retrieves documents based on *meaning*, not exact word overlap.

## Hybrid Search

Production systems combine both:
1. **BM25** (keyword) — precise, handles exact terms and rare words
2. **Vector similarity** (semantic) — handles paraphrases and conceptual queries
3. **Re-ranking** with a cross-encoder for final ordering

This hybrid approach is planned for minoverse Phase 2.

## Role in Knowledge Graphs

Embeddings enable **entity linking** in knowledge graphs:
- Two mentions of "Transformer" and "transformer architecture" can be linked to the same node by embedding proximity
- Relatedness scores between concepts can be derived from cosine similarity

See also: [[Retrieval-Augmented Generation]], [[Knowledge Graphs as Semantic Infrastructure]], [[BERT and Bidirectional Encoders]]
