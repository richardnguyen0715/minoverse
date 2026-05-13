"""Minoverse API client for the Telegram bot."""
from __future__ import annotations

import httpx
import structlog

from .config import settings

logger = structlog.get_logger(__name__)


class MinoverseClient:
    """Typed async client for the Minoverse FastAPI backend."""

    def __init__(self) -> None:
        self.base_url = settings.MINOVERSE_API_URL.rstrip("/")
        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        if settings.MINOVERSE_API_KEY:
            self._headers["Authorization"] = f"Bearer {settings.MINOVERSE_API_KEY}"

    async def ingest(self, url: str, mode: str = "technical") -> dict:  # type: ignore[type-arg]
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                f"{self.base_url}/ingest/url",
                json={"url": url, "mode": mode, "store_memory": True, "update_graph": True},
                headers=self._headers,
            )
            res.raise_for_status()
            return res.json()

    async def stream_ingest(self, url: str, mode: str = "technical"):  # type: ignore[return]
        """Yield SSE events from the streaming ingest endpoint."""
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/ingest/url/stream",
                json={"url": url, "mode": mode, "store_memory": True, "update_graph": True},
                headers={**self._headers, "Accept": "text/event-stream"},
            ) as res:
                res.raise_for_status()
                async for line in res.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            return
                        import json
                        try:
                            yield json.loads(data)
                        except Exception:
                            pass

    async def research(self, topic: str, depth: str = "deep") -> dict:  # type: ignore[type-arg]
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(
                f"{self.base_url}/research/search",
                json={"query": topic},
                headers=self._headers,
            )
            res.raise_for_status()
            return res.json()

    async def query_memory(self, query: str, limit: int = 5) -> dict:  # type: ignore[type-arg]
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                f"{self.base_url}/memory/query",
                json={"query": query, "limit": limit},
                headers=self._headers,
            )
            res.raise_for_status()
            return res.json()

    async def graph_context(self, entity: str) -> dict:  # type: ignore[type-arg]
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.get(
                f"{self.base_url}/graph/context",
                params={"entity": entity},
                headers=self._headers,
            )
            res.raise_for_status()
            return res.json()

    async def health(self) -> dict:  # type: ignore[type-arg]
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(f"{self.base_url}/health")
            res.raise_for_status()
            return res.json()


api = MinoverseClient()
