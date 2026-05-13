# Phase 1 — Knowledge Core: Usage Guide

> **Prerequisites:** Phase 0 is running (Postgres, Redis, API server).  
> See [`docs/phase-0-usage.md`](./phase-0-usage.md) if the stack is not yet started.

---

## Quick Reference

| Task | Command |
|---|---|
| Index entire vault | `cd apps/api && uv run minoverse index` |
| Start live watcher | `cd apps/api && uv run minoverse watch` |
| Check graph stats | `cd apps/api && uv run minoverse graph` |
| List resources via API | `curl http://localhost:8000/knowledge/resources` |
| List notes via API | `curl http://localhost:8000/knowledge/notes` |
| Get backlinks | `curl http://localhost:8000/notes/{id}/backlinks` |
| Run tests | `cd apps/api && uv run pytest src/ -v` |

---

## 1. Apply the Phase 1 Migration

Migration `002` adds unique constraints required by the upsert repositories. Run this **once** before using Phase 1 features.

```bash
cd apps/api
uv run alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, add vault_file_id unique constraints
```

Verify current head:
```bash
uv run alembic current
# 002 (head)
```

---

## 2. Install Phase 1 Dependencies

If you cloned fresh or haven't synced since Phase 1 was added:

```bash
cd apps/api
uv sync
```

This picks up `markdown-it-py`, `python-frontmatter`, and `typer`.

---

## 3. Vault Setup

The vault directory lives at `vault/` in the repo root. It is pre-structured from Phase 0:

```
vault/
├── resources/
│   ├── papers/
│   ├── youtube/
│   ├── github/
│   ├── articles/
│   ├── docs/
│   └── social/
├── notes/
├── concepts/
├── daily/
├── templates/
└── attachments/
```

Place `.md` files anywhere under `vault/`. Subdirectory location determines the **resource type** assigned during indexing:

| Vault path | Resource type |
|---|---|
| `vault/resources/papers/*.md` | `paper` |
| `vault/resources/youtube/*.md` | `youtube_video` |
| `vault/resources/github/*.md` | `github_repo` |
| `vault/resources/articles/*.md` | `article` |
| `vault/resources/docs/*.md` | `documentation` |
| `vault/resources/social/*.md` | `tweet` |
| `vault/notes/*.md` | `note` |
| `vault/concepts/*.md` | `concept` |
| `vault/daily/*.md` | `daily_note` |
| Anywhere else | `note` (default) |

---

## 4. Markdown File Format

Minoverse reads standard Obsidian-compatible markdown. All frontmatter fields are optional.

```markdown
---
title: My Note Title
tags: [ai, productivity, research]
author: Jane Doe
url: https://example.com
aliases: [short-name, alt-title]
---

# My Note Title

Body content here. You can link to other notes with [[wiki links]].

Use [[Note Name|Display Text]] for aliased links.

## Section Heading

More content...
```

### Supported Frontmatter Keys

| Key | Type | Effect |
|---|---|---|
| `title` | string | Overrides filename-derived title |
| `tags` | list or string | Stored in `tags` table and linked to resource |
| `aliases` | list or string | Stored in resource `extra_metadata` |
| `url` | string | Stored in `resources.url` |
| `author` | string | Stored in `resources.author` |
| `language` | string | Stored in `resources.language` |

Any other frontmatter key is stored as-is in `notes.frontmatter` (JSONB).

---

## 5. CLI Commands

### `minoverse index` — Index the Vault

Scans all `*.md` files in the vault and ingests them into the database. This is **idempotent** — safe to re-run at any time.

```bash
cd apps/api
uv run minoverse index
```

Output:
```
📚 Indexing vault: /path/to/minoverse/vault
✅ Indexed 42/42 files
```

If any files fail:
```
✅ Indexed 40/42 files
⚠️  2 files failed:
   • vault/notes/broken.md: Failed to parse frontmatter
   • vault/notes/missing.md: Vault file not found
```

**Override vault path** (useful for testing with a different vault):
```bash
uv run minoverse index --vault /path/to/other/vault
```

### `minoverse watch` — Live File Watcher

Starts a long-running daemon that watches the vault for filesystem changes and automatically ingests new/modified files and soft-deletes removed files.

```bash
cd apps/api
uv run minoverse watch
```

Output:
```
👁  Watching vault: /path/to/minoverse/vault  (Ctrl+C to stop)
```

**What triggers ingestion:**
- New `.md` file created in vault
- Existing `.md` file modified (save in editor)
- `.md` file deleted (soft-deleted in DB)

