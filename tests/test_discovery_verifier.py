from datetime import datetime, timedelta, timezone

import pytest

from ruos.discovery_verifier import verify_discovery
from ruos.live_research import LiveResearchError
from ruos.search_discovery import SearchDiscovery, SearchResult


def _discovery(*, query: str = "سازه‌های تبلیغاتی", fetched_at: str = "2026-08-06T05:00:00Z") -> SearchDiscovery:
    return SearchDiscovery(
        provider="fake",
        query=query,
        market="ir",
        language="fa",
        fetched_at=fetched_at,
        results=tuple(
            SearchResult(index, f"نتیجه {index}", f"https://example.com/{index}", "شرح")
            for index in range(1, 6)
        ),
    )


def test_discovery_verification_records_freshness() -> None:
    verified = verify_discovery(
        _discovery(),
        expected_query="سازه‌های تبلیغاتی",
        expected_market="ir",
        expected_language="fa",
        now=datetime(2026, 8, 6, 8, tzinfo=timezone.utc),
    )
    assert verified.result_count == 5
    assert verified.freshness_hours == 3
    assert verified.payload()["status"] == "verified-search-discovery"


def test_discovery_rejects_wrong_query() -> None:
    with pytest.raises(LiveResearchError, match="query"):
        verify_discovery(
            _discovery(query="بیلبورد"),
            expected_query="سازه‌های تبلیغاتی",
            expected_market="ir",
            expected_language="fa",
        )


def test_discovery_rejects_stale_snapshot() -> None:
    with pytest.raises(LiveResearchError, match="stale"):
        verify_discovery(
            _discovery(fetched_at="2026-07-01T05:00:00Z"),
            expected_query="سازه‌های تبلیغاتی",
            expected_market="ir",
            expected_language="fa",
            now=datetime(2026, 8, 6, 5, tzinfo=timezone.utc),
            max_age=timedelta(days=7),
        )
