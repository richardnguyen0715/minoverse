# Phase 1 — Knowledge Core: Implementation Record

> **Status:** Complete  
> **Completed:** 2026-05-09  
> **Commit range:** follows Phase 0 (`667a402`)  
> **Tests:** 19 / 19 passed  
> **Migration applied:** `002_add_vault_file_unique_constraints`

---

## Overview

Phase 1 delivers the ingestion backbone of minoverse: the ability to parse, store, and link markdown vault files. After Phase 1, the vault is the single source of truth; the database is a live, queryable projection of it.

### Goals

| Goal | Outcome |
|---|---|
| Parse markdown files into structured data | `ParsedDocument` dataclass via markdown-it-py + python-frontmatter |
| Store parsed files idempotently | Upsert repositories for `vault_files`, `resources`, `notes` |
| Resolve and store wiki links | Forward links + backlink graph in `wiki_links` table |
| Tag resources from frontmatter | Get-or-create tag pipeline |
| Live vault sync | Async file watcher emitting events |
| CLI for vault operations | `minoverse index`, `watch`, `graph` |
| REST API for knowledge data | Routes on `/knowledge` and `/notes` |

---

## Task 1.0 — Dependencies and Package Config

**Files changed:** `apps/api/pyproject.toml`

Three new runtime dependencies were added:

| Package | Version | Purpose |
|---|---|---|
| `markdown-it-py` | `>=3.0` | AST-level markdown parsing (headings, links, inline tokens) |
| `python-frontmatter` | `>=1.1` | YAML frontmatter extraction from `.md` files |
| `typer` | `>=0.12` | CLI framework for `minoverse` commands |

A CLI entrypoint was added to `[project.scripts]`:

```toml
[project.scripts]
minoverse = "src.cli.main:app"
```

This makes `uv run minoverse` available from within `apps/api/`.

---

## Task 1.1 — Markdown Parser

**Files created:**
- `apps/api/src/ingestion/schemas/parsed_document.py`
- `apps/api/src/ingestion/pipelines/markdown_parser.py`

### Design Constraints

- **Pure module** — no I/O side effects beyond reading the input file
- **Single entry point** — `parse_markdown_file(file_path: Path) → ParsedDocument`
- **Only one regex allowed** — for Obsidian wiki-link syntax (`[[target]]`, `[[target|alias]]`), which markdown-it-py does not handle natively
- All other parsing is done through the markdown-it-py AST token stream

### `ParsedDocument` Schema

```python
@dataclass
class ParsedDocument:
    source_path: Path
    frontmatter: dict[str, object]   # raw YAML key/value pairs
    body: str                        # content without frontmatter
    raw_markdown: str                # full file content
    headings: list[Heading]          # in document order
    wiki_links: list[WikiLinkRef]    # deduplicated [[links]]
    tags: list[str]                  # lowercased, deduplicated
    urls: list[str]                  # http/https URLs
    aliases: list[str]               # from frontmatter aliases key
    char_count: int
    word_count: int
```

### Parsing Pipeline (internal)

```
file_path.read_text()
  → frontmatter.loads()        extract YAML frontmatter + body
  → MarkdownIt().parse(body)   produce token stream (AST)
  → _extract_headings()        walk token stream for heading_open tokens
  → _extract_wiki_links()      regex scan body for [[...]]
  → _extract_tags()            frontmatter["tags"] (list or space-separated string)
  → _extract_urls()            walk link_open tokens + bare URL regex fallback
  → _extract_aliases()         frontmatter["aliases"]
  → ParsedDocument(...)
```

### Wiki Link Regex

```python
_WIKI_LINK_RE = re.compile(r"\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]")
```

- Group 1: target (required)
- Group 2: alias (optional, after `|`)
- Results are deduplicated by target

### Title Resolution (in ingestion service)

Priority order:
1. `frontmatter["title"]`
2. First H1 heading from AST
3. File stem converted to Title Case (dashes/underscores → spaces)

### Resource Type Resolution

Vault subdirectory prefixes map to canonical resource types:

| Vault path prefix | Resource type |
|---|---|
| `resources/papers/` | `paper` |
| `resources/youtube/` | `youtube_video` |
| `resources/github/` | `github_repo` |
| `resources/articles/` | `article` |
| `resources/docs/` | `documentation` |
| `resources/social/` | `tweet` |
| `notes/` | `note` |
| `concepts/` | `concept` |
| `daily/` | `daily_note` |
| (anything else) | `note` |

