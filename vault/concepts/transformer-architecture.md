---
title: "Transformer Architecture"
type: concept
tags: [transformer, self-attention, encoder, decoder, architecture]
---

# Transformer Architecture

The Transformer is a neural network architecture based entirely on **attention mechanisms**, dispensing with recurrence and convolutions. First proposed in [[Attention Is All You Need]] (Vaswani et al., 2017), it has become the dominant architecture in NLP, vision, and multi-modal AI.

## Why Transformers Replaced RNNs

| Property | RNN/LSTM | Transformer |
|---|---|---|
| Parallelism | Sequential (slow training) | Fully parallel (fast training) |
| Long-range dependencies | Gradient vanishing | Direct attention (O(1) path length) |
| Context window | Limited by memory | Can be extended (1M+ tokens) |
| Scalability | Hard to scale | Scales with data and compute |

## Core Components

### Self-Attention
Each token computes attention over all other tokens in the sequence:
```
Q, K, V = Linear projections of input embeddings
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V
```

The attention score between two tokens captures their semantic relationship regardless of distance.

### Multi-Head Attention
Multiple parallel attention heads allow the model to simultaneously attend to:
- Syntactic relationships (subject-verb agreement)
- Semantic relationships (co-reference, entailment)
- Positional relationships

### Feed-Forward Network
After attention, each position passes through a two-layer MLP independently:
```
FFN(x) = max(0, xW₁ + b₁)W₂ + b₂
```

### Residual Connections + Layer Normalization
Stabilizes training by allowing gradients to flow directly through skip connections.

### Positional Encoding
Since attention is permutation-invariant, position information is injected via sinusoidal encodings added to the input embeddings.

## Encoder vs. Decoder

**Encoder** (BERT, RoBERTa):
- Bidirectional attention — each token attends to all others
- Ideal for understanding tasks: classification, NER, semantic search

**Decoder** (GPT, LLaMA):
- Causal (masked) attention — tokens only attend to previous tokens
- Ideal for generation: text completion, chat, code generation

**Encoder-Decoder** (T5, BART):
- Encoder processes input; decoder attends to encoder output via cross-attention
- Ideal for seq2seq tasks: translation, summarization, **RAG**

## Scaling Properties

Transformers exhibit remarkable scaling behavior:
- Performance improves log-linearly with model size, data, and compute
- Emergent capabilities (reasoning, few-shot learning) appear at scale
- This is the empirical basis for **Large Language Models**

## Applications Beyond NLP

- **Vision Transformer (ViT)**: patches of images as tokens
- **Audio Spectrograms**: time-frequency features as tokens
- **AlphaFold**: protein structure prediction using attention
- **Decision Transformer**: reinforcement learning with offline data

See also: [[Attention Is All You Need]], [[BERT and Bidirectional Encoders]], [[Large Language Models and GPT]], [[Vector Embeddings and Semantic Search]]
