"""content_brief.py — real query construction + discovery + fetch,
orchestrated per structure, proven offline with a fake provider/transport
(no BRAVE_SEARCH_API_KEY/SERPER_API_KEY needed here — search_discovery.py's
SearchProvider and live_research.py's ResearchTransport are both injectable
Protocols; the CLI is the only place that reads a real key from the
environment).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from ruos.architecture_registry import StructureRecord
from ruos.content_brief import (
    QuerySpec,
    build_content_brief,
    default_queries,
    render_brief_markdown,
    write_content_brief,
)
from ruos.live_research import LiveResearchAdapter, LiveResearchError, TransportResponse
from ruos.research_snapshot import load_snapshot
from ruos.search_discovery import SearchResult

_CLOCK = lambda: datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc)


def _structure(**overrides) -> StructureRecord:
    base = dict(
        id="STR-TEST", name_fa="استرابورد آزمایشی", family="استرابورد", context="outdoor",
        url="/structures/test-structure/", route="outdoor_purchase",
        orientation="horizontal", dimensions="5x3", face_count=None, mounting=None,
    )
    base.update(overrides)
    return StructureRecord(**base)


class FakeProvider:
    name = "fake"

    def __init__(self, results_per_query: int = 5) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.results_per_query = results_per_query

    def search(self, query: str, *, market: str, language: str, count: int):
        self.calls.append((query, market, language))
        return tuple(
            SearchResult(i + 1, f"نتیجه {i + 1}", f"https://example.com/{market}/{i + 1}", "خلاصه")
            for i in range(min(count, self.results_per_query))
        )


class FakeTransport:
    def fetch(self, url: str, policy) -> TransportResponse:
        body = (
            "<html><head><title>صفحه واقعی</title></head><body><main>"
            f"متن واقعی نمونه دربارهٔ سازه، آماده برای نقل‌قول با ارجاع به {url}. " * 4
            + "</main></body></html>"
        )
        return TransportResponse(
            requested_url=url, final_url=url, status=200,
            headers={"content-type": "text/html; charset=utf-8"}, body=body.encode("utf-8"),
        )


def test_default_queries_trace_to_real_structure_fields() -> None:
    queries = default_queries(_structure())
    assert len(queries) == 2
    iran, intl = queries
    assert iran.market == "ir" and iran.language == "fa"
    assert "استرابورد آزمایشی" in iran.query
    assert intl.market == "us" and intl.language == "en"


def test_build_content_brief_runs_both_passes_and_verifies() -> None:
    provider = FakeProvider()
    adapter = LiveResearchAdapter(transport=FakeTransport(), clock=_CLOCK)
    brief = build_content_brief(
        _structure(), provider, adapter=adapter, clock=_CLOCK, now=_CLOCK(),
        results_per_query=5, fetch_per_query=2,
    )
    assert len(provider.calls) == 2  # iran pass + international pass
    assert brief.verified.source_count == 4  # 2 queries x fetch_per_query=2
    assert brief.slug == "test-structure"
    assert all(source.id.startswith("test-structure-") for source in brief.sources)


def test_a_query_that_yields_no_usable_results_fails_loudly() -> None:
    class EmptyProvider:
        name = "empty"

        def search(self, query, *, market, language, count):
            raise LiveResearchError("fake provider returned no usable results")

    with pytest.raises(LiveResearchError):
        build_content_brief(_structure(), EmptyProvider(), adapter=LiveResearchAdapter(transport=FakeTransport()))


def test_write_content_brief_round_trips_full_text_through_the_snapshot(tmp_path: Path) -> None:
    provider = FakeProvider()
    adapter = LiveResearchAdapter(transport=FakeTransport(), clock=_CLOCK)
    brief = build_content_brief(_structure(), provider, adapter=adapter, clock=_CLOCK, now=_CLOCK(), fetch_per_query=1)

    snapshot_path, brief_path = write_content_brief(brief, tmp_path)
    assert snapshot_path.is_file() and brief_path.is_file()

    reloaded = load_snapshot(snapshot_path)
    assert reloaded.evidence[0].full_text  # the longer body text survived the JSON round trip
    assert "متن واقعی نمونه" in reloaded.evidence[0].full_text


def test_brief_markdown_carries_real_citations_a_drafter_can_use() -> None:
    provider = FakeProvider()
    adapter = LiveResearchAdapter(transport=FakeTransport(), clock=_CLOCK)
    brief = build_content_brief(_structure(), provider, adapter=adapter, clock=_CLOCK, now=_CLOCK(), fetch_per_query=1)

    markdown = render_brief_markdown(brief)
    for source in brief.sources:
        assert f"`{source.id}`" in markdown
        assert source.url in markdown
    assert "متن واقعی نمونه" in markdown


def test_custom_queries_are_honoured_over_the_defaults() -> None:
    provider = FakeProvider()
    adapter = LiveResearchAdapter(transport=FakeTransport(), clock=_CLOCK)
    custom = (QuerySpec("custom", "پرسش سفارشی", "ir", "fa"),)
    brief = build_content_brief(_structure(), provider, queries=custom, adapter=adapter, clock=_CLOCK, now=_CLOCK())
    assert provider.calls == [("پرسش سفارشی", "ir", "fa")]
    assert brief.queries == custom
