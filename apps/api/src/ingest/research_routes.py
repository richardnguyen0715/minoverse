"""Research routes — web search, GitHub repo discovery, entity extraction."""
from __future__ import annotations

import structlog
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    sources: list[str] = []


class FindRepoRequest(BaseModel):
    query: str
    topic: str | None = None
    language: str | None = None
    min_stars: int = 100
    limit: int = 5


class SearchResult(BaseModel):
    title: str | None
    url: str
    snippet: str | None
    source: str
    score: float | None = None


@router.post("/search")
async def search_web(req: SearchRequest) -> dict:  # type: ignore[type-arg]
    """Multi-source web search (HackerNews + DuckDuckGo fallback)."""
    results: list[dict] = []  # type: ignore[type-arg]

    # HackerNews via Algolia
    if not req.sources or "hackernews" in req.sources or "hn" in req.sources:
        hn_results = await _search_hackernews(req.query, req.limit)
        results.extend(hn_results)

    # GitHub search
    if not req.sources or "github" in req.sources:
        gh_results = await _search_github_repos(req.query, limit=min(req.limit, 5))
        results.extend(gh_results)

    return {"results": results[:req.limit], "total": len(results)}


@router.post("/find-repo")
async def find_repo(req: FindRepoRequest) -> dict:  # type: ignore[type-arg]
    """Search GitHub for matching repositories."""
    results = await _search_github_repos(
        query=req.query,
        topic=req.topic,
        language=req.language,
        min_stars=req.min_stars,
        limit=req.limit,
    )
    return {"results": results, "total": len(results)}


async def _search_hackernews(query: str, limit: int = 10) -> list[dict]:  # type: ignore[type-arg]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={"query": query, "hitsPerPage": limit},
            )
            if res.status_code == 200:
                data = res.json()
                return [
                    {
                        "title": h.get("title"),
                        "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                        "snippet": (h.get("story_text") or "")[:300],
                        "source": "hackernews",
                        "score": h.get("points"),
                    }
                    for h in data.get("hits", [])
                ]
    except Exception as e:
        logger.warning("hn_search_failed", error=str(e))
    return []


async def _search_github_repos(
    query: str,
    topic: str | None = None,
    language: str | None = None,
    min_stars: int = 0,
    limit: int = 5,
) -> list[dict]:  # type: ignore[type-arg]
    try:
        q = query
        if topic:
            q += f" topic:{topic}"
        if language:
            q += f" language:{language}"
        if min_stars:
            q += f" stars:>={min_stars}"

        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": q, "sort": "stars", "order": "desc", "per_page": limit},
                headers={"Accept": "application/vnd.github+json"},
            )
            if res.status_code == 200:
                data = res.json()
                return [
                    {
                        "title": item.get("full_name"),
                        "url": item.get("html_url"),
                        "snippet": item.get("description") or "",
                        "source": "github",
                        "stars": item.get("stargazers_count"),
                        "language": item.get("language"),
                        "topics": item.get("topics", []),
                    }
                    for item in data.get("items", [])
                ]
    except Exception as e:
        logger.warning("github_search_failed", error=str(e))
    return []
