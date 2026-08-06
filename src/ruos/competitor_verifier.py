from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from .competitor_snapshot import CompetitorEvidenceSnapshot
from .live_research import LiveResearchError
from .search_discovery import SearchDiscovery


@dataclass(frozen=True)
class VerifiedCompetitorEvidence:
    page_slug: str
    discovery_sha256: str
    snapshot_sha256: str
    evidence_count: int
    covered_ranks: tuple[int, ...]
    freshness_hours: int

    def payload(self) -> dict[str, object]:
        return {
            "status": "verified-competitor-pages",
            "page_slug": self.page_slug,
            "discovery_sha256": self.discovery_sha256,
            "snapshot_sha256": self.snapshot_sha256,
            "evidence_count": self.evidence_count,
            "covered_ranks": list(self.covered_ranks),
            "freshness_hours": self.freshness_hours,
        }


def verify_competitor_evidence(
    snapshot: CompetitorEvidenceSnapshot,
    discovery: SearchDiscovery,
    *,
    expected_page_slug: str,
    now: datetime | None = None,
    max_age: timedelta = timedelta(days=7),
    minimum_pages: int = 3,
) -> VerifiedCompetitorEvidence:
    if snapshot.page_slug != expected_page_slug:
        raise LiveResearchError("Competitor evidence snapshot belongs to a different page")
    if snapshot.discovery_sha256 != discovery.sha256:
        raise LiveResearchError("Competitor evidence does not match the verified search discovery")
    if len(snapshot.evidence) < minimum_pages:
        raise LiveResearchError(
            f"Competitor evidence has {len(snapshot.evidence)} pages; minimum is {minimum_pages}"
        )
    result_by_rank = {item.rank: item for item in discovery.results}
    ranks: list[int] = []
    fetched_times: list[datetime] = []
    for item in snapshot.evidence:
        try:
            rank = int(item.source_id.rsplit(":", 1)[-1])
        except ValueError as exc:
            raise LiveResearchError("Competitor evidence source id has an invalid rank") from exc
        result = result_by_rank.get(rank)
        if result is None or item.requested_url != result.url:
            raise LiveResearchError("Competitor evidence is not traceable to the discovered result URL")
        final_domain = (urlparse(item.final_url).hostname or "").lower()
        if not final_domain or not item.final_url.startswith("https://"):
            raise LiveResearchError("Competitor evidence final URL is invalid")
        if item.status < 200 or item.status >= 300 or not item.excerpt.strip():
            raise LiveResearchError("Competitor evidence does not contain a successful observed page")
        try:
            fetched_times.append(
                datetime.fromisoformat(item.fetched_at.replace("Z", "+00:00")).astimezone(timezone.utc)
            )
        except ValueError as exc:
            raise LiveResearchError("Competitor evidence timestamp is invalid") from exc
        ranks.append(rank)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    oldest = min(fetched_times)
    age = current - oldest
    if age < timedelta(0):
        raise LiveResearchError("Competitor evidence timestamp is in the future")
    if age > max_age:
        raise LiveResearchError("Competitor evidence snapshot is stale")
    return VerifiedCompetitorEvidence(
        page_slug=snapshot.page_slug,
        discovery_sha256=snapshot.discovery_sha256,
        snapshot_sha256=snapshot.sha256,
        evidence_count=len(snapshot.evidence),
        covered_ranks=tuple(ranks),
        freshness_hours=int(age.total_seconds() // 3600),
    )
