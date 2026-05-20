"""
Centralized GitHub URL parsing.

Supports repository URLs, file/tree/blob paths, .git suffix, trailing slashes,
query parameters, and owner/repo shorthand. Distinguishes repository vs file analytics mode.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional, Tuple
from urllib.parse import urlparse, unquote

from utils.exceptions import InvalidURLError

Mode = Literal["repository", "file"]

_RESERVED_PATH_SEGMENTS = frozenset({
    "tree", "blob", "pull", "issues", "releases", "projects", "actions",
    "security", "pulse", "graphs", "wiki", "settings", "discussions", "raw",
})
_INVALID_OWNERS = frozenset({
    "settings", "explore", "trending", "features", "marketplace",
    "notifications", "search", "login", "signup", "orgs", "organizations",
})


@dataclass(frozen=True)
class ParsedGitHubURL:
    owner: str
    repo: str
    mode: Mode
    repo_url: str
    branch: Optional[str] = None
    file_path: Optional[str] = None


def parse_github_url(url: str) -> ParsedGitHubURL:
    """
    Parse any supported GitHub URL into structured components.

    Raises InvalidURLError for malformed input.
    """
    if not url or not str(url).strip():
        raise InvalidURLError(internal_details="Empty URL")

    raw = str(url).strip()
    if "#" in raw:
        raw = raw.split("#", 1)[0]
    if "?" in raw:
        raw = raw.split("?", 1)[0]
    raw = raw.rstrip("/")

    if raw.lower().endswith(".git"):
        raw = raw[:-4].rstrip("/")

    # owner/repo shorthand
    if not raw.startswith("http://") and not raw.startswith("https://"):
        if "github.com" not in raw.lower():
            parts = [p for p in raw.split("/") if p]
            if len(parts) < 2:
                raise InvalidURLError(url=raw, internal_details="Need owner/repo")
            raw = f"https://github.com/{parts[0]}/{parts[1]}"
            if len(parts) > 2:
                raw += "/" + "/".join(parts[2:])

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.netloc or "").lower().replace("www.", "")
    if host != "github.com":
        raise InvalidURLError(url=raw, internal_details=f"Unsupported host: {host}")

    path = unquote(parsed.path or "").strip("/")
    segments = [s for s in path.split("/") if s]
    if len(segments) < 2:
        raise InvalidURLError(url=raw, internal_details="Missing owner/repo")

    owner, repo = segments[0], segments[1]
    _validate_owner_repo(owner, repo)

    mode: Mode = "repository"
    branch: Optional[str] = None
    file_path: Optional[str] = None

    if len(segments) > 2:
        kind = segments[2].lower()
        if kind in ("blob", "raw"):
            mode = "file"
            if len(segments) < 4:
                raise InvalidURLError(
                    url=raw,
                    internal_details="File URL must include branch and path",
                )
            branch = segments[3]
            file_path = "/".join(segments[4:])
            if not file_path:
                raise InvalidURLError(url=raw, internal_details="File path missing")
        elif kind == "tree":
            if len(segments) >= 4:
                branch = segments[3]
                rest = "/".join(segments[4:])
                if rest:
                    mode = "file"
                    file_path = rest
        elif kind in _RESERVED_PATH_SEGMENTS and kind not in ("tree", "blob", "raw"):
            pass  # repo landing pages — ignore extra segments

    repo_url = f"https://github.com/{owner}/{repo}"
    return ParsedGitHubURL(
        owner=owner,
        repo=repo,
        mode=mode,
        repo_url=repo_url,
        branch=branch,
        file_path=file_path,
    )


def normalize_github_url(url: str) -> str:
    """Return canonical repository URL (https://github.com/owner/repo)."""
    return parse_github_url(url).repo_url


def parse_github_repo_url(repo_url: str) -> Tuple[str, str]:
    """Return (owner, repo) from any supported GitHub URL."""
    parsed = parse_github_url(repo_url)
    return parsed.owner, parsed.repo


def _validate_owner_repo(owner: str, repo: str) -> None:
    if not owner or not repo or owner.lower() in _INVALID_OWNERS:
        raise InvalidURLError(
            internal_details=f"Invalid owner/repo: {owner}/{repo}",
        )
    if not re.match(r"^[a-zA-Z0-9\-]+$", owner):
        raise InvalidURLError(internal_details=f"Invalid owner: {owner}")
    if not re.match(r"^[a-zA-Z0-9\-._]+$", repo):
        raise InvalidURLError(internal_details=f"Invalid repo: {repo}")
