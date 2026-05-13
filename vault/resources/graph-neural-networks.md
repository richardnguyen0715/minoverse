---
title: "Graph Neural Networks for Knowledge Reasoning"
type: article
author: "Research Notes"
published_at: 2024-03-10
tags: [gnn, knowledge-graph, link-prediction, graph-learning, embedding]
---

# Graph Neural Networks for Knowledge Reasoning

**Graph Neural Networks (GNNs)** extend deep learning to graph-structured data. When applied to **knowledge graphs**, GNNs can infer missing links, classify entities, and generate rich relational embeddings — capabilities impossible with flat vector representations alone.

## Why Graphs Need Special Neural Networks

Standard neural networks assume i.i.d. (independent and identically distributed) inputs. Graphs violate this assumption — nodes are connected, and information propagates through edges. GNNs address this via **message passing**: each node aggregates information from its neighbors.

## Message Passing Framework

The general GNN update rule for node v at layer k:

```
h_v^(k) = UPDATE(h_v^(k-1), AGGREGATE({h_u^(k-1) : u ∈ N(v)}))
```

Where:
- `h_v^(k)`: embedding of node v at layer k
- `N(v)`: neighbors of v
- `AGGREGATE`: pooling function (mean, sum, max, attention)
- `UPDATE`: transformation (typically an MLP)

After K layers, each node's embedding captures a K-hop neighborhood.

## Key GNN Architectures

### Graph Convolutional Network (GCN)
Spectral approach: convolve over the graph Laplacian. Simple, effective, but limited to undirected graphs.

### GraphSAGE
Inductive learning: sample fixed-size neighborhoods and aggregate. Works for graphs where new nodes arrive at inference time.

### Graph Attention Network (GAT)
Introduces **attention weights** over neighbors — different neighbors contribute differently to the aggregation. Analogous to the multi-head attention in the **Transformer architecture** ([[Transformer Architecture]]).

### Relational Graph Convolutional Network (R-GCN)
Handles **typed relations** in knowledge graphs:
```
h_v^(k) = σ(W_0 h_v^(k-1) + Σ_r Σ_u∈N_r(v) (1/|N_r(v)|) W_r h_u^(k-1))
```
Each relation type r has its own weight matrix W_r — crucial for knowledge graph reasoning where edge types matter (e.g., "is_a" vs. "causes" vs. "part_of").

## Knowledge Graph Completion

The canonical task: predict missing `(subject, predicate, ?)` triples.

### TransE
Embeds entities and relations as vectors. Models relation r as a translation from subject to object:
```
h + r ≈ t  (when (h, r, t) holds)
```
Simple, interpretable, widely used baseline.

### RotatE
Models relations as rotations in complex vector space. Handles symmetric, antisymmetric, inverse, and composition patterns.

### KGBERT
Uses **BERT** ([[BERT and Bidirectional Encoders]]) to score triples by encoding "(subject) [SEP] (predicate) [SEP] (object)" as text. Leverages pre-trained language knowledge.

## Applications in Personal Knowledge Management

GNNs applied to a personal knowledge graph (like minoverse) enable:
1. **Relation inference**: suggest that "RAG" relates to "knowledge graphs" even without explicit user annotation
2. **Concept clustering**: group related concepts (Transformer, BERT, GPT, attention) into "Neural Language Models" cluster
3. **Note recommendation**: find notes that are graph-adjacent to what you're currently reading
4. **Gap detection**: identify areas where your knowledge graph has sparse connections → areas to research

## Integration with Vector Embeddings

GNN node embeddings and **vector embeddings** ([[Vector Embeddings and Semantic Search]]) are complementary:
- Word/sentence embeddings: distributional semantics from text
- GNN node embeddings: structural position in the knowledge graph

Combining both (e.g., initializing GNN with BERT embeddings) produces the richest representations for downstream tasks.

See also: [[Knowledge Graphs as Semantic Infrastructure]], [[Vector Embeddings and Semantic Search]], [[Transformer Architecture]]
