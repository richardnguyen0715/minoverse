"""GitHub scraper adapter.

Uses the GitHub REST API to extract repository metadata, README, and activity.
Supports both authenticated (with GITHUB_TOKEN) and unauthenticated requests.
"""
from __future__ import annotations

import base64
import re

import httpx
import structlog

from ..config import settings
from ..schemas import NormalizedDocument, SourceType
from .base import BaseScraper

logger = structlog.get_logger(__name__)

GITHUB_API = "https://api.github.com"
REPO_PATTERN = re.compile(r"github\.com/([^/]+)/([^/?\s]+)")


class GitHubScraper(BaseScraper):
    """Extracts README, stars, issues, and commit activity from GitHub repos."""

    @property
    def name(self) -> str:
        return "github"

    def can_handle(self, url: str) -> bool:
        return bool(REPO_PATTERN.search(url))

    async def scrape(self, url: str) -> NormalizedDocument:
        match = REPO_PATTERN.search(url)
        if not match:
            raise ValueError(f"Cannot parse GitHub URL: {url}")

        owner, repo = match.group(1), match.group(2).rstrip("/")
        repo = repo.split("/")[0]  # strip any sub-path

        logger.info("scraping_github", owner=owner, repo=repo)

        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        async with httpx.AsyncClient(timeout=15) as client:
            repo_data, readme = await self._fetch_repo(client, owner, repo, headers)
            topics = await self._fetch_topics(client, owner, repo, headers)

        content = self._build_content(repo_data, readme)

        return NormalizedDocument(
            source_url=url,
            source_type=SourceType.GITHUB,
            canonical_url=f"https://github.com/{owner}/{repo}",
            title=f"{owner}/{repo}",
            author=owner,
            content=content,
            tags=topics[:15],
            metadata={
                "owner": owner,
                "repo": repo,
                "full_name": repo_data.get("full_name"),
                "description": repo_data.get("description"),
                "stars": repo_data.get("stargazers_count"),
                "forks": repo_data.get("forks_count"),
                "watchers": repo_data.get("watchers_count"),
                "open_issues": repo_data.get("open_issues_count"),
                "language": repo_data.get("language"),
                "license": (repo_data.get("license") or {}).get("spdx_id"),
                "created_at": repo_data.get("created_at"),
                "updated_at": repo_data.get("updated_at"),
                "pushed_at": repo_data.get("pushed_at"),
                "topics": topics,
                "has_readme": bool(readme),
                "archived": repo_data.get("archived", False),
            },
        )

    async def _fetch_repo(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        headers: dict[str, str],
    ) -> tuple[dict, str]:  # type: ignore[type-arg]
        repo_res = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=headers)
        repo_data: dict = {}  # type: ignore[type-arg]
        if repo_res.status_code == 200:
            repo_data = repo_res.json()

        # Fetch README
        readme = ""
        readme_res = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/readme", headers=headers
        )
        if readme_res.status_code == 200:
            readme_json = readme_res.json()
            if readme_json.get("encoding") == "base64" and readme_json.get("content"):
                try:
                    readme = base64.b64decode(readme_json["content"]).decode("utf-8", errors="replace")
                    readme = readme[:8000]  # cap at 8K chars
                except Exception:
                    pass

        return repo_data, readme

    async def _fetch_topics(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        headers: dict[str, str],
    ) -> list[str]:
        topics_res = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/topics",
            headers={**headers, "Accept": "application/vnd.github.mercy-preview+json"},
        )
        if topics_res.status_code == 200:
            return topics_res.json().get("names", [])
        return []

    def _build_content(self, repo_data: dict, readme: str) -> str:  # type: ignore[type-arg]
        parts: list[str] = []

        if repo_data.get("description"):
            parts.append(f"Description: {repo_data['description']}")

        if repo_data.get("language"):
            parts.append(f"Primary language: {repo_data['language']}")

        stars = repo_data.get("stargazers_count")
        if stars is not None:
            parts.append(f"Stars: {stars:,}")

        if readme:
            parts.append("\n---\n")
            parts.append(readme)

        return "\n".join(parts) if parts else f"GitHub repository: {repo_data.get('full_name', '')}"
