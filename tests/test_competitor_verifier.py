from datetime import datetime, timedelta, timezone

import pytest

from ruos.competitor_page_research import CompetitorPageResearch
from ruos.competitor_snapshot import build_competitor_snapshot
from ruos.competitor_verifier import verify_competitor_evidence
from ruos.live_research import LiveEvidence, LiveResearchError
from ruos.search_discovery import SearchDiscovery, SearchResult


NOW = datetime(2026, 8, 6, 6, 30, tzinfo=timezone.utc)


def _discovery() -> SearchDiscovery:
    return SearchDiscovery(
        "brave",
        "سازه‌های تبلیغاتی",
        "ir",
        "fa",
        "2026-08-06T06:00:00Z",
        tuple(
            SearchResult(rank, f"Result {rank}", f"https://example{rank}.com/page", "snippet")
            for rank in range(1, 6)
        ),
    )


def _evidence(rank: int, *, url: str | None = None, fetched_at: str = "2026-08-06T06:05:00Z") -> LiveEvidence:
    requested = url or f"https://example{rank}.com/page"
    return LiveEvidence(
        f"competitor-page:{rank}", requested, requested, "live-web", fetched_at, 200,
        "text/html", str(rank) * 64, 1200, f"Page {rank}", "Observed page content",
        (), (), (),
    )


def _snapshot(discovery: SearchDiscovery):
    return build_competitor_snapshot(
        "structures",
        CompetitorPageResearch(discovery.sha256, (_evidence(1), _evidence(2), _evidence(3))),
    )


def test_verifier_accepts_fresh_traceable_pages() -> None:
    discovery = _discovery()
    verified = verify_competitor_evidence(
        _snapshot(discovery), discovery, expected_page_slug="structures", now=NOW
    )
    assert verified.evidence_count == 3
    assert verified.covered_ranks == (1, 2, 3)
    assert verified.discovery_sha256 == discovery.sha256
    assert len(verified.snapshot_sha256) == 64


def test_verifier_rejects_page_not_traceable_to_discovery() -> None:
    discovery = _discovery()
    snapshot = build_competitor_snapshot(
        "structures",
        CompetitorPageResearch(discovery.sha256, (_evidence(1, url="https://other.com"), _evidence(2), _evidence(3))),
    )
    with pytest.raises(LiveResearchError, match="not traceable"):
        verify_competitor_evidence(snapshot, discovery, expected_page_slug="structures", now=NOW)


def test_verifier_rejects_stale_pages() -> None:
    discovery = _discovery()
    snapshot = build_competitor_snapshot(
        "structures",
        CompetitorPageResearch(
            discovery.sha256,
            (_evidence(1, fetched_at="2026-07-20T00:00:00Z"), _evidence(2), _evidence(3)),
        ),
    )
    with pytest.raises(LiveResearchError, match="stale"):
        verify_competitor_evidence(
            snapshot,
            discovery,
            expected_page_slug="structures",
            now=NOW,
            max_age=timedelta(days=7),
        )