---

## Task 1.2 — File Watcher Service

**File created:** `apps/api/src/ingestion/services/file_watcher_service.py`

### Design Constraints

- **No parsing** inside the watcher
- **No DB access** inside the watcher
- Emits exactly one `VaultChangeEvent` per filesystem change
- Only watches `.md` files (others silently ignored)

### Interface

```python
async def watch_vault(
    vault_path: Path,
    on_change: Callable[[VaultChangeEvent], Coroutine],
    *,
    glob_pattern: str = "**/*.md",
) -> None: ...
```

`watchfiles.awatch()` is used for async, cross-platform filesystem watching. The callback `on_change` is awaited for each event — for high-throughput use, enqueue to a task queue inside the callback.

### Change Types

```python
class VaultChangeType(StrEnum):
    CREATED  = "created"
    MODIFIED = "modified"
    DELETED  = "deleted"
```

---

## Task 1.3 — Repositories

**Files created:**

| File | Responsibility |
|---|---|
| `knowledge/repositories/vault_file_repository.py` | `upsert_vault_file()`, `mark_vault_file_deleted()` |
| `knowledge/repositories/resource_repository.py` | `upsert_resource()` |
| `notes/repositories/note_repository.py` | `upsert_note()` |
| `graph/repositories/wiki_link_repository.py` | `upsert_wiki_links()`, `get_backlinks()` |

### Upsert Pattern

All repositories use PostgreSQL `ON CONFLICT DO UPDATE` via SQLAlchemy:

```python
stmt = pg_insert(VaultFile).values(...).on_conflict_do_update(
    index_elements=["relative_path"],
    set_={...},
)
```

This requires the unique constraints added in migration `002` (see below).

### `mark_vault_file_deleted()`

Sets `sync_status = "deleted"` and `deleted_at = now()` without removing the row — soft delete to preserve referential integrity.

---

## Task 1.4 — Wiki Link Service

**File created:** `apps/api/src/graph/services/wiki_link_service.py`

```python
async def extract_and_store_wiki_links(
    session: AsyncSession,
    source_note: Note,
    parsed_doc: ParsedDocument,
) -> None: ...
```

### Resolution Logic

For each `WikiLinkRef` in the parsed document:

1. Look up `notes` table by `title` matching the wiki link target
2. If found → store a resolved forward link (source → target)
3. If not found → store an unresolved link (target recorded as text only)

This means the graph is built incrementally — links resolve as their target notes are indexed.

---

## Task 1.5 — Tag Service

**File created:** `apps/api/src/tagging/services/tag_service.py`

```python
async def upsert_tags_for_resource(
    session: AsyncSession,
    resource_id: uuid.UUID,
    tags: list[str],
) -> None: ...
```

### Tag Pipeline

1. For each tag name: `INSERT INTO tags ... ON CONFLICT DO NOTHING` (get or create)
2. Clear existing `resource_tags` for this resource
3. Insert new `resource_tags` rows (resource ↔ tag associations)

Tags are stored lowercased and stripped, matching the parser's normalization.

---

## Task 1.6 — Ingestion Service (Pipeline Orchestrator)

**File created:** `apps/api/src/ingestion/services/ingestion_service.py`

This is the central coordinator. Both the CLI `index` command and the file watcher call it.

### Pipeline Steps (in order)

```
ingest_vault_file(file_path, session)
  1. resolve relative_path from vault root
  2. parse_markdown_file()              → ParsedDocument
  3. compute_file_hash()                → SHA-256 hex
  4. upsert_vault_file()               → VaultFile row
  5. upsert_resource()                 → Resource row
  6. upsert_note()                     → Note row
  7. session.flush()                   (make IDs available)
  8. extract_and_store_wiki_links()    [non-fatal on error]
  9. upsert_tags_for_resource()        [non-fatal on error]
  10. session.commit()
```

### Failure Isolation

Steps 8 and 9 (wiki links and tags) are wrapped in `try/except` and log a `warning` on failure without aborting. The core vault_file + resource + note persistence always commits.

### Delete Handling

```python
async def delete_vault_file(file_path: Path, session: AsyncSession) -> None: ...
```

Soft-deletes the `vault_files` row and its resource (sets `deleted_at`).

---

## Task 1.7 — Vault Indexing Service

**File created:** `apps/api/src/knowledge/services/vault_indexing_service.py`

```python
async def index_vault(vault_path: Path) -> IndexResult: ...
```

