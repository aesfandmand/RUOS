from dataclasses import replace
from pathlib import Path

import pytest

from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.research_studio import ResearchStudioError, conduct_research
from ruos.spec_loader import load_page_spec


def _inputs():
    page = load_page_spec(Path("pages/structures.json"))
    intelligence = build_creative_intelligence(page, compose_content(page))
    return page, intelligence


def test_research_brief_is_traceable_and_deterministic() -> None:
    page, intelligence = _inputs()
    first = conduct_research(page, intelligence)
    second = conduct_research(page, intelligence)

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert len(first.sha256) == 64
    assert first.market == "iran"
    assert first.language == "fa"
    assert first.primary_query == "سازه‌های تبلیغاتی"
    assert first.evidence_status == "ready"
    assert first.evidence_score >= 75
    assert len(first.sources) >= 5
    assert {source.kind for source in first.sources} >= {
        "search-demand",
        "competitor",
        "design-reference",
    }
    assert {candidate.kind for candidate in first.pattern_candidates} >= {
        "storytelling",
        "scroll",
        "motion",
        "interaction",
    }
    assert all(candidate.source_id in {source.id for source in first.sources} for candidate in first.pattern_candidates)


def test_research_rejects_missing_required_source_kind() -> None:
    page, intelligence = _inputs()
    research = dict(page.metadata["research"])
    research["sources"] = [
        source for source in research["sources"] if source["kind"] != "search-demand"
    ]
    metadata = dict(page.metadata)
    metadata["research"] = research

    with pytest.raises(ResearchStudioError, match="search-demand"):
        conduct_research(replace(page, metadata=metadata), intelligence)


def test_research_rejects_untraceable_pattern_source() -> None:
    page, intelligence = _inputs()
    research = dict(page.metadata["research"])
    patterns = [dict(pattern) for pattern in research["patterns"]]
    patterns[0]["source_id"] = "missing-source"
    research["patterns"] = patterns
    metadata = dict(page.metadata)
    metadata["research"] = research

    with pytest.raises(ResearchStudioError, match="unknown source"):
        conduct_research(replace(page, metadata=metadata), intelligence)


def test_research_does_not_invent_numeric_search_volume() -> None:
    page, intelligence = _inputs()
    brief = conduct_research(page, intelligence)
    payload = brief.payload()

    assert "search_volume" not in payload
    assert any("حجم جست‌وجوی عددی" in limitation for limitation in brief.limitations)
