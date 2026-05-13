# Issue 007: Ollama Models Not Pulled

## Status
Resolved

## Symptom
All AI enrichment produces empty results: `{"tags": [], "text": "", "entities": {}}`.  
`GET /graph/full` returns `{"nodes": [], "edges": []}` even after indexing.  
Worker logs show `HTTP 404` responses from Ollama.

## Root Cause
The Ollama container starts empty. Models are **not** pulled automatically.  
`CHAT_MODEL=qwen3` in `.env` refers to the full `qwen3` tag which is ~5 GB.  
`qwen3:0.6b` (522 MB) is a sufficient substitute for development.

## Fix
```bash
docker exec -it minoverse_ollama ollama pull qwen3:0.6b
docker exec -it minoverse_ollama ollama pull bge-m3
```

Update `.env`:
```
CHAT_MODEL=qwen3:0.6b
EMBEDDING_MODEL=bge-m3
```

## Prevention Checklist
- [ ] Add model pull step to `make setup` / first-run documentation
- [ ] Check `docker exec minoverse_ollama ollama list` shows expected models before indexing
- [ ] `GET /health` should report Ollama model availability