Walks the vault directory for all `*.md` files and calls `ingest_vault_file()` for each. Returns an `IndexResult` with counts:

```python
@dataclass
class IndexResult:
    total_files: int
    indexed: int
    failed: int
    errors: list[str]
```

---

## Task 1.8 — CLI

**File created:** `apps/api/src/cli/main.py`

Built with Typer. Entrypoint: `uv run minoverse`.

| Command | Description |
|---|---|
| `minoverse index [--vault PATH]` | Scan and index all `.md` files in the vault |
| `minoverse watch [--vault PATH]` | Start the live file watcher daemon |
| `minoverse graph` | Print knowledge graph node/edge counts |
| `minoverse rebuild` | Stub — Phase 3 (embedding rebuild) |
| `minoverse search QUERY` | Stub — Phase 2 (hybrid retrieval) |

---

## Task 1.9 — REST API Routes

**Files created:**
- `apps/api/src/knowledge/routes.py` — prefix `/knowledge`
- `apps/api/src/notes/routes.py` — prefix `/notes`

Both routers are registered in `src/main.py`.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/knowledge/vault-files` | List all indexed vault files (max 100) |
| `GET` | `/knowledge/resources` | List resources, optional `?resource_type=` filter |
| `GET` | `/knowledge/resources/{id}` | Fetch single resource with full metadata |
| `GET` | `/notes` | List all notes, optional `?note_type=` filter |
| `GET` | `/notes/{id}` | Fetch single note with frontmatter |
| `GET` | `/notes/{id}/backlinks` | List all wiki links pointing TO this note |

---

## Task 1.10 — Alembic Migration 002

**File created:** `apps/api/alembic/versions/002_add_vault_file_unique_constraints.py`

Adds `UNIQUE` constraints required by the upsert repositories:

```sql
ALTER TABLE resources ADD CONSTRAINT uq_resources_vault_file_id UNIQUE (vault_file_id);
ALTER TABLE notes     ADD CONSTRAINT uq_notes_vault_file_id     UNIQUE (vault_file_id);
```

These enable the `ON CONFLICT (vault_file_id) DO UPDATE` clauses used in the resource and note upserts.

---

## Task 1.11 — Exception Extension

**File modified:** `apps/api/src/core/exceptions.py`

Added `MarkdownParseError`:

```python
class MarkdownParseError(MinoverseError):
    """Raised when a markdown file cannot be parsed."""
```

Used by `parse_markdown_file()` to wrap frontmatter parse failures.

---

## Tests

**19 pure unit tests — no DB, no I/O mocking required.**

| Test file | Test class | What it covers |
|---|---|---|
| `ingestion/tests/test_markdown_parser.py` | `TestParseMarkdownFile` | YAML frontmatter, body separation, missing file, char count |
| `ingestion/tests/test_markdown_parser.py` | `TestExtractWikiLinks` | Simple links, aliased links, deduplication, multiple, empty |
| `ingestion/tests/test_markdown_parser.py` | `TestExtractHeadings` | H1, multi-level, slug generation |
| `ingestion/tests/test_markdown_parser.py` | `TestExtractTags` | List tags, string tags, no tags, deduplication |
| `graph/tests/test_wiki_link_service.py` | `TestWikiLinkExtraction` | No links, nested brackets ignored, heading fragment links |

All tests are pure (no side effects) and run in 0.06 seconds.

```bash
cd apps/api
uv run pytest src/ -v
# 19 passed in 0.06s
```

---

## Architecture Notes

### Domain Isolation

Each domain (`knowledge`, `notes`, `graph`, `ingestion`, `tagging`) owns its own entities, repositories, services, schemas, and tests. Cross-domain dependencies flow in one direction:

```
ingestion/services → knowledge/repositories
                   → notes/repositories
                   → graph/services
                   → tagging/services
```

No domain imports from `ingestion` except through service interfaces.

### No Business Logic in Watcher

The file watcher is intentionally dumb — it maps filesystem events to `VaultChangeEvent` and calls the injected callback. All parsing, DB writes, and error handling live in `ingestion_service.py`.

### Idempotency Guarantee

`ingest_vault_file()` can be called any number of times for the same file with identical results. The database state converges to the current file content on every run. This means `minoverse index` is safe to re-run at any time.

### Soft Deletes

Deleted vault files are never removed from the DB — they are soft-deleted with `sync_status = "deleted"` and `deleted_at = now()`. This preserves link integrity and allows future recovery or audit.
