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
from urllib.parse import quote

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
    installations_json = os.environ.get(
        "RUNDINOVA_GITHUB_INSTALLATIONS_JSON", ""
    ).strip()
    private_key_b64 = os.environ.get("RUNDINOVA_GITHUB_APP_PRIVATE_KEY_B64", "").strip()
    if installations_json:
        try:
            installations = json.loads(installations_json)
        except (TypeError, ValueError) as exc:
            raise RuntimeError(
                "GitHub App installations must be a JSON object."
            ) from exc
        if not isinstance(installations, dict):
            raise RuntimeError("GitHub App installations must be a JSON object.")
        installation_id = str(installations.get(owner, "")).strip()
        if not installation_id:
            raise RuntimeError(
                f"No GitHub App installation configured for owner {owner}."
            )
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
    except Exception:  # noqa: BLE001 - GitHub sync remains usable without a working Frappe cache
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


def fetch_installation_repositories(owner):
    """List repositories granted to a GitHub App installation or configured PAT."""
    app_id = os.environ.get("RUNDINOVA_GITHUB_APP_ID", "").strip()
    private_key = os.environ.get("RUNDINOVA_GITHUB_APP_PRIVATE_KEY_B64", "").strip()
    installation_id = os.environ.get("RUNDINOVA_GITHUB_INSTALLATION_ID", "").strip()
    installations = os.environ.get("RUNDINOVA_GITHUB_INSTALLATIONS_JSON", "").strip()
    using_app = bool(app_id and private_key and (installation_id or installations))
    if not _github_access_token(owner):
        raise RuntimeError(
            "Configure a GitHub App installation or a read-only GitHub token first."
        )

    repositories = []
    page = 1
    while True:
        response = requests.get(
            f"{GITHUB_API_BASE}/installation/repositories"
            if using_app
            else f"{GITHUB_API_BASE}/user/repos",
            params=(
                {"per_page": 100, "page": page}
                if using_app
                else {
                    "visibility": "all",
                    "affiliation": "owner,organization_member,collaborator",
                    "per_page": 100,
                    "page": page,
                }
            ),
            headers=_api_headers(owner),
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
        page_repositories = payload.get("repositories", []) if using_app else payload
        repositories.extend(
            {
                "full_name": item.get("full_name", ""),
                "html_url": item.get("html_url", ""),
                "description": item.get("description") or "",
                "default_branch": item.get("default_branch", "main"),
                "private": bool(item.get("private")),
            }
            for item in page_repositories
            if item.get("full_name") and item.get("html_url")
        )
        if len(page_repositories) < 100:
            return repositories
        page += 1


def fetch_repository_source_context(
    owner, repo, branch, max_files=80, max_chars=180_000
):
    """Read bounded text source from the whole tree; never clone or execute it."""
    tree_response = requests.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{quote(branch, safe='')}",
        params={"recursive": 1},
        headers=_api_headers(owner),
        timeout=TIMEOUT_SECONDS,
    )
    tree_response.raise_for_status()
    tree = tree_response.json()
    ignored_dirs = {
        ".git",
        ".next",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "target",
        "vendor",
    }
    text_names = {
        "dockerfile",
        "makefile",
        "readme",
        "readme.md",
        "pyproject.toml",
        "package.json",
        "go.mod",
        "cargo.toml",
        "pubspec.yaml",
    }
    text_extensions = {
        ".c",
        ".cpp",
        ".cs",
        ".dart",
        ".go",
        ".html",
        ".java",
        ".js",
        ".jsx",
        ".md",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".sh",
        ".sql",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
    candidates = []
    for entry in tree.get("tree", []):
        path = entry.get("path", "")
        if entry.get("type") != "blob" or entry.get("size", 0) > 200_000:
            continue
        parts = path.lower().split("/")
        basename = parts[-1]
        if any(part in ignored_dirs for part in parts):
            continue
        if basename.startswith(".env") or any(
            marker in basename for marker in ("secret", "credential", "private_key")
        ):
            continue
        if basename in {
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
        }:
            continue
        if basename not in text_names and not any(
            basename.endswith(extension) for extension in text_extensions
        ):
            continue
        candidates.append(entry)
    candidates.sort(
        key=lambda item: (
            0 if item["path"].lower().split("/")[-1].startswith("readme") else 1,
            0 if item["path"].lower().split("/")[-1] in text_names else 1,
            item["path"],
        )
    )

    files = []
    used_chars = 0
    for entry in candidates[:max_files]:
        response = requests.get(
            entry["url"], headers=_api_headers(owner), timeout=TIMEOUT_SECONDS
        )
        response.raise_for_status()
        blob = response.json()
        if blob.get("encoding") != "base64":
            continue
        content = base64.b64decode(blob.get("content", "")).decode(
            "utf-8", errors="replace"
        )
        remaining = max_chars - used_chars
        if remaining <= 0:
            break
        content = content[:remaining]
        # Do not transmit credentials accidentally committed in source files.
        content = re.sub(
            r"(?im)([A-Z0-9_]*(?:API[_-]?KEY|ACCESS[_-]?TOKEN|CLIENT[_-]?SECRET|"
            r"PASSWORD|DATABASE[_-]?URL|PRIVATE[_-]?KEY|SECRET)[A-Z0-9_]*)"
            r"(\s*[:=]\s*)(['\"]?)[^\s'\"]+",
            r"\1\2\3[REDACTED]",
            content,
        )
        content = re.sub(
            r"(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
            r"AIza[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9]{20,})\b",
            "[REDACTED_TOKEN]",
            content,
        )
        content = re.sub(
            r"(?s)-----BEGIN(?: RSA| EC| OPENSSH)? PRIVATE KEY-----.*?"
            r"-----END(?: RSA| EC| OPENSSH)? PRIVATE KEY-----",
            "[REDACTED_PRIVATE_KEY]",
            content,
        )
        used_chars += len(content)
        files.append({"path": entry["path"], "content": content})
    return {
        "branch": branch,
        "tree_files": len(tree.get("tree", [])),
        "candidate_files": len(candidates),
        "files_read": len(files),
        "truncated": bool(tree.get("truncated"))
        or len(candidates) > max_files
        or used_chars >= max_chars,
        "files": files,
    }


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
