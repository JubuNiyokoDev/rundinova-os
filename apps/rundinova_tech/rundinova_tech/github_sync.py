"""Read-only GitHub integration for RundiNova Repository records.

Public repositories work without credentials. A token supplied through the
RUNDINOVA_GITHUB_TOKEN environment variable enables the same GET-only sync for
private repositories. This module never writes to GitHub.
"""

import os
import re

import requests

GITHUB_API_BASE = "https://api.github.com"
TIMEOUT_SECONDS = 15
API_VERSION = "2026-03-10"
GITHUB_URL = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?$")


def parse_github_url(url):
    """Extract (owner, repo) from a GitHub URL. Returns None if invalid."""
    match = GITHUB_URL.match((url or "").strip())
    if not match:
        return None
    return match.group(1), match.group(2)


def _api_headers():
    """Build request headers without exposing credentials in sync results."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RundiNova-OS",
        "X-GitHub-Api-Version": API_VERSION,
    }
    token = os.environ.get("RUNDINOVA_GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_repository_info(owner, repo):
    """GET /repos/{owner}/{repo} - returns parsed dict or raises on error."""
    response = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
        headers=_api_headers(),
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "full_name": data.get("full_name", ""),
        "description": data.get("description") or "",
        "default_branch": data.get("default_branch", "main"),
        "open_issues_count": data.get("open_issues_count", 0),
        "watchers_count": data.get("watchers_count", 0),
        "stargazers_count": data.get("stargazers_count", 0),
        "forks_count": data.get("forks_count", 0),
        "language": data.get("language") or "",
        "pushed_at": data.get("pushed_at") or "",
        "html_url": data.get("html_url", ""),
    }


def fetch_recent_commits(owner, repo, limit=5):
    """GET /repos/{owner}/{repo}/commits - returns a list of recent commit summaries."""
    response = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits",
        params={"per_page": limit},
        headers=_api_headers(),
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    commits = []
    for item in response.json():
        commit = item.get("commit", {})
        commits.append(
            {
                "sha": item.get("sha", "")[:8],
                "message": (commit.get("message") or "").split("\n")[0][:120],
                "author": (commit.get("author") or {}).get("name", ""),
                "date": (commit.get("author") or {}).get("date", ""),
            }
        )
    return commits


def sync_repository(github_url):
    """Fetch live metadata for a repository URL. Returns a summary dict.

    Raises ValueError for invalid URLs and requests.HTTPError for API failures.
    """
    parsed = parse_github_url(github_url)
    if not parsed:
        raise ValueError(f"Invalid GitHub URL: {github_url}")
    owner, repo = parsed
    info = fetch_repository_info(owner, repo)
    commits = fetch_recent_commits(owner, repo, limit=5)
    return {**info, "recent_commits": commits, "owner": owner, "repo": repo}
