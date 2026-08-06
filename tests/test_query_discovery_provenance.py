from dataclasses import replace
from pathlib import Path

import pytest

from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.query_intelligence import QueryIntelligenceError, build_query_intelligence
from ruos.research_studio import conduct_research
from ruos.spec_loader import load_page_spec


def _page_with_discovery(query: str = "سازه‌های تبلیغاتی"):
    page = load_page_spec(Path("pages/structures.json"))
    metadata = dict(page.metadata)
    metadata["verified_live_research"] = {
        "status": "verified-live-with-search-discovery",
        "snapshot_sha256": "a" * 64,
        "search_discovery": {
            "status": "verified-search-discovery",
            "provider": "brave",
            "query": query,
            "market": "ir",
            "language": "fa",
            "result_count": 10,
            "freshness_hours": 1,
            "sha256": "b" * 64,
            "results": [
                {
                    "rank": 1,
                    "title": "نتیجه اول",
                    "url": "https://example.com/one",
                    "snippet": "شرح",
                }
            ],
        },
    }
    return replace(page, metadata=metadata)


def test_verified_discovery_is_bound_to_query_intelligence() -> None:
    page = _page_with_discovery()
    intelligence = build_creative_intelligence(page, compose_content(page))
    research = conduct_research(page, intelligence)

    result = build_query_intelligence(page, research, intelligence)
    payload = result.payload()

    assert result.evidence_source_ids[-1] == "search-discovery:brave"
    assert payload["discovery_evidence"]["sha256"] == "b" * 64
    assert payload["discovery_evidence"]["query"] == result.primary_query


def test_query_intelligence_rejects_mismatched_discovery_query() -> None:
    page = _page_with_discovery("خرید بیلبورد")
    intelligence = build_creative_intelligence(page, compose_content(page))
    research = conduct_research(page, intelligence)

    with pytest.raises(QueryIntelligenceError, match="does not match"):
        build_query_intelligence(page, research, intelligence)
