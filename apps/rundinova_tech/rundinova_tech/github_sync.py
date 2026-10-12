"""Read-only GitHub integration for RundiNova Repository records.

Public repositories work without credentials. A token supplied through the
RUNDINOVA_GITHUB_TOKEN environment variable enables the same GET-only sync for
private repositories. This module never writes to GitHub.
"""

import base64
import json
import os
import re
import time

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


def _api_headers(owner):
    """Build request headers without exposing credentials in sync results."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "RundiNova-OS",
        "X-GitHub-Api-Version": API_VERSION,
    }
    token = _github_access_token(owner)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _github_access_token(owner):
    """Return a centrally configured token for the repository owner.

    GitHub App credentials are preferred because they mint short-lived tokens
    for the repositories granted to the installation. A fine-grained PAT stays
    available as a migration path for existing self-hosted deployments.
    """
    app_id = os.environ.get("RUNDINOVA_GITHUB_APP_ID", "").strip()
    installation_id = os.environ.get("RUNDINOVA_GITHUB_INSTALLATION_ID", "").strip()
    installations_json = os.environ.get("RUNDINOVA_GITHUB_INSTALLATIONS_JSON", "").strip()
    private_key_b64 = os.environ.get(
        "RUNDINOVA_GITHUB_APP_PRIVATE_KEY_B64", ""
    ).strip()
    if installations_json:
        try:
            installations = json.loads(installations_json)
        except (TypeError, ValueError) as exc:
            raise RuntimeError("GitHub App installations must be a JSON object.") from exc
        if not isinstance(installations, dict):
            raise RuntimeError("GitHub App installations must be a JSON object.")
        installation_id = str(installations.get(owner, "")).strip()
        if not installation_id:
            raise RuntimeError(f"No GitHub App installation configured for owner {owner}.")
    app_values = (app_id, installation_id, private_key_b64)
    if any(app_values) and not all(app_values):
        raise RuntimeError("GitHub App configuration is incomplete.")
    if app_id and installation_id and private_key_b64:
        return _installation_token(app_id, installation_id, private_key_b64)
    return os.environ.get("RUNDINOVA_GITHUB_TOKEN", "").strip()


def _installation_token(app_id, installation_id, private_key_b64):
    """Mint/cache an installation token; its secret never leaves this module."""
    cache = None
    cache_key = f"rundinova:github:installation-token:{installation_id}"
    try:
        import frappe

        if getattr(frappe.local, "site", None):
            cache = frappe.cache()
            cached = cache.get_value(cache_key)
            if cached:
                return cached
    except Exception:
        cache = None

    try:
        import jwt

        private_key = base64.b64decode(private_key_b64, validate=True).decode("utf-8")
        now = int(time.time())
        app_jwt = jwt.encode(
            {"iat": now - 30, "exp": now + 540, "iss": app_id},
            private_key,
            algorithm="RS256",
        )
        response = requests.post(
            f"{GITHUB_API_BASE}/app/installations/{installation_id}/access_tokens",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {app_jwt}",
                "User-Agent": "RundiNova-OS",
                "X-GitHub-Api-Version": API_VERSION,
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        token = response.json()["token"]
        if cache:
            cache.set_value(cache_key, token, expires_in_sec=50 * 60)
        return token
    except Exception as exc:
        raise RuntimeError(
            "GitHub App authentication failed; check its installation settings."
        ) from exc


def fetch_repository_info(owner, repo):
    """GET /repos/{owner}/{repo} - returns parsed dict or raises on error."""
    response = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
        headers=_api_headers(owner),
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
        headers=_api_headers(owner),
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
