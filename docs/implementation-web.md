# Web UI — Implementation Record

> Phase: Web UI (Next.js)  
> Commit: `6dc34ea`  
> Status: ✅ Complete — 18/18 tests passing

---

## Overview

Built a full-stack browser UI for the Minoverse knowledge operating system, connecting to the FastAPI backend (Phase 0–3) via REST. The UI follows the specifications in `.standards/phase 3-ui-design.md` and `.standards/implementation-plan.md`.

**Stack:** Next.js 15 · React 19 · TypeScript strict · Tailwind CSS v4 · shadcn/ui · Zustand v5 · React Flow (`@xyflow/react`) · react-markdown · Vitest

---

## Tasks Completed

### 1. Scaffold `apps/web/`

- `npx create-next-app@latest` with App Router, TypeScript, Tailwind, ESLint
- Installed: `zustand`, `@xyflow/react`, `react-markdown`, `remark-gfm`, `cmdk`, `lucide-react`, `clsx`, `tailwind-merge`
- Installed dev: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@vitejs/plugin-react`, `jsdom`
- Configured `vitest.config.ts` with jsdom environment and `@testing-library/jest-dom` setup

### 2. `src/lib/types.ts` — API types

Mirrors the FastAPI response shapes:

```typescript
export type ResourceType = 'paper' | 'youtube_video' | 'github_repo' | 'article'
  | 'documentation' | 'tweet' | 'note' | 'concept' | 'daily_note'

export interface Resource { id, title, resource_type, url, author, extra_metadata, ... }
export interface Note { id, resource_id, note_type, frontmatter, ... }
export interface WikiLink { id, source_resource_id, target_resource_id, alias, ... }
export interface AiEnrichment { id, resource_id, enrichment_type, content, model, ... }
export type EnrichmentType = 'summary_concise' | 'summary_detailed' | 'ai_tags' | 'entities' | 'related'
```

### 3. `src/lib/api.ts` — Typed API client

All methods use `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`). No axios — plain `fetch` with typed returns.

| Function | Endpoint |
|---|---|
| `fetchResources(type?)` | `GET /knowledge/resources` |
| `fetchResource(id)` | `GET /knowledge/resources/{id}` |
| `fetchNotes(type?)` | `GET /notes` |
| `fetchNote(id)` | `GET /notes/{id}` |
| `fetchNoteBacklinks(id)` | `GET /notes/{id}/backlinks` |
| `fetchEnrichments(id)` | `GET /enrichment/{id}` |
| `triggerEnrichment(id)` | `POST /enrichment/{id}/trigger` |

### 4. `src/lib/utils.ts` — Pure helpers

- `resourceTypeLabel(type)` — human-readable label (e.g. `"youtube_video"` → `"YouTube"`)
- `resourceTypeColor(type)` — Tailwind badge color class
- `formatDate(iso)` — locale date string with graceful fallback
- `buildApiUrl(path)` — prepends `NEXT_PUBLIC_API_URL`
- `cn(...classes)` — clsx + tailwind-merge utility

### 5. `src/store/ui-store.ts` — Zustand UIStore

```typescript
interface UIState {
  isPaletteOpen: boolean
  isSidebarOpen: boolean
  rightPanelTab: 'ai' | 'graph' | 'info'
  openPalette() / closePalette() / togglePalette()
  openSidebar() / closeSidebar() / toggleSidebar()
  setRightPanelTab(tab)
}
```

### 6. `src/store/knowledge-store.ts` — Zustand KnowledgeStore

```typescript
interface KnowledgeState {
  searchQuery: string
  resourceTypeFilter: ResourceType | null
  recentResources: Resource[]
  setSearchQuery(q) / setResourceTypeFilter(t) / addRecentResource(r) / clearRecents()
}
```

### 7. `src/components/command-palette.tsx` — ⌘K Command Palette

- Triggered by `Cmd+K` (or `Ctrl+K` on Windows/Linux)
- Debounced fetch against `/knowledge/resources` with query filter
- Keyboard navigation — arrow keys + Enter to open resource
- Built with `cmdk` (shadcn/ui Command primitive)
- Shows resource type badge, title, and type icon

### 8. `src/components/layout/` — App shell

- `sidebar.tsx` — Left sidebar: Library nav by type (All, Papers, Notes, Concepts, Daily, YouTube, GitHub, Articles, Docs, Tweets), Recent Resources list (up to 10)
- `right-panel.tsx` — Right context panel with tab bar: **AI** · **Graph** · **Info**
- `app-shell.tsx` — 3-column layout wrapper (sidebar + main + right panel)

### 9. `src/components/knowledge/` — Knowledge components

- `resource-card.tsx` — Card for resource grid: title, type badge, author, date, tags preview
- `enrichment-panel.tsx` — Renders AI enrichments inside the right panel:
  - Summary (concise or detailed)
  - AI-generated tags (badge list)
  - Extracted entities (grouped by type)
  - Related resources (linked list)
  - Trigger re-enrichment button

### 10. `src/components/graph/` — React Flow knowledge graph

- `knowledge-graph.tsx` — Local neighborhood graph for a resource
  - Nodes: the central resource + linked resources (wiki links)
  - Edges: forward and backlinks
  - Node click → navigate to that resource
  - Controls: zoom in/out, fit view, minimap
  - Dark-mode styled with CSS variables

### 11. `src/app/layout.tsx` — Root layout

- `<html lang="en" className="dark">` — dark theme by default
- Providers wrapper: Zustand + command palette listener
- Inter font via `next/font/google`
- Tailwind globals + CSS variables for shadcn/ui

### 12. `src/app/page.tsx` — Root redirect → `/resources`

### 13. `src/app/resources/page.tsx` — Resource list

- Type filter tabs (All / Paper / Note / Concept / Daily / YouTube / GitHub / Article / Docs / Tweet)
- Search bar (controlled, debounced 300ms)
- Responsive resource card grid
- Empty state with icon + copy
- Syncs filter with KnowledgeStore

### 14. `src/app/resources/[id]/page.tsx` — Resource viewer

- Fetches resource + enrichments in parallel (Promise.all)
- Left: document content area — title, type badge, metadata row (author, date, URL), heading TOC from `extra_metadata`
- Right panel: AI tab (EnrichmentPanel), Graph tab (KnowledgeGraph), Info tab (raw metadata)
- Adds resource to `recentResources` on load

### 15. `src/app/notes/page.tsx` — Notes list

- Filter by note type (all / note / concept / daily_note)
- Card grid with frontmatter preview

### 16. `src/app/notes/[id]/page.tsx` — Note viewer

- Fetches note + backlinks in parallel
- Renders frontmatter as metadata row
- Backlinks section at bottom (wiki links pointing here)

### 17. Tests — `src/__tests__/`

**18/18 passing**

| File | Tests |
|---|---|
| `lib/utils.test.ts` | `resourceTypeLabel`, `resourceTypeColor`, `formatDate`, `cn`, `buildApiUrl` — 10 tests |
| `lib/api.test.ts` | `fetchResources`, `fetchResource`, `fetchEnrichments` — mock fetch, typed returns — 5 tests |
| `store/ui-store.test.ts` | palette open/close/toggle, sidebar toggle, rightPanelTab — 3 tests |

### 18. `start.sh` step ⑩ + `stop.sh`

- Step ⑩ in `scripts/start.sh`: starts `npm run dev` in `apps/web/`, saves PID to `.minoverse/web.pid`, logs to `.minoverse/web.log`
- `scripts/stop.sh`: reads `.minoverse/web.pid` and kills the Next.js process
- `Makefile`: added `web-install`, `web-dev`, `web-build`, `web-test`, `logs-web`; `make test` now runs both API pytest and web Vitest

---

## CORS

FastAPI `src/main.py` already had `CORSMiddleware` allowing `http://localhost:3000`. No changes needed.

