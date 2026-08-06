from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .live_research import LiveResearchError
from .research_snapshot import ResearchSnapshot
from .research_studio import ResearchSource


@dataclass(frozen=True)
class VerifiedResearchEvidence:
    page_slug: str
    snapshot_sha256: str
    created_at: str
    source_count: int
    covered_source_ids: tuple[str, ...]
    freshness_hours: int

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "snapshot_sha256": self.snapshot_sha256,
            "created_at": self.created_at,
            "source_count": self.source_count,
            "covered_source_ids": list(self.covered_source_ids),
            "freshness_hours": self.freshness_hours,
            "status": "verified-live",
        }


def verify_snapshot(
    page_slug: str,
    sources: Iterable[ResearchSource],
    snapshot: ResearchSnapshot,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(days=14),
) -> VerifiedResearchEvidence:
    if snapshot.page_slug != page_slug:
        raise LiveResearchError("Research snapshot does not belong to the requested page")
    expected = {source.id: source for source in sources}
    observed = {item.source_id: item for item in snapshot.evidence}
    missing = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))
    if missing:
        raise LiveResearchError("Research snapshot is missing configured sources: " + ", ".join(missing))
    if unexpected:
        raise LiveResearchError("Research snapshot contains unknown sources: " + ", ".join(unexpected))
    for source_id, source in expected.items():
        evidence = observed[source_id]
        if evidence.requested_url != source.url:
            raise LiveResearchError(f"Research source URL changed after snapshot: {source_id}")
        if evidence.status < 200 or evidence.status >= 300:
            raise LiveResearchError(f"Research source is not successful: {source_id}")
        if not evidence.excerpt.strip() or len(evidence.content_sha256) != 64:
            raise LiveResearchError(f"Research source has incomplete live evidence: {source_id}")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    created = datetime.fromisoformat(snapshot.created_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    age = current - created
    if age < timedelta(0):
        raise LiveResearchError("Research snapshot timestamp is in the future")
    if age > max_age:
        raise LiveResearchError(
            f"Research snapshot is stale ({age.days} days old; maximum {max_age.days} days)"
        )
    return VerifiedResearchEvidence(
        page_slug=page_slug,
        snapshot_sha256=snapshot.sha256,
        created_at=snapshot.created_at,
        source_count=len(snapshot.evidence),
        covered_source_ids=tuple(sorted(observed)),
        freshness_hours=int(age.total_seconds() // 3600),
    )
