from dataclasses import replace
from pathlib import Path

import pytest

from ruos.competitive_intelligence import CompetitiveIntelligenceError, build_competitive_intelligence
from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.research_studio import conduct_research
from ruos.spec_loader import load_page_spec


def _research_with_discovery():
    page = load_page_spec(Path("pages/structures.json"))
    intelligence = build_creative_intelligence(page, compose_content(page))
    research = conduct_research(page, intelligence)
    discovery = {
        "status": "verified-search-discovery",
        "provider": "brave",
        "query": "سازه‌های تبلیغاتی",
        "sha256": "a" * 64,
        "results": [
            {
                "rank": rank,
                "title": f"نتیجه {rank}",
                "url": f"https://example{rank}.com/page",
                "snippet": f"شرح مشاهده‌شده {rank}",
            }
            for rank in range(1, 6)
        ],
    }
    return page, replace(
        research,
        evidence_status="verified-live-with-search-discovery",
        provenance={"status": "verified-live-with-search-discovery", "search_discovery": discovery},
    )


def test_competitive_intelligence_uses_verified_search_results() -> None:
    page, research = _research_with_discovery()
    result = build_competitive_intelligence(page, research)

    assert result.discovery_provider == "brave"
    assert result.discovery_sha256 == "a" * 64
    assert len(result.discovered_competitors) == 5
    assert result.discovered_competitors[0].domain == "example1.com"
    observed = [signal for signal in result.signals if signal.signal_type == "observed-search-result"]
    assert len(observed) == 5
    assert observed[0].source_id == "search-discovery:brave:1"
    assert "شرح مشاهده‌شده 1" in observed[0].observation
    assert "fetch the page" in observed[0].implication


def test_competitive_intelligence_remains_explicit_without_discovery() -> None:
    page = load_page_spec(Path("pages/structures.json"))
    intelligence = build_creative_intelligence(page, compose_content(page))
    research = conduct_research(page, intelligence)
    result = build_competitive_intelligence(page, research)

    assert result.discovered_competitors == ()
    assert result.discovery_provider is None
    declared = [signal for signal in result.signals if signal.signal_type == "declared-market-source"]
    assert declared
    assert "hypothesis" in declared[0].implication


def test_competitive_intelligence_rejects_tampered_discovery_order() -> None:
    page, research = _research_with_discovery()
    provenance = dict(research.provenance or {})
    discovery = dict(provenance["search_discovery"])
    rows = [dict(item) for item in discovery["results"]]
    rows[0]["rank"] = 2
    discovery["results"] = rows
    provenance["search_discovery"] = discovery

    with pytest.raises(CompetitiveIntelligenceError, match="ranks must be contiguous"):
        build_competitive_intelligence(page, replace(research, provenance=provenance))
