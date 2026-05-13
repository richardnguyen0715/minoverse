# Issue 010: Entity Promotion Schema Mismatch — Graph Always Empty

## Status
Resolved

## Symptom
Graph always shows 0 nodes even after enrichment succeeds and produces non-empty entities.  
`GET /graph/full` returns `{"nodes": [], "edges": []}`.  
Worker logs show `empty_entities_list` debug messages despite enrichment containing entities.

## Root Cause
Phase 3 `entity_service.py` stores entities in a **categorized format**:

```json
{
  "tools": ["PyTorch"],
  "frameworks": ["Transformer"],
  "papers": ["Attention Is All You Need"],
  "methodologies": ["self-attention"]
}
```

Phase 4 `entity_promotion_service.py` tried to read a **flat format** that was never written:

```python
raw_entities = enrichment.content.get("entities", [])  # always []
```

The key `"entities"` never exists in the stored enrichment content, so the promotion service always received an empty list and promoted nothing.

## Fix
Updated `entity_promotion_service.py` to fall back to the categorized format when the flat `"entities"` key is absent, mapping each category to an entity type:

```python
raw_entities = enrichment.content.get("entities", [])

if not raw_entities:
    _type_map = {
        "tools": "technology",
        "frameworks": "framework",
        "papers": "concept",
        "methodologies": "concept",
    }
    for key, entity_type in _type_map.items():
        for name in enrichment.content.get(key, []):
            name = str(name).strip()
            if name:
                raw_entities.append({"name": name, "type": entity_type})
```

## Prevention Checklist
- [ ] When two phases share a data schema, define it once in a shared schema module
- [ ] Write an integration test asserting entity promotion produces > 0 entities given known enrichment content
- [ ] Document the enrichment content schema in `docs/` or in the relevant schema file
