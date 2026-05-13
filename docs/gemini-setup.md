# Gemini API Setup Guide

This guide explains how to configure Google Gemini as the AI provider for minoverse.

---

## Overview

Minoverse supports two AI providers:

| Provider | When to use |
|---|---|
| **Gemini** (default) | Cloud inference via Google API — no GPU required |
| **Ollama** | Fully local inference — no internet required |

Gemini supports two authentication modes:

| Auth mode | How it works |
|---|---|
| **API key rotation** | Up to 5 keys, round-robin — auto-rotates on quota errors |
| **Service account** (optional) | Uses a Google service-account JSON; bypasses per-key quotas |

---

## 1. Get a Gemini API Key

1. Go to **[Google AI Studio](https://aistudio.google.com/apikey)**
2. Sign in with your Google account
3. Click **Create API key** → choose a project or create a new one
4. Copy the generated key (starts with `AIza...`)

Repeat for up to 5 keys (recommended: use separate Google accounts or projects to maximize free quota).

---

## 2. Configure API Keys

Open `apps/api/.env` and set `GEMINI_API_KEYS` to a comma-separated list:

```bash
# apps/api/.env

AI_PROVIDER=gemini

# Up to 5 keys — rotate automatically on 429/quota errors
GEMINI_API_KEYS=AIzaSy_key_one,AIzaSy_key_two,AIzaSy_key_three,AIzaSy_key_four,AIzaSy_key_five

# Model to use (default: gemini-2.0-flash — fast, free tier available)
GEMINI_CHAT_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

That's all. No Ollama, no Docker GPU needed.

---

## 3. (Optional) Use a Service Account

A service account is a Google Cloud identity that authenticates as your project instead of a user. Use this when:
- You need higher quotas (Vertex AI usage)
- You want centralized auth without managing multiple personal API keys
- You're deploying to production

### 3.1 Create a Service Account

1. Go to **[Google Cloud Console → IAM & Admin → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)**
2. Select or create a project
3. Click **Create Service Account**
4. Give it a name (e.g. `minoverse-ai`)
5. Grant the role: **Vertex AI User** (`roles/aiplatform.user`)
6. Click **Done**

### 3.2 Download the JSON Key

1. Click on your new service account
2. Go to **Keys** tab → **Add Key** → **Create new key** → **JSON**
3. Save the file (e.g. `apps/api/service-account.json`)

> ⚠️ Never commit `service-account.json` to git. It is already in `.gitignore`.

### 3.3 Enable Required APIs

In your Google Cloud project, enable:
- **Vertex AI API** (`aiplatform.googleapis.com`)
- **Generative Language API** (`generativelanguage.googleapis.com`)

```bash
gcloud services enable aiplatform.googleapis.com generativelanguage.googleapis.com
```

### 3.4 Configure Service Account in `.env`

```bash
# apps/api/.env

AI_PROVIDER=gemini

# Leave GEMINI_API_KEYS empty (service account takes precedence)
GEMINI_API_KEYS=

# Service account settings
GEMINI_SERVICE_ACCOUNT_PATH=./service-account.json
GEMINI_PROJECT_ID=your-gcp-project-id
GEMINI_LOCATION=us-central1          # or us-east1, europe-west4, etc.

# Models available via Vertex AI
GEMINI_CHAT_MODEL=gemini-2.0-flash
GEMINI_EMBEDDING_MODEL=text-embedding-004
```

---

## 4. Verify Configuration

After setting keys, test that the provider is working:

```bash
make start          # start all services

# Check API health
curl http://localhost:8000/health

# Index the vault (triggers Gemini enrichment)
make index

# Watch enrichment logs
make logs-worker
# Look for: ai_call  provider=gemini  success=True
```

---

## 5. Available Gemini Models

### Chat Models

| Model | Speed | Context | Free tier |
|---|---|---|---|
| `gemini-2.0-flash` | Fast | 1M tokens | ✅ Yes |
| `gemini-2.0-flash-lite` | Very fast | 1M tokens | ✅ Yes |
| `gemini-1.5-pro` | Slower, smarter | 2M tokens | Limited |
| `gemini-2.5-pro` | Best quality | 1M tokens | Limited |

### Embedding Models

| Model | Dimensions | Notes |
|---|---|---|
| `text-embedding-004` | 768 | Recommended — stable, free tier |
| `gemini-embedding-exp-03-07` | 3072 | Experimental, higher quality |

Change models without touching Python code:

```bash
# apps/api/.env
GEMINI_CHAT_MODEL=gemini-2.5-pro
GEMINI_EMBEDDING_MODEL=text-embedding-004

# Restart to apply
make restart
```

---

## 6. Switching Back to Ollama

```bash
# apps/api/.env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
CHAT_MODEL=qwen3:0.6b
EMBEDDING_MODEL=bge-m3
```

Then:

```bash
make restart
```

No code changes required.

---

## 7. Key Rotation Details

When `AI_PROVIDER=gemini` and multiple keys are configured:

- Keys are used **round-robin** (key 1 → key 2 → ... → key N → key 1)
- On **HTTP 429** (quota exhausted) or **HTTP 403** (forbidden): automatically rotates to the next key and retries immediately
- On **5xx** (server error): exponential backoff (1 s → 2 s → 4 s) with the same key, then gives up
- On **4xx** other than 429/403 (bad request, invalid model): fails immediately

Each key gets **up to 60 requests/minute** (Gemini free tier). With 5 keys you get ~300 rpm effectively.

Rotation is logged:

```
[info] gemini_key_rotated  new_key_index=2  total_keys=5
```

---

## 8. Telemetry

Every AI call logs a structured `ai_call` event regardless of provider:

```
[info] ai_call  prompt=summarize  prompt_version=v1  model=gemini-2.0-flash  provider=gemini  latency_ms=1842  success=True
```

Monitor with:

```bash
make logs-api    # API service logs
make logs-worker # Enrichment worker logs
```

---

## 9. Troubleshooting

### `ValueError: AI_PROVIDER=gemini but neither GEMINI_API_KEYS nor GEMINI_SERVICE_ACCOUNT_PATH is configured`

Set at least one in `apps/api/.env`:

```bash
GEMINI_API_KEYS=AIzaSy...your_key_here
```

### `RuntimeError: Gemini generate failed (non-retryable)` with 400

Check that `GEMINI_CHAT_MODEL` is a valid Gemini model name:

```bash
# Valid: gemini-2.0-flash, gemini-1.5-pro
# Invalid: qwen3, gpt-4, gemini (no version)
GEMINI_CHAT_MODEL=gemini-2.0-flash
```

### All keys exhausted (429 on all keys)

You've hit the per-minute free quota on all keys. Options:
- Wait 60 seconds
- Use a service account with paid quota
- Switch to Ollama: `AI_PROVIDER=ollama`

### Service account: `google.auth.exceptions.DefaultCredentialsError`

- Verify `GEMINI_SERVICE_ACCOUNT_PATH` points to the correct JSON file
- Verify the file exists and is valid JSON
- Verify the service account has the **Vertex AI User** role
- Verify `GEMINI_PROJECT_ID` matches the project where Vertex AI is enabled

### Service account: `404 Publisher Model not found`

The model name differs for Vertex AI. Check available models in your region:

```bash
GEMINI_CHAT_MODEL=gemini-2.0-flash   # always use full version tag
GEMINI_LOCATION=us-central1          # try a different region if 404 persists
```

---

## 10. Security Notes

- **API keys**: treated as secrets. Store only in `apps/api/.env`, never in code.
- **Service account JSON**: already in `.gitignore`. Never commit it.
- **`.env` file**: also in `.gitignore`. Never commit it.
- To rotate a compromised key: delete it in [Google AI Studio](https://aistudio.google.com/apikey) and add a replacement to `GEMINI_API_KEYS`.
