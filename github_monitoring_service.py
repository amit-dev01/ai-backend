"""
GitHub Technical Velocity & Open Source Signal Service.

Monitors open-source and developer-facing competitor repositories:
  - Release Frequency & Release Cadence
  - Stargazer & Fork Growth Velocity
  - Primary Programming Languages & Tech Stack
  - Issue Resolution & Technical Momentum
"""

import logging
from datetime import datetime, timezone
from typing import Any, Optional
import httpx

from database import get_competitor_by_id

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com/repos"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CI-Intelligence-Agent/2.0",
    "Accept": "application/vnd.github.v3+json"
}


class GitHubMonitoringService:
    """Monitors technical repository velocity and developer engagement."""

    @staticmethod
    def _parse_repo_slug(github_url: str) -> Optional[tuple[str, str]]:
        """Extracts (owner, repo) from a GitHub URL or string like 'owner/repo'."""
        clean = github_url.strip().rstrip("/")
        if "github.com/" in clean:
            parts = clean.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
        elif "/" in clean and not clean.startswith("http"):
            parts = clean.split("/")
            if len(parts) == 2:
                return parts[0], parts[1]
        return None

    @staticmethod
    async def get_repo_velocity(repo_input: str) -> dict[str, Any]:
        """
        Gathers live technical velocity metrics from a public GitHub repository.
        """
        slug = GitHubMonitoringService._parse_repo_slug(repo_input)
        if not slug:
            return {
                "repo": repo_input,
                "hasPublicRepo": False,
                "status": "INVALID_OR_PRIVATE_REPO",
                "message": f"Could not parse public GitHub repository from '{repo_input}'."
            }

        owner, repo_name = slug
        repo_url = f"{GITHUB_API_BASE}/{owner}/{repo_name}"
        releases_url = f"{repo_url}/releases"
        languages_url = f"{repo_url}/languages"

        try:
            async with httpx.AsyncClient(timeout=10, headers=REQUEST_HEADERS) as client:
                # 1. Fetch Repository Meta
                repo_resp = await client.get(repo_url)
                if repo_resp.status_code == 404:
                    return {
                        "repo": f"{owner}/{repo_name}",
                        "hasPublicRepo": False,
                        "status": "NOT_FOUND",
                        "message": f"Repository '{owner}/{repo_name}' is private or does not exist."
                    }
                elif repo_resp.status_code != 200:
                    return {
                        "repo": f"{owner}/{repo_name}",
                        "hasPublicRepo": False,
                        "status": "API_RATE_LIMITED",
                        "message": f"GitHub API responded with HTTP {repo_resp.status_code}."
                    }

                repo_data = repo_resp.json()

                # 2. Fetch Recent Releases
                releases_resp = await client.get(releases_url, params={"per_page": 5})
                releases_data = releases_resp.json() if releases_resp.status_code == 200 else []

                # 3. Fetch Languages
                lang_resp = await client.get(languages_url)
                lang_data = lang_resp.json() if lang_resp.status_code == 200 else {}

        except Exception as exc:
            logger.warning("GitHub query failed for %s/%s: %s", owner, repo_name, exc)
            return {
                "repo": f"{owner}/{repo_name}",
                "hasPublicRepo": False,
                "status": "NETWORK_ERROR",
                "message": str(exc)
            }

        # Analyze Release Cadence
        recent_releases = []
        for rel in (releases_data if isinstance(releases_data, list) else []):
            recent_releases.append({
                "tag": rel.get("tag_name"),
                "name": rel.get("name") or rel.get("tag_name"),
                "publishedAt": rel.get("published_at"),
                "htmlUrl": rel.get("html_url")
            })

        # Calculate Tech Stack Breakdown
        total_lang_bytes = sum(lang_data.values()) if lang_data else 1
        top_languages = [
            {"language": lang, "percentage": round((b / total_lang_bytes) * 100.0, 1)}
            for lang, b in sorted(lang_data.items(), key=lambda x: x[1], reverse=True)[:4]
        ]

        stars = repo_data.get("stargazers_count", 0)
        forks = repo_data.get("forks_count", 0)
        open_issues = repo_data.get("open_issues_count", 0)
        updated_at = repo_data.get("pushed_at") or repo_data.get("updated_at")

        # Classify Technical Velocity
        if len(recent_releases) >= 3 or stars > 5000:
            velocity_status = "HYPER_ACTIVE_DEVELOPMENT"
        elif len(recent_releases) >= 1 or stars > 500:
            velocity_status = "HEALTHY_STEADY_CADENCE"
        else:
            velocity_status = "LOW_COMMUNITY_VELOCITY"

        return {
            "repo": f"{owner}/{repo_name}",
            "hasPublicRepo": True,
            "stars": stars,
            "forks": forks,
            "openIssues": open_issues,
            "lastPushedAt": updated_at,
            "velocityClassification": velocity_status,
            "recentReleases": recent_releases,
            "techStack": top_languages,
            "summary": (
                f"Repository '{owner}/{repo_name}' has {stars:,} stars and {len(recent_releases)} recent releases. "
                f"Primary language: {top_languages[0]['language'] if top_languages else 'N/A'}. "
                f"Velocity status: {velocity_status}."
            )
        }

    @staticmethod
    async def get_competitor_github_signals(competitor_id: str) -> dict[str, Any]:
        """
        Inspects competitor website/name and derives technical GitHub velocity.
        """
        competitor = get_competitor_by_id(competitor_id) or {}
        comp_name = competitor.get("name", "Competitor")
        website = competitor.get("website_url", "")

        # Guess probable repo slug or check website domain
        clean_name = comp_name.lower().replace(" ", "").replace("-", "")
        # Common pattern: organization/product or company/company
        candidate_slug = f"{clean_name}/{clean_name}"

        return await GitHubMonitoringService.get_repo_velocity(candidate_slug)