---

## Environment Variable

`apps/web/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

This file is gitignored. `apps/web/.env.local.example` is committed as a template.

---

## Design Decisions

| Decision | Rationale |
|---|---|
| Dark theme by default | Per `.standards/phase 3-ui-design.md` |
| 3-column layout | Sidebar + workspace + right context panel per spec |
| No axios — plain `fetch` | Minimize deps; Next.js native fetch has caching hooks |
| Zustand (not Context) | Per spec; simpler API, no Provider nesting |
| `cmdk` for palette | shadcn-compatible, WAI-ARIA keyboard nav built-in |
| `@xyflow/react` v12 | Per spec; stable API, dark mode via CSS vars |
| react-markdown + remark-gfm | Per spec; GFM tables/strikethrough/task lists |
| Vitest (not Jest) | Native ESM, faster, Vite-aligned; per `.standards/testing-debugging-frameworks.md` |
| No raw markdown body | `resource_contents` table is empty until Phase 2; UI shows metadata + enrichments |

---

## Files Created

```
apps/web/
├── .env.local                        API URL env
├── .env.local.example               Template (committed)
├── next.config.ts
├── tsconfig.json
├── vitest.config.ts
├── components.json                  shadcn/ui config
├── src/
│   ├── app/
│   │   ├── layout.tsx               Root layout (dark, providers)
│   │   ├── page.tsx                 Redirect → /resources
│   │   ├── globals.css              Tailwind + CSS vars
│   │   ├── resources/
│   │   │   ├── page.tsx             Resource list
│   │   │   └── [id]/page.tsx        Resource viewer
│   │   └── notes/
│   │       ├── page.tsx             Notes list
│   │       └── [id]/page.tsx        Note viewer
│   ├── components/
│   │   ├── command-palette.tsx      ⌘K palette
│   │   ├── providers.tsx            Zustand + global listeners
│   │   ├── layout/
│   │   │   ├── app-shell.tsx        3-column shell
│   │   │   ├── sidebar.tsx          Left nav + recents
│   │   │   └── right-panel.tsx      AI/Graph/Info tabs
│   │   ├── knowledge/
│   │   │   ├── resource-card.tsx    Grid card
│   │   │   └── enrichment-panel.tsx AI enrichments display
│   │   ├── graph/
│   │   │   └── knowledge-graph.tsx  React Flow graph
│   │   └── ui/                      shadcn primitives (Button, Badge, Tabs, etc.)
│   ├── lib/
│   │   ├── types.ts                 API response types
│   │   ├── api.ts                   Typed fetch client
│   │   └── utils.ts                 Pure helpers
│   ├── store/
│   │   ├── ui-store.ts              Palette/sidebar/panel state
│   │   └── knowledge-store.ts       Search/filter/recents state
│   └── __tests__/
│       ├── setup.ts                 jest-dom matchers
│       ├── lib/
│       │   ├── utils.test.ts        10 pure-util tests
│       │   └── api.test.ts          5 fetch-mock tests
│       └── store/
│           └── ui-store.test.ts     3 store tests
```
