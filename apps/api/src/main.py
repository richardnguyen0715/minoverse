"""FastAPI application factory for minoverse API."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.core.config import settings
from src.core.logging import configure_logging
from src.enrichment.routes import router as enrichment_router
from src.graph.routes import router as graph_router
from src.ingest.routes import router as ingest_router
from src.ingest.research_routes import router as research_router
from src.knowledge.routes import router as knowledge_router
from src.memory.routes import copilot_router, memory_router
from src.notes.routes import router as notes_router
from src.sync.routes import sync_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle."""
    configure_logging(debug=settings.debug)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title="Minoverse API",
        description="AI-native Personal Knowledge Operating System",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(knowledge_router)
    app.include_router(notes_router)
    app.include_router(enrichment_router)
    app.include_router(graph_router)
    app.include_router(memory_router)
    app.include_router(copilot_router)
    app.include_router(sync_router)
    app.include_router(ingest_router)
    app.include_router(research_router)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root to interactive API docs."""
        return RedirectResponse(url="/docs")

    @app.get("/health", tags=["system"])
    async def health_check() -> dict:  # type: ignore[type-arg]
        """Return API liveness status with component health.

        Used by Docker Compose healthchecks, load balancers, and the AutoIngest CLI.
        """
        import httpx

        components: dict[str, str] = {}

        # Check Redis
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            await r.aclose()
            components["redis"] = "ok"
        except Exception:
            components["redis"] = "error"

        # Check Ollama/AI provider
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                res = await client.get(f"{settings.ollama_base_url}/api/tags")
                components["ollama"] = "ok" if res.status_code == 200 else "error"
        except Exception:
            components["ollama"] = "error"

        all_ok = all(v == "ok" for v in components.values())
        return {
            "status": "ok" if all_ok else "degraded",
            "version": "0.1.0",
            "components": components,
        }

    return app


app = create_app()
