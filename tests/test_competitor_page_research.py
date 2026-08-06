from datetime import datetime, timezone

import pytest

from ruos.competitor_page_research import fetch_competitor_pages
from ruos.live_research import FetchPolicy, LiveResearchAdapter, LiveResearchError, TransportResponse
from ruos.search_discovery import SearchDiscovery, SearchResult


class RankedTransport:
    def __init__(self, failing: set[str] | None = None) -> None:
        self.failing = failing or set()

    def fetch(self, url: str, policy: FetchPolicy) -> TransportResponse:
        if url in self.failing:
            raise LiveResearchError("simulated failure")
        body = f"<html><title>{url}</title><body>Observed competitor page content for {url}</body></html>".encode()
        return TransportResponse(url, url, 200, {"content-type": "text/html; charset=utf-8"}, body)


def _discovery() -> SearchDiscovery:
    return SearchDiscovery(
        "fake",
        "سازه‌های تبلیغاتی",
        "ir",
        "fa",
        "2026-08-06T05:00:00Z",
        tuple(SearchResult(rank, f"نتیجه {rank}", f"https://example{rank}.com/page", f"شرح {rank}") for rank in range(1, 6)),
    )


def _adapter(failing: set[str] | None = None) -> LiveResearchAdapter:
    return LiveResearchAdapter(
        transport=RankedTransport(failing),
        clock=lambda: datetime(2026, 8, 6, 6, 0, tzinfo=timezone.utc),
    )


def test_fetch_competitor_pages_preserves_discovery_traceability() -> None:
    discovery = _discovery()
    result = fetch_competitor_pages(discovery, _adapter(), limit=4, minimum_success=3)

    assert result.discovery_sha256 == discovery.sha256
    assert [item.source_id for item in result.evidence] == [
        "competitor-page:1",
        "competitor-page:2",
        "competitor-page:3",
        "competitor-page:4",
    ]
    assert result.evidence[0].requested_url == discovery.results[0].url
    assert "Observed search rank 1" in result.evidence[0].observations[0]
    assert result.evidence[0].manual_claims == ("Search snippet: شرح 1",)


def test_fetch_competitor_pages_allows_bounded_failures() -> None:
    discovery = _discovery()
    result = fetch_competitor_pages(
        discovery,
        _adapter({discovery.results[1].url}),
        limit=4,
        minimum_success=3,
    )
    assert [item.source_id for item in result.evidence] == [
        "competitor-page:1",
        "competitor-page:3",
        "competitor-page:4",
    ]


def test_fetch_competitor_pages_rejects_insufficient_evidence() -> None:
    discovery = _discovery()
    failing = {item.url for item in discovery.results[:3]}
    with pytest.raises(LiveResearchError, match="minimum is 3"):
        fetch_competitor_pages(discovery, _adapter(failing), limit=4, minimum_success=3)


def test_fetch_competitor_pages_validates_limits() -> None:
    with pytest.raises(LiveResearchError, match="limit must be between"):
        fetch_competitor_pages(_discovery(), _adapter(), limit=0)
    with pytest.raises(LiveResearchError, match="minimum_success"):
        fetch_competitor_pages(_discovery(), _adapter(), limit=3, minimum_success=4)
