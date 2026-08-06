from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .open_source_registry import OpenSourceAsset, OpenSourceRegistryError


class GitHubRegistryError(OpenSourceRegistryError):
    """Raised when GitHub cannot provide trustworthy registry evidence."""


@dataclass(frozen=True)
class GitHubRepositoryEvidence:
    repository: str
    repository_url: str
    homepage_url: str
    description: str
    default_branch: str
    source_commit: str
    license_spdx: str
    stars: int
    open_issues: int
    pushed_at: str
    days_since_push: int
    latest_release: str
    archived: bool
    disabled: bool
    fork: bool
    observed_at: str

    def payload(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "repository_url": self.repository_url,
            "homepage_url": self.homepage_url,
            "description": self.description,
            "default_branch": self.default_branch,
            "source_commit": self.source_commit,
            "license_spdx": self.license_spdx,
            "stars": self.stars,
            "open_issues": self.open_issues,
            "pushed_at": self.pushed_at,
            "days_since_push": self.days_since_push,
            "latest_release": self.latest_release,
            "archived": self.archived,
            "disabled": self.disabled,
            "fork": self.fork,
            "observed_at": self.observed_at,
        }


class GitHubTransport(Protocol):
    def get_json(self, path: str) -> Mapping[str, object]: ...


class GitHubApiTransport:
    def __init__(self, token: str | None = None, timeout_seconds: float = 15.0) -> None:
        self.token = (token or os.getenv("GITHUB_TOKEN", "")).strip()
        self.timeout_seconds = timeout_seconds

    def get_json(self, path: str) -> Mapping[str, object]:
        if not path.startswith("/"):
            raise GitHubRegistryError("GitHub API path must be absolute")
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "RUOS-OpenSourceRegistry/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(f"https://api.github.com{path}", headers=headers, method="GET")
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read(2_000_001)
                if len(body) > 2_000_000:
                    raise GitHubRegistryError("GitHub response exceeds 2000000 bytes")
                raw = json.loads(body.decode("utf-8"))
        except HTTPError as exc:
            raise GitHubRegistryError(f"GitHub API returned HTTP {exc.code} for {path}") from exc
        except URLError as exc:
            raise GitHubRegistryError(f"GitHub API request failed for {path}: {exc.reason}") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubRegistryError("GitHub API returned invalid JSON") from exc
        if not isinstance(raw, Mapping):
            raise GitHubRegistryError("GitHub API response root must be an object")
        return raw


def _timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise GitHubRegistryError(f"GitHub {field} timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise GitHubRegistryError(f"GitHub {field} timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def _repository_name(value: str) -> str:
    clean = value.strip().strip("/")
    parts = clean.split("/")
    if len(parts) != 2 or not all(parts):
        raise GitHubRegistryError("Repository must use owner/name format")
    if any(part in {".", ".."} for part in parts):
        raise GitHubRegistryError("Repository owner and name are invalid")
    return clean


class GitHubRegistryAdapter:
    def __init__(
        self,
        transport: GitHubTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.transport = transport or GitHubApiTransport()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def inspect(self, repository: str) -> GitHubRepositoryEvidence:
        full_name = _repository_name(repository)
        encoded = "/".join(quote(part, safe="") for part in full_name.split("/"))
        repo = self.transport.get_json(f"/repos/{encoded}")
        branch = str(repo.get("default_branch", "")).strip()
        if not branch:
            raise GitHubRegistryError("GitHub repository has no default branch")
        commit = self.transport.get_json(f"/repos/{encoded}/commits/{quote(branch, safe='')}")
        sha = str(commit.get("sha", "")).strip().lower()
        if len(sha) < 7 or any(ch not in "0123456789abcdef" for ch in sha):
            raise GitHubRegistryError("GitHub default-branch commit SHA is invalid")

        license_data = repo.get("license")
        license_spdx = ""
        if isinstance(license_data, Mapping):
            license_spdx = str(license_data.get("spdx_id", "")).strip()
        if not license_spdx or license_spdx == "NOASSERTION":
            raise GitHubRegistryError("GitHub repository has no approved SPDX license evidence")

        observed = self.clock().astimezone(timezone.utc).replace(microsecond=0)
        pushed_at = str(repo.get("pushed_at", "")).strip()
        pushed = _timestamp(pushed_at, "pushed_at")
        age = observed - pushed
        if age.total_seconds() < 0:
            raise GitHubRegistryError("GitHub repository push timestamp is in the future")

        release = ""
        try:
            release_data = self.transport.get_json(f"/repos/{encoded}/releases/latest")
        except GitHubRegistryError:
            release_data = {}
        if isinstance(release_data, Mapping):
            release = str(release_data.get("tag_name", "")).strip()

        html_url = str(repo.get("html_url", "")).strip()
        if html_url != f"https://github.com/{full_name}":
            raise GitHubRegistryError("GitHub repository URL does not match requested repository")
        if bool(repo.get("archived", False)) or bool(repo.get("disabled", False)):
            raise GitHubRegistryError("Archived or disabled repositories cannot enter the production registry")

        return GitHubRepositoryEvidence(
            repository=full_name,
            repository_url=html_url,
            homepage_url=str(repo.get("homepage", "") or "").strip(),
            description=str(repo.get("description", "") or "").strip(),
            default_branch=branch,
            source_commit=sha,
            license_spdx=license_spdx,
            stars=max(0, int(repo.get("stargazers_count", 0))),
            open_issues=max(0, int(repo.get("open_issues_count", 0))),
            pushed_at=pushed_at,
            days_since_push=int(age.total_seconds() // 86400),
            latest_release=release,
            archived=False,
            disabled=False,
            fork=bool(repo.get("fork", False)),
            observed_at=observed.isoformat().replace("+00:00", "Z"),
        )

    def build_asset(
        self,
        repository: str,
        *,
        asset_id: str,
        name: str,
        category: str,
        package_name: str,
        version: str = "",
        maintenance_score: int,
        documentation_score: int,
        accessibility_score: int,
        performance_score: int,
        rtl_score: int,
        ecosystem_score: int,
        production_score: int,
        capabilities: tuple[str, ...],
        constraints: tuple[str, ...] = (),
    ) -> OpenSourceAsset:
        evidence = self.inspect(repository)
        resolved_version = version.strip() or evidence.latest_release
        return OpenSourceAsset(
            id=asset_id,
            name=name,
            category=category,
            repository_url=evidence.repository_url,
            homepage_url=evidence.homepage_url,
            package_name=package_name,
            license_spdx=evidence.license_spdx,
            version=resolved_version,
            source_commit=evidence.source_commit,
            observed_at=evidence.observed_at,
            stars=evidence.stars,
            open_issues=evidence.open_issues,
            days_since_push=evidence.days_since_push,
            maintenance_score=maintenance_score,
            documentation_score=documentation_score,
            accessibility_score=accessibility_score,
            performance_score=performance_score,
            rtl_score=rtl_score,
            ecosystem_score=ecosystem_score,
            production_score=production_score,
            capabilities=capabilities,
            constraints=constraints,
        )
