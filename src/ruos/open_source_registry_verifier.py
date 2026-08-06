from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .open_source_registry import OpenSourceRegistry, OpenSourceRegistryError


_REQUIRED_PRODUCTION_CATEGORIES = (
    "accessibility",
    "animation",
    "component",
    "font",
    "icon",
    "qa",
)


@dataclass(frozen=True)
class VerifiedOpenSourceRegistry:
    snapshot_sha256: str
    asset_count: int
    categories: tuple[str, ...]
    freshest_age_hours: int
    oldest_age_hours: int

    def payload(self) -> dict[str, object]:
        return {
            "status": "verified-open-source-registry",
            "snapshot_sha256": self.snapshot_sha256,
            "asset_count": self.asset_count,
            "categories": list(self.categories),
            "freshest_age_hours": self.freshest_age_hours,
            "oldest_age_hours": self.oldest_age_hours,
        }


def verify_open_source_registry(
    registry: OpenSourceRegistry,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(days=14),
    minimum_assets: int = 8,
    required_categories: tuple[str, ...] = _REQUIRED_PRODUCTION_CATEGORIES,
    minimum_production_score: int = 80,
) -> VerifiedOpenSourceRegistry:
    if len(registry.assets) < minimum_assets:
        raise OpenSourceRegistryError(
            f"Open-source registry has {len(registry.assets)} assets; minimum is {minimum_assets}"
        )
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    ages: list[timedelta] = []
    eligible_categories: set[str] = set()
    for asset in registry.assets:
        try:
            observed = datetime.fromisoformat(asset.observed_at.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError as exc:
            raise OpenSourceRegistryError(f"Registry asset {asset.id} has an invalid observation time") from exc
        age = current - observed
        if age < timedelta(0):
            raise OpenSourceRegistryError(f"Registry asset {asset.id} was observed in the future")
        if age > max_age:
            raise OpenSourceRegistryError(f"Registry asset {asset.id} is stale")
        ages.append(age)
        if asset.production_score >= minimum_production_score:
            eligible_categories.add(asset.category)

    missing = sorted(set(required_categories) - eligible_categories)
    if missing:
        raise OpenSourceRegistryError(
            "Open-source registry lacks production-qualified categories: " + ", ".join(missing)
        )
    categories = tuple(sorted({asset.category for asset in registry.assets}))
    return VerifiedOpenSourceRegistry(
        snapshot_sha256=registry.sha256,
        asset_count=len(registry.assets),
        categories=categories,
        freshest_age_hours=int(min(ages).total_seconds() // 3600),
        oldest_age_hours=int(max(ages).total_seconds() // 3600),
    )
