"""Scraping service — FastAPI application."""
from __future__ import annotations

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .router import scrape
from .schemas import NormalizedDocument

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="Minoverse Scraping Service",
    description="Multi-source content extraction API",
    version="0.1.0",
)


class ScrapeRequest(BaseModel):
    url: str
    include_comments: bool = False


class ArticleRequest(BaseModel):
    url: str
    include_comments: bool = False


class VideoRequest(BaseModel):
    url: str
    include_transcript: bool = True
    include_comments: bool = False


class RepoRequest(BaseModel):
    url: str
    include_issues: bool = False
    include_commits: bool = False


@app.get("/health")
async def health() -> dict:  # type: ignore[type-arg]
    return {"status": "ok", "service": "scraping"}


@app.post("/scrape", response_model=NormalizedDocument)
async def scrape_url(req: ScrapeRequest) -> NormalizedDocument:
    """Scrape any URL — auto-detects source type."""
    try:
        doc = await scrape(req.url)
        return doc
    except Exception as e:
        logger.error("scrape_failed", url=req.url, error=str(e))
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/scrape/article", response_model=NormalizedDocument)
async def scrape_article(req: ArticleRequest) -> NormalizedDocument:
    """Extract article content from a web page."""
    from .adapters.generic import GenericScraper
    try:
        doc = await GenericScraper().scrape(req.url)
        return doc
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/scrape/video", response_model=NormalizedDocument)
async def scrape_video(req: VideoRequest) -> NormalizedDocument:
    """Extract YouTube video info and transcript."""
    from .adapters.youtube import YouTubeScraper
    try:
        doc = await YouTubeScraper().scrape(req.url)
        return doc
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@app.post("/scrape/repo", response_model=NormalizedDocument)
async def scrape_repo(req: RepoRequest) -> NormalizedDocument:
    """Extract GitHub repository metadata and README."""
    from .adapters.github import GitHubScraper
    try:
        doc = await GitHubScraper().scrape(req.url)
        return doc
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
