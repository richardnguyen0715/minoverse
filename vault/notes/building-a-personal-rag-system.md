---
title: "Building a Personal RAG System with minoverse"
type: note
tags: [rag, personal-knowledge-management, vector-search, llm, second-brain]
---

# Building a Personal RAG System with minoverse

This note documents my exploration of turning minoverse into a fully functional personal **Retrieval-Augmented Generation (RAG)** system — where I can ask questions in natural language and get grounded answers sourced from my own notes.

## The Problem I'm Solving

I have hundreds of research notes, paper summaries, and concepts scattered across markdown files. Finding relevant information requires manual scanning. I want to ask:
> "What did I learn about attention mechanisms?"
> "Which papers discuss knowledge graph construction?"
> "How does semantic search differ from keyword search?"

...and get answers that cite my actual notes, not hallucinated information.

## Architecture I'm Implementing

```
[Vault: .md files]
       ↓ file watcher
[Indexing Pipeline]
       ↓
[Parser] → title, content, frontmatter
       ↓
[Embeddings] ← bge-m3 / text-embedding-004 (Gemini)
       ↓
[PostgreSQL + pgvector] ← chunk_embeddings table
       ↓
[Query time: user question]
       ↓
[Embed question] → cosine similarity search → top-k chunks
       ↓
[Context window: retrieved chunks + question]
       ↓
[LLM: Gemini 2.0 Flash] → grounded answer
```

This is exactly the RAG pattern described in [[Retrieval-Augmented Generation]].

## Chunking Strategy

Long documents need to be split into chunks before embedding:
- **Fixed-size chunking**: 512 tokens with 50-token overlap — simple but may break sentences
- **Semantic chunking**: split at paragraph/heading boundaries — more coherent
- **Proposition chunking**: convert each claim to a standalone statement — highest quality, expensive

For minoverse I'm starting with semantic chunking (split at markdown headings).

## Embedding Model Choices

After reading [[Vector Embeddings and Semantic Search]], I've decided on:
- **bge-m3** (via Ollama) for local/offline mode — excellent multilingual support
- **text-embedding-004** (Gemini API) for cloud mode — fast, free tier

Both produce 768-1024 dimensional vectors suitable for pgvector HNSW indexing.

## Hybrid Search Plan

Pure vector search misses exact keyword matches (e.g., specific model names, paper titles). I plan to implement:
1. BM25 full-text search (PostgreSQL `tsvector`) for keyword precision
2. Vector similarity search (pgvector) for semantic recall
3. Reciprocal Rank Fusion (RRF) to merge both ranked lists
4. Cross-encoder re-ranking for final top-k (optional, slower)

This is Phase 2 of minoverse's roadmap.

## Graph-Enhanced Retrieval

Beyond flat vector search, the [[Knowledge Graphs as Semantic Infrastructure]] in minoverse should enable:
- **Entity-anchored retrieval**: search by concept node → fetch all documents mentioning that concept
- **Relation traversal**: find notes related to "Transformer" by following edges to "BERT", "GPT", "attention"
- **Graph RAG**: include relevant graph sub-context in the LLM prompt

## Current Status

- ✅ Vault indexing pipeline working
- ✅ AI enrichment (summaries, tags, entities) via Gemini
- ✅ Knowledge graph construction (entity promotion + relation generation)
- ✅ Web UI with graph visualization
- 🔲 Hybrid BM25 + vector retrieval (Phase 2)
- 🔲 Natural language Q&A interface

See also: [[Retrieval-Augmented Generation]], [[Vector Embeddings and Semantic Search]], [[Knowledge Graphs as Semantic Infrastructure]], [[Large Language Models and GPT]]
