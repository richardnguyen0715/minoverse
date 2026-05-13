# Minoverse — Development Makefile
#
# Usage:
#   make start     — start the full stack (infra + API + watcher)
#   make stop      — stop everything
#   make restart   — stop then start
#   make status    — show what is running
#   make logs-api  — tail the API server log
#   make logs-watch — tail the vault watcher log
#   make index     — re-index the vault manually
#   make migrate   — apply pending Alembic migrations
#   make test      — run all tests
#   make lint      — run ruff + mypy
#
# AutoIngest:
#   make ingest-install   — install AutoIngest CLI deps
#   make ingest <url>     — analyze a URL (shortcut)
#   make research <topic> — research a topic
#   make telegram         — start the Telegram bot (dev polling mode)
#   make scraping         — start the scraping service

.PHONY: start stop restart status \
        logs-api logs-watch logs-worker logs-web \
        index migrate test lint worker graph \
        web-install web-dev web-build web-test \
        copilot memory sync \
        desktop-install desktop-rust desktop-dev desktop-build desktop-package desktop-open \
        ingest-install ingest-dev ingest-analyze ingest-research ingest-memory ingest-health \
        telegram telegram-install telegram-dev \
        scraping-install scraping-dev \
        docker-up docker-down docker-up-telegram \
        help

# ── Lifecycle ────────────────────────────────────────────────────────────────

start:
	@bash scripts/start.sh

stop:
	@bash scripts/stop.sh

restart: stop start

status:
	@bash scripts/status.sh

# ── Logs ─────────────────────────────────────────────────────────────────────

logs-api:
	@tail -f .minoverse/api.log

logs-watch:
	@tail -f .minoverse/watcher.log

logs-worker:
	@tail -f .minoverse/worker.log

# ── Vault ────────────────────────────────────────────────────────────────────

index:
	@cd apps/api && uv run minoverse index

# ── Database ─────────────────────────────────────────────────────────────────

migrate:
	@cd apps/api && uv run alembic upgrade head

worker:
	@cd apps/api && .venv/bin/python -m dramatiq src.workers

graph:
	@cd apps/api && uv run minoverse graph

web-install:
	@cd apps/web && npm install

web-dev:
	@cd apps/web && npm run dev

web-build:
	@cd apps/web && npm run build

web-test:
	@cd apps/web && npm test

logs-web:
	@tail -f .minoverse/web.log

# ── Phase 5 — AI Copilot + Memory ────────────────────────────────────────────

copilot:
	@open http://localhost:3000/copilot 2>/dev/null || echo "Open http://localhost:3000/copilot"

memory:
	@open http://localhost:3000/memory 2>/dev/null || echo "Open http://localhost:3000/memory"

# ── Phase 6 — Sync & Desktop ─────────────────────────────────────────────────

sync:
	@open http://localhost:3000/sync 2>/dev/null || echo "Open http://localhost:3000/sync"

desktop-install:
	@cd apps/desktop && npm install

desktop-rust:
	@echo "Installing Rust toolchain (stable)..."
	@curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
	@echo "Rust installed. Restart your shell or run: source ~/.cargo/env"

desktop-dev:
	@export PATH="$$HOME/.cargo/bin:$$PATH" && \
	cargo --version > /dev/null 2>&1 || \
	  (echo "" && echo "❌  Rust / Cargo not found." && \
	   echo "    Run:  make desktop-rust" && echo "" && exit 1) && \
	echo "▶  Starting Minoverse desktop (splash → services → web UI)..." && \
	cd apps/desktop && npm run dev

desktop-build:
	@export PATH="$$HOME/.cargo/bin:$$PATH" && \
	cargo --version > /dev/null 2>&1 || \
	  (echo "" && echo "❌  Rust / Cargo not found." && \
	   echo "    Run:  make desktop-rust" && echo "" && exit 1) && \
	cd apps/desktop && npm run build

desktop-package:
	@bash scripts/package.sh

desktop-open:
	@open /Applications/Minoverse.app 2>/dev/null || \
	  (echo "Minoverse.app not found in /Applications/ — run 'make desktop-package' first")

# ── Quality ──────────────────────────────────────────────────────────────────

test:
	@cd apps/api && uv run pytest src/ -v
	@cd apps/web && npm test

lint:
	@cd apps/api && uv run ruff check src/ && uv run mypy src/

# ── AutoIngest CLI ────────────────────────────────────────────────────────────

.PHONY: bun-install
bun-install:
	@if ! command -v bun >/dev/null 2>&1; then \
		echo "Installing Bun..."; \
		curl -fsSL https://bun.sh/install | bash; \
		export BUN_INSTALL="$$HOME/.bun"; \
		export PATH="$$BUN_INSTALL/bin:$$PATH"; \
	else \
		echo "Bun already installed: $$(bun --version)"; \
	fi

ingest-install: bun-install
	@echo "Installing AutoIngest CLI dependencies..."
	@export PATH="$$HOME/.bun/bin:$$PATH" && cd apps/autoingest && bun install
	@chmod +x apps/autoingest/bin/autoingest
	@ln -sf $$(pwd)/apps/autoingest/bin/autoingest $$HOME/.bun/bin/autoingest
	@echo "✓ autoingest installed globally — run: autoingest"
	@echo "  (Ensure ~/.bun/bin is in PATH — add to ~/.zshrc if needed)"

ingest-dev:
	@export PATH="$$HOME/.bun/bin:$$PATH" && cd apps/autoingest && bun run src/index.ts

# Shortcuts: make ingest URL=https://example.com
ingest:
	@export PATH="$$HOME/.bun/bin:$$PATH" && cd apps/autoingest && bun run src/index.ts analyze "$(URL)"

