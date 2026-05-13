---
title: "Attention Is All You Need"
type: paper
author: "Vaswani et al."
published_at: 2017-06-12
tags: [transformer, attention, deep-learning, nlp]
url: https://arxiv.org/abs/1706.03762
---

# Attention Is All You Need

The **Transformer** architecture, introduced in this landmark 2017 paper by Vaswani et al., fundamentally changed how sequence-to-sequence tasks are solved in NLP. Before the Transformer, recurrent architectures (RNNs, LSTMs) were the dominant paradigm, but they suffered from sequential computation bottlenecks that prevented parallelism during training.

## Core Contribution: Self-Attention

The central innovation is the **self-attention mechanism** (also called scaled dot-product attention). Given queries Q, keys K, and values V:

```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V
```

This allows each token in a sequence to directly attend to every other token in O(1) distance — compared to O(n) for RNNs. The result: long-range dependencies are captured without gradient vanishing.

## Multi-Head Attention

Rather than computing one attention function, the model linearly projects queries, keys, and values into h separate subspaces and runs attention in parallel. The outputs are concatenated and projected again:

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
where head_i = Attention(Q W_i^Q, K W_i^K, V W_i^V)
```

Multi-head attention lets the model jointly attend from different representation subspaces at different positions — capturing syntactic and semantic relationships simultaneously.

## Positional Encoding

Since attention is permutation-invariant, the model injects **positional encoding** using sine and cosine functions at different frequencies. This gives the model information about the order of tokens.

## Architecture

The Transformer uses an encoder-decoder structure:
- **Encoder**: Stack of N=6 identical layers, each with multi-head self-attention + feed-forward network, with residual connections and layer normalization
- **Decoder**: Same stack but with an additional cross-attention sublayer attending to encoder output; uses masked self-attention to prevent attending to future tokens

## Impact

The Transformer became the backbone of:
- **BERT** — bidirectional encoder for language understanding
- **GPT series** — autoregressive decoder for generation
- **T5, PaLM, LLaMA, Gemini** — all large language models
- Vision Transformers (ViT) — applied to images

See also: [[Transformer Architecture]], [[BERT and Bidirectional Encoders]], [[Large Language Models and GPT]]
