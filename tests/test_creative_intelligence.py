from dataclasses import replace
from pathlib import Path

import pytest

from ruos.content_composer import compose_content
from ruos.creative_intelligence import CreativeIntelligenceError, build_creative_intelligence
from ruos.spec_loader import load_page_spec


def _page():
    return load_page_spec(Path("pages/structures.json"))


def test_intelligence_is_deterministic_and_query_led() -> None:
    page = _page()
    content = compose_content(page)
    first = build_creative_intelligence(page, content)
    second = build_creative_intelligence(page, content)

    assert first.fingerprint_payload() == second.fingerprint_payload()
    assert first.query.primary_query == "سازه‌های تبلیغاتی"
    assert first.query.search_intent == "commercial-investigation"
    assert "خرید سازه تبلیغاتی" in first.query.supporting_queries
    assert "سازه تبلیغاتی ایندور" in first.semantic.entities
    assert "FAQPage" in first.semantic.schema_types
    assert first.sales.conversion_goal == "qualified-conversation"
    assert first.sales.friction_policy == "phone-first-minimal-form"
    assert first.sales.commercial_routes == (
        "خرید ایندور",
        "خرید اوتدور",
        "اجاره رسانه",
        "سرمایه‌گذاری",
    )
    assert "خرید ایندور" in first.semantic.ai_summary
    assert first.creative.emotional_curve == (
        "کنجکاوی",
        "درک",
        "اعتماد",
        "وضوح تصمیم",
        "اقدام",
    )


def test_intelligence_rejects_missing_entities() -> None:
    page = _page()
    sections = tuple(replace(section, items=()) for section in page.sections)
    empty = replace(page, sections=sections)

    with pytest.raises(CreativeIntelligenceError, match="explicit entity"):
        build_creative_intelligence(empty, compose_content(empty))


def test_intelligence_requires_contextual_and_closing_ctas() -> None:
    page = _page()
    sections = tuple(
        replace(section, cta_label="", cta_href="")
        if section.kind == "hero"
        else section
        for section in page.sections
    )
    one_cta = replace(page, sections=sections)

    with pytest.raises(CreativeIntelligenceError, match="contextual and closing CTAs"):
        build_creative_intelligence(one_cta, compose_content(one_cta))


def test_intelligence_rejects_duplicate_query_configuration() -> None:
    page = _page()
    metadata = dict(page.metadata)
    metadata["supporting_queries"] = ["خرید سازه تبلیغاتی", "خرید سازه تبلیغاتی"]

    with pytest.raises(CreativeIntelligenceError, match="duplicate values"):
        build_creative_intelligence(replace(page, metadata=metadata), compose_content(page))