Non-markdown files (images, PDFs, etc.) are silently ignored.

**Stop the watcher:** `Ctrl+C`

**Run as a background process:**
```bash
# Run in a separate terminal, or detach with nohup
nohup uv run minoverse watch > /tmp/minoverse-watch.log 2>&1 &
echo $! > /tmp/minoverse-watch.pid

# Stop it later
kill $(cat /tmp/minoverse-watch.pid)
```

### `minoverse graph` — Knowledge Graph Stats

Queries the DB and prints current node and edge counts. Requires the API stack to be running (Postgres must be reachable).

```bash
cd apps/api
uv run minoverse graph
```

Output:
```
📊 Knowledge Graph Stats
   Vault files : 42
   Resources   : 42
   Notes       : 38
   Wiki links  : 127
```

### Stubs (Phase 2+ Commands)

These commands exist but are not yet implemented:

```bash
uv run minoverse rebuild     # Phase 3 — rebuild chunk embeddings
uv run minoverse search "query"  # Phase 2 — hybrid search
```

---

## 6. REST API

The API server must be running. Start it if not already:

```bash
cd apps/api
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive docs: http://localhost:8000/docs

### List Vault Files

```bash
curl http://localhost:8000/knowledge/vault-files | python3 -m json.tool
```

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "relative_path": "notes/my-note.md",
    "sync_status": "indexed",
    "file_hash": "abc123...",
    "file_size": 1204
  }
]
```

### List Resources

```bash
# All resources
curl http://localhost:8000/knowledge/resources

# Filter by type
curl "http://localhost:8000/knowledge/resources?resource_type=paper"
curl "http://localhost:8000/knowledge/resources?resource_type=note"
curl "http://localhost:8000/knowledge/resources?resource_type=youtube_video"
```

### Get Single Resource

```bash
curl http://localhost:8000/knowledge/resources/{resource_id}
```

```json
{
  "id": "...",
  "vault_file_id": "...",
  "resource_type": "paper",
  "title": "Attention Is All You Need",
  "url": "https://arxiv.org/abs/1706.03762",
  "author": "Vaswani et al.",
  "language": "en",
  "extra_metadata": {
    "headings": [{"level": 1, "text": "Abstract", "slug": "abstract"}],
    "urls": ["https://arxiv.org/abs/1706.03762"],
    "aliases": [],
    "word_count": 842
  },
  "is_favorite": false,
  "is_archived": false,
  "created_at": "2026-05-09T15:30:00+00:00",
  "updated_at": "2026-05-09T15:30:00+00:00"
}
```

### List Notes

```bash
# All notes
curl http://localhost:8000/notes

# Filter by type
curl "http://localhost:8000/notes?note_type=daily_note"
curl "http://localhost:8000/notes?note_type=concept"
```

### Get Single Note

```bash
curl http://localhost:8000/notes/{note_id}
```

```json
{
  "id": "...",
  "vault_file_id": "...",
  "title": "My Note",
  "note_type": "note",
  "frontmatter": {"tags": ["ai", "research"], "author": "Me"},
  "created_at": "2026-05-09T15:30:00+00:00",
  "updated_at": "2026-05-09T15:30:00+00:00"
}
```

### Get Backlinks

Returns all wiki links that point **to** the specified note — i.e., which notes reference this one.

```bash
curl http://localhost:8000/notes/{note_id}/backlinks
```

```json
[
  {
    "id": "...",
    "source_note_id": "...",
    "anchor_text": "My Note"
  }
]
```

---

## 7. End-to-End Demo

This demo walks through indexing a sample vault and verifying the results.

**Step 1: Start the stack (if not running)**
```bash
cd infra && docker compose up -d
cd ../apps/api && uv run alembic upgrade head
```

**Step 2: Create a test note**
```bash
cat > vault/notes/my-first-note.md << 'EOF'
---
title: My First Note
tags: [demo, test]
---

# My First Note

This is a test note. It links to [[Second Note]].

See also: https://minoverse.dev
EOF
```

**Step 3: Create a second note**
```bash
cat > vault/notes/second-note.md << 'EOF'
---
title: Second Note
tags: [demo]
---

# Second Note

This note is referenced by [[My First Note]].
EOF
```

**Step 4: Index the vault**
```bash
cd apps/api && uv run minoverse index
# 📚 Indexing vault: .../vault
# ✅ Indexed 2/2 files
```

