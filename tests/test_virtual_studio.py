from dataclasses import replace
from pathlib import Path

import pytest

from ruos.component_resolver import resolve_components
from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.models import GateResult
from ruos.motion_composer import compose_motion
from ruos.pattern_resolver import resolve_patterns
from ruos.qa import evaluate
from ruos.quality_score import calculate_agency_quality
from ruos.render import render_css, render_document, render_runtime
from ruos.research_studio import conduct_research
from ruos.semantic_enhancer import enhance_semantics
from ruos.spec_loader import load_page_spec
from ruos.virtual_studio import VirtualStudioError, conduct_virtual_studio_review
from ruos.visual_dna import resolve_visual_dna


def _review_inputs():
    page = load_page_spec(Path("pages/structures.json"))
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    components = resolve_components(page)
    patterns = resolve_patterns(page, components)
    motion = compose_motion(patterns, components)
    html = enhance_semantics(page, intelligence, render_document(page, components)).html
    css = render_css(resolve_visual_dna(page.visual_profile))
    runtime = render_runtime() + "\nconst reduceMotion=true;const target=document.body;target.animate([],{duration:0});"
    gates = evaluate(page, html, css, runtime)
    quality = calculate_agency_quality(gates)
    research = conduct_research(page, intelligence)
    return page, research, gates, quality


def test_virtual_studio_is_deterministic_and_unanimous() -> None:
    page, research, gates, quality = _review_inputs()
    first = conduct_virtual_studio_review(page, research, gates, quality)
    second = conduct_virtual_studio_review(page, research, gates, quality)

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert len(first.verdicts) == 10
    assert first.unanimous
    assert first.publishable
    assert first.total_score >= 88
    assert {verdict.role for verdict in first.verdicts} == {
        "Creative Director",
        "Art Director",
        "UX Lead",
        "UI Lead",
        "Motion Lead",
        "Content Director",
        "SEO Lead",
        "CRO Lead",
        "Accessibility Lead",
        "Front-end Lead",
    }


def test_virtual_studio_rejects_failed_specialist_gate() -> None:
    page, research, gates, quality = _review_inputs()
    broken = tuple(
        replace(gate, passed=False, score=40, failures=("conversion path is ineffective",))
        if gate.gate == "conversion"
        else gate
        for gate in gates
    )
    review = conduct_virtual_studio_review(page, research, broken, calculate_agency_quality(broken))

    cro = next(verdict for verdict in review.verdicts if verdict.role == "CRO Lead")
    assert not cro.passed
    assert not review.unanimous
    assert not review.publishable
    assert any("CRO Lead" in blocker for blocker in review.blockers)


def test_virtual_studio_requires_complete_gate_contract() -> None:
    page, research, gates, quality = _review_inputs()
    incomplete = tuple(gate for gate in gates if gate.gate != "performance")

    with pytest.raises(VirtualStudioError, match="missing QA gates"):
        conduct_virtual_studio_review(page, research, incomplete, quality)


def test_virtual_studio_rejects_research_for_another_page() -> None:
    page, research, gates, quality = _review_inputs()
    foreign = replace(research, page_slug="other-page")

    with pytest.raises(VirtualStudioError, match="does not belong"):
        conduct_virtual_studio_review(page, foreign, gates, quality)
