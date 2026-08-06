from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import urlparse


class OpenSourceRegistryError(ValueError):
    """Raised when an open-source asset cannot be trusted or ranked."""


_ALLOWED_CATEGORIES = {
    "animation",
    "accessibility",
    "color",
    "component",
    "design-system",
    "font",
    "icon",
    "performance",
    "qa",
    "scroll",
    "seo",
    "visual-regression",
}
_ALLOWED_LICENSES = {
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "MIT",
    "MPL-2.0",
    "OFL-1.1",
}


def _utc_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OpenSourceRegistryError("Registry timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise OpenSourceRegistryError("Registry timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _public_https_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise OpenSourceRegistryError("Registry URLs must use public HTTPS URLs")
    host = parsed.hostname.lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".localhost"):
        raise OpenSourceRegistryError("Registry URLs cannot target localhost")
    return value


@dataclass(frozen=True)
class OpenSourceAsset:
    id: str
    name: str
    category: str
    repository_url: str
    homepage_url: str
    package_name: str
    license_spdx: str
    version: str
    source_commit: str
    observed_at: str
    stars: int
    open_issues: int
    days_since_push: int
    maintenance_score: int
    documentation_score: int
    accessibility_score: int
    performance_score: int
    rtl_score: int
    ecosystem_score: int
    production_score: int
    capabilities: tuple[str, ...]
    constraints: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id.strip() or not self.name.strip():
            raise OpenSourceRegistryError("Registry assets require id and name")
        if self.category not in _ALLOWED_CATEGORIES:
            raise OpenSourceRegistryError(f"Unsupported registry category: {self.category}")
        _public_https_url(self.repository_url)
        if self.homepage_url:
            _public_https_url(self.homepage_url)
        if self.license_spdx not in _ALLOWED_LICENSES:
            raise OpenSourceRegistryError(f"License is not approved: {self.license_spdx}")
        if len(self.source_commit) < 7 or any(ch not in "0123456789abcdef" for ch in self.source_commit.lower()):
            raise OpenSourceRegistryError("source_commit must be a hexadecimal commit SHA")
        _utc_timestamp(self.observed_at)
        if min(self.stars, self.open_issues, self.days_since_push) < 0:
            raise OpenSourceRegistryError("Registry metrics cannot be negative")
        for score in self.scores.values():
            if not 0 <= score <= 100:
                raise OpenSourceRegistryError("Registry scores must be between 0 and 100")
        if not self.capabilities:
            raise OpenSourceRegistryError("Registry assets require at least one capability")

    @property
    def scores(self) -> dict[str, int]:
        return {
            "maintenance": self.maintenance_score,
            "documentation": self.documentation_score,
            "accessibility": self.accessibility_score,
            "performance": self.performance_score,
            "rtl": self.rtl_score,
            "ecosystem": self.ecosystem_score,
            "production": self.production_score,
        }

    @property
    def composite_score(self) -> int:
        weighted = (
            self.maintenance_score * 18
            + self.documentation_score * 12
            + self.accessibility_score * 15
            + self.performance_score * 15
            + self.rtl_score * 10
            + self.ecosystem_score * 12
            + self.production_score * 18
        )
        return round(weighted / 100)

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "repository_url": self.repository_url,
            "homepage_url": self.homepage_url,
            "package_name": self.package_name,
            "license_spdx": self.license_spdx,
            "version": self.version,
            "source_commit": self.source_commit,
            "observed_at": self.observed_at,
            "metrics": {
                "stars": self.stars,
                "open_issues": self.open_issues,
                "days_since_push": self.days_since_push,
            },
            "scores": {**self.scores, "composite": self.composite_score},
            "capabilities": list(self.capabilities),
            "constraints": list(self.constraints),
        }


@dataclass(frozen=True)
class OpenSourceRegistry:
    assets: tuple[OpenSourceAsset, ...]

    @classmethod
    def build(cls, assets: Iterable[OpenSourceAsset]) -> "OpenSourceRegistry":
        ordered = tuple(sorted(assets, key=lambda item: item.id))
        ids = [asset.id for asset in ordered]
        if len(ids) != len(set(ids)):
            raise OpenSourceRegistryError("Open-source registry contains duplicate ids")
        repos = [asset.repository_url.rstrip("/").lower() for asset in ordered]
        if len(repos) != len(set(repos)):
            raise OpenSourceRegistryError("Open-source registry contains duplicate repositories")
        return cls(ordered)

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "asset_count": len(self.assets),
            "assets": [asset.payload() for asset in self.assets],
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def ranked(
        self,
        category: str,
        *,
        minimum_score: int = 0,
        required_capabilities: tuple[str, ...] = (),
    ) -> tuple[OpenSourceAsset, ...]:
        if category not in _ALLOWED_CATEGORIES:
            raise OpenSourceRegistryError(f"Unsupported registry category: {category}")
        required = {item.strip().casefold() for item in required_capabilities if item.strip()}
        matches = []
        for asset in self.assets:
            capabilities = {item.casefold() for item in asset.capabilities}
            if asset.category != category:
                continue
            if asset.composite_score < minimum_score or asset.production_score < minimum_score:
                continue
            if not required.issubset(capabilities):
                continue
            matches.append(asset)
        return tuple(sorted(matches, key=lambda item: (-item.composite_score, item.id)))

    def require(self, asset_id: str) -> OpenSourceAsset:
        for asset in self.assets:
            if asset.id == asset_id:
                return asset
        raise KeyError(asset_id)