# make research TOPIC="RAG architectures"
research-topic:
	@export PATH="$$HOME/.bun/bin:$$PATH" && cd apps/autoingest && bun run src/index.ts research "$(TOPIC)"

ingest-health:
	@export PATH="$$HOME/.bun/bin:$$PATH" && cd apps/autoingest && bun run src/index.ts health

ingest-tools:
	@export PATH="$$HOME/.bun/bin:$$PATH" && cd apps/autoingest && bun run src/index.ts tools

ingest-memory:
	@export PATH="$$HOME/.bun/bin:$$PATH" && cd apps/autoingest && bun run src/index.ts memory list

# ── Telegram Bot ──────────────────────────────────────────────────────────────

telegram-install:
	@echo "Installing Telegram bot dependencies..."
	@cd apps/telegram && uv sync

telegram:
	@cd apps/telegram && uv run python -m src.main

telegram-dev: telegram

# ── Scraping Service ──────────────────────────────────────────────────────────

scraping-install:
	@echo "Installing scraping service dependencies..."
	@cd services/scraping && uv sync

scraping:
	@cd services/scraping && uv run uvicorn src.main:app --host 0.0.0.0 --port 8001 --reload

scraping-dev: scraping

# ── Docker ────────────────────────────────────────────────────────────────────

docker-up:
	@cd infra && docker compose up -d

docker-down:
	@cd infra && docker compose down

docker-up-telegram:
	@cd infra && docker compose --profile telegram up -d

docker-logs:
	@cd infra && docker compose logs -f

# ── Help ─────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "  Minoverse — available make targets"
	@echo ""
	@echo "  Lifecycle:"
	@echo "    make start       Start everything (infra + API + watcher)"
	@echo "    make stop        Stop everything"
	@echo "    make restart     Stop then start"
	@echo "    make status      Show what is running"
	@echo ""
	@echo "  Logs:"
	@echo "    make logs-api    Tail API server log"
	@echo "    make logs-watch  Tail vault watcher log"
	@echo "    make logs-worker Tail enrichment worker log"
	@echo ""
	@echo "  Operations:"
	@echo "    make index       Re-index vault manually"
	@echo "    make migrate     Apply pending DB migrations"
	@echo "    make worker      Run Dramatiq worker (enrichment + graph)"
	@echo "    make graph       Run graph CLI command"
	@echo ""
	@echo "  AutoIngest CLI (apps/autoingest):"
	@echo "    make ingest-install       Install CLI deps (bun install)"
	@echo "    make ingest URL=<url>     Analyze a URL"
	@echo "    make research-topic TOPIC=<t>  Research a topic"
	@echo "    make ingest-health        Check API health"
	@echo "    make ingest-tools         List all available tools"
	@echo "    make ingest-memory        List recent knowledge entries"
	@echo "    Direct: cd apps/autoingest && bun run src/index.ts --help"
	@echo ""
	@echo "  Telegram Bot (apps/telegram):"
	@echo "    make telegram-install     Install bot deps"
	@echo "    make telegram             Start bot in polling mode"
	@echo ""
	@echo "  Scraping Service (services/scraping):"
	@echo "    make scraping-install     Install deps"
	@echo "    make scraping             Run scraping service on :8001"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-up            Start all services via Docker Compose"
	@echo "    make docker-down          Stop all Docker services"
	@echo "    make docker-up-telegram   Start + Telegram bot"
	@echo ""
	@echo "  Phase 4 Knowledge Graph:"
	@echo "    API:  GET /graph/full            — full knowledge graph"
	@echo "    API:  GET /graph/resource/:id    — per-resource graph"
	@echo "    API:  GET /graph/entities        — list concept entities"
	@echo "    UI:   http://localhost:3000/graph — interactive graph view"
	@echo ""
	@echo "  Phase 5 AI Copilot + Memory:"
	@echo "    make copilot     Open AI copilot UI"
	@echo "    make memory      Open memory browser UI"
	@echo "    API:  POST /copilot/ask          — ask vault a question"
	@echo "    API:  GET  /copilot/sessions     — list sessions"
	@echo "    API:  POST /memory/extract/:id   — extract semantic memory"
	@echo "    UI:   http://localhost:3000/copilot — AI copilot chat"
	@echo "    UI:   http://localhost:3000/memory  — memory browser"
	@echo ""
	@echo "  Phase 6 Sync & Desktop:"
	@echo "    make sync            Open sync event log UI"
	@echo "    make desktop-install Install Tauri desktop npm deps"
	@echo "    make desktop-rust    Install Rust toolchain (required for Tauri)"
	@echo "    make desktop-dev     Run Tauri desktop in dev mode (requires Rust)"
	@echo "    make desktop-build   Build production desktop binary (requires Rust)"
	@echo "    make desktop-package Build + install Minoverse.app to /Applications/"
	@echo "    make desktop-open    Open Minoverse.app from /Applications/"
	@echo "    API:  GET  /sync/events    — paginated event log"
	@echo "    API:  POST /sync/emit      — emit a sync event"
	@echo "    API:  POST /sync/replay    — replay unapplied events"
	@echo "    UI:   http://localhost:3000/sync — sync event log"
	@echo ""
	@echo "  Quality:"
	@echo "    make test        Run all tests"
	@echo "    make lint        Run ruff + mypy"
	@echo ""
	@echo "  Web UI:"
	@echo "    make web-install Install web dependencies"
	@echo "    make web-dev     Run web dev server"
	@echo "    make web-build   Build web for production"
	@echo "    make web-test    Run web tests"
	@echo "    make logs-web    Tail web server log"
	@echo ""
