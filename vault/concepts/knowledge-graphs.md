---
title: "Knowledge Graphs as Semantic Infrastructure"
type: concept
tags: [knowledge-graph, entities, relations, ontology, graph-database, semantic-web]
---

# Knowledge Graphs as Semantic Infrastructure

A **knowledge graph** is a structured representation of entities and their relationships. Unlike relational databases (which store tabular data) or vector databases (which store dense representations), a knowledge graph explicitly encodes the *semantic meaning* of connections between concepts.

## Structure

A knowledge graph consists of:
- **Nodes (Entities)**: concepts, people, places, technologies (e.g., "Transformer", "BERT", "Attention Mechanism")
- **Edges (Relations)**: typed, directed connections between entities (e.g., "BERT *uses* Transformer", "Vaswani et al. *authored* Attention Paper")
- **Properties**: attributes on nodes and edges (e.g., publication_year, confidence_score)

The fundamental unit is the **triple**: `(subject, predicate, object)` — e.g., `(BERT, is_a, Transformer)`.

## Why Knowledge Graphs for PKM?

In a Personal Knowledge Management system, a knowledge graph:
1. **Surfaces hidden connections**: two notes discussing "attention mechanisms" and "self-supervised learning" get linked even without explicit wiki links
2. **Enables traversal**: "show me everything related to RAG" → graph traversal finds Transformer → BERT → vector embeddings → semantic search
3. **Structures knowledge**: turns unstructured markdown into a queryable semantic network
4. **Powers Graph RAG**: retrieve from the graph structure, not just flat vectors, for richer context

## Knowledge Graph Construction Pipeline

For minoverse, the pipeline:
1. **Entity extraction** via LLM (Gemini) — extract named concepts, tools, frameworks, methodologies from each note
2. **Entity promotion** — deduplicate and normalize entities (e.g., "Transformers" → "Transformer")
3. **Relation generation** via LLM — identify relationships between co-occurring entities across documents
4. **Graph storage** — `concept_entities` and `concept_relations` tables in PostgreSQL

## Graph Neural Networks (GNNs)

GNNs extend deep learning to graph-structured data. By propagating information across edges, GNNs can:
- Infer missing relations in incomplete knowledge graphs (link prediction)
- Generate embeddings for nodes that incorporate neighborhood structure
- Classify entities based on their relational context

GNNs are used in large-scale knowledge graphs like Google's Knowledge Graph and Wikidata.

## Relationship to Vector Embeddings

Knowledge graphs and vector embeddings are complementary:
- **Embeddings** capture distributional semantics (what words appear with what)
- **Knowledge graphs** capture structured, interpretable relations

**Graph RAG** combines both: retrieve sub-graphs (structured) + embed them (dense) for the most contextually rich retrieval.

## Major Knowledge Graphs

| Graph | Scale | Use case |
|---|---|---|
| Wikidata | 100M+ facts | General world knowledge |
| Google Knowledge Graph | Billions of facts | Search engine enrichment |
| ConceptNet | 21M assertions | Commonsense reasoning |
| DBpedia | 4.5M entities | Semantic web, SPARQL queries |

See also: [[Retrieval-Augmented Generation]], [[Vector Embeddings and Semantic Search]], [[Building a Personal RAG System]]
