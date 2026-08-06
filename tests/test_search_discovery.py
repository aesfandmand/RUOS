from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ruos.live_research import LiveResearchError
from ruos.search_discovery import SearchResult, create_provider, discover_search


class FakeProvider:
    name = "fake"

    def search(self, query: str, *, market: str, language: str, count: int):
        assert query == "سازه‌های تبلیغاتی"
        assert market == "ir"
        assert language == "fa"
        assert count == 2
        return (
            SearchResult(1, "نتیجه اول", "https://example.com/one", "شرح اول"),
            SearchResult(2, "نتیجه دوم", "https://example.com/two", "شرح دوم"),
        )


def test_discovery_is_traceable_and_deterministic() -> None:
    clock = lambda: datetime(2026, 8, 6, 5, 0, tzinfo=timezone.utc)
    first = discover_search(FakeProvider(), " سازه‌های تبلیغاتی ", market="ir", language="fa", count=2, clock=clock)
    second = discover_search(FakeProvider(), "سازه‌های تبلیغاتی", market="ir", language="fa", count=2, clock=clock)

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert first.provider == "fake"
    assert first.fetched_at == "2026-08-06T05:00:00Z"
    assert [item.rank for item in first.results] == [1, 2]
    assert len(first.sha256) == 64


def test_discovery_rejects_empty_query() -> None:
    with pytest.raises(LiveResearchError, match="requires a query"):
        discover_search(FakeProvider(), "   ")


def test_provider_factory_rejects_unknown_provider() -> None:
    with pytest.raises(LiveResearchError, match="Unsupported search provider"):
        create_provider("unknown")


def test_brave_provider_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    with pytest.raises(LiveResearchError, match="BRAVE_SEARCH_API_KEY"):
        create_provider("brave")


def test_serper_provider_requires_api_key(monkeypatch) -> None:
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    with pytest.raises(LiveResearchError, match="SERPER_API_KEY"):
        create_provider("serper")