**Step 5: Check graph stats**
```bash
uv run minoverse graph
# 📊 Knowledge Graph Stats
#    Vault files : 2
#    Resources   : 2
#    Notes       : 2
#    Wiki links  : 2
```

**Step 6: List notes via API**
```bash
curl http://localhost:8000/notes | python3 -m json.tool
```

**Step 7: Get backlinks for Second Note**
```bash
# Get Second Note's ID first
NOTE_ID=$(curl -s http://localhost:8000/notes | python3 -c "
import sys, json
notes = json.load(sys.stdin)
n = next(n for n in notes if n['title'] == 'Second Note')
print(n['id'])
")

curl http://localhost:8000/notes/$NOTE_ID/backlinks | python3 -m json.tool
# Returns: My First Note → Second Note link
```

**Step 8: Start the live watcher**
```bash
uv run minoverse watch &
# 👁  Watching vault: .../vault  (Ctrl+C to stop)
```

**Step 9: Add a note and watch it auto-index**
```bash
echo '---
title: Live Test
tags: [live]
---
# Live Test
Auto-indexed!' > vault/notes/live-test.md

# The watcher log will show:
# vault_file_changed change_type=created path=.../live-test.md
# vault_file_ingested relative_path=notes/live-test.md
```

---

## 8. Running Tests

```bash
cd apps/api
uv run pytest src/ -v
```

Expected output:
```
============================= test session starts ==============================
collected 19 items

src/graph/tests/test_wiki_link_service.py::... PASSED
src/ingestion/tests/test_markdown_parser.py::... PASSED
...
============================== 19 passed in 0.06s ==============================
```

Run a specific test module:
```bash
uv run pytest src/ingestion/tests/ -v
uv run pytest src/graph/tests/ -v
```

---

## 9. Debugging

### Database: Inspect Indexed Data

Connect to Postgres and inspect what was indexed:

```bash
docker exec -it minoverse-postgres-1 psql -U minoverse -d minoverse

-- Check vault files
SELECT relative_path, sync_status, file_size FROM vault_files ORDER BY created_at DESC;

-- Check resources
SELECT title, resource_type, created_at FROM resources WHERE deleted_at IS NULL;

-- Check notes
SELECT title, note_type FROM notes ORDER BY created_at DESC;

-- Check wiki links
SELECT target_raw, anchor_text FROM wiki_links LIMIT 20;

-- Check tags
SELECT t.name, COUNT(rt.resource_id) AS usage
FROM tags t
JOIN resource_tags rt ON rt.tag_id = t.id
GROUP BY t.name ORDER BY usage DESC;
```

### Logs: Structured Structlog Output

In development mode (default), logs are human-readable via structlog dev renderer:

```
2026-05-09 22:00:01 [info     ] ingesting_vault_file  relative_path=notes/my-note.md
2026-05-09 22:00:01 [info     ] vault_file_ingested   relative_path=notes/my-note.md resource_id=... wiki_links=3 tags=2
```

Set `DEBUG=true` in `apps/api/.env` for verbose debug output.

### Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Vault not found: /path/to/vault` | `VAULT_PATH` in `.env` is wrong | Set correct absolute path in `apps/api/.env` |
| `File is outside vault root` | Trying to index a file outside `VAULT_PATH` | Only pass files under `vault/` to `ingest_vault_file()` |
| `Failed to parse frontmatter` | Invalid YAML in `---` block | Fix the YAML syntax in the file's frontmatter |
| `sqlalchemy.exc.OperationalError` | Postgres is not running | `cd infra && docker compose up -d postgres` |
| `alembic: Can't locate revision 002` | Migration not applied | `cd apps/api && uv run alembic upgrade head` |
| Watcher not picking up changes | `vault_path` doesn't exist | Check `VAULT_PATH` in `.env` points to existing directory |

### Re-index Everything

If the database gets out of sync with the vault (e.g., after a schema change):

```bash
# Reset DB
cd apps/api
uv run alembic downgrade base
uv run alembic upgrade head

# Re-index
uv run minoverse index
```

---

## 10. Environment Variables

All Phase 1 behaviour is controlled via `apps/api/.env` (copied from `infra/.env.example`):

| Variable | Default | Description |
|---|---|---|
| `VAULT_PATH` | `../../vault` | Path to vault directory (relative to `apps/api/` or absolute) |
| `DATABASE_URL` | `postgresql+asyncpg://minoverse:minoverse@localhost:5432/minoverse` | Postgres connection string |
| `DEBUG` | `false` | Enable debug logging |

The `VAULT_PATH` must be readable by the process running `minoverse index` or `minoverse watch`.
