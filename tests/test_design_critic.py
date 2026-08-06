from dataclasses import replace
from pathlib import Path

import pytest

from ruos.component_resolver import resolve_components
from ruos.competitive_intelligence import build_competitive_intelligence
from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.creative_selection import select_creative_library
from ruos.design_critic import DesignCriticError, critique_design
from ruos.motion_composer import compose_motion
from ruos.pattern_intelligence import select_patterns
from ruos.pattern_resolver import resolve_patterns
from ruos.qa import evaluate
from ruos.quality_score import calculate_agency_quality
from ruos.query_intelligence import build_query_intelligence
from ruos.render import render_css, render_document, render_runtime
from ruos.research_studio import conduct_research
from ruos.semantic_enhancer import enhance_semantics
from ruos.spec_loader import load_page_spec
from ruos.studio_knowledge import compose_studio_knowledge
from ruos.visual_dna import resolve_visual_dna


def _inputs():
    page = load_page_spec(Path("pages/structures.json"))
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    research = conduct_research(page, intelligence)
    queries = build_query_intelligence(page, research, intelligence)
    competition = build_competitive_intelligence(page, research)
    components = resolve_components(page)
    selected_patterns = select_patterns(page, research, queries, competition)
    graph = compose_studio_knowledge(page, research, queries, selected_patterns)
    selection = select_creative_library(page, queries, components, selected_patterns, graph)
    patterns = resolve_patterns(page, components)
    motion = compose_motion(patterns, components)
    html = enhance_semantics(page, intelligence, render_document(page, components)).html
    css = render_css(resolve_visual_dna(page.visual_profile))
    runtime = render_runtime() + "\nconst reduceMotion=true;const target=document.body;target.animate([],{duration:0});"
    gates = evaluate(page, html, css, runtime)
    quality = calculate_agency_quality(gates)
    return page, gates, quality, selection


def test_critic_is_deterministic_and_actionable() -> None:
    page, gates, quality, selection = _inputs()
    first = critique_design(page, gates, quality, selection)
    second = critique_design(page, gates, quality, selection)

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert len(first.findings) == 10
    assert all(finding.action for finding in first.findings)
    assert first.release_recommendation in {"publish", "publish-with-backlog"}
    assert first.selection_sha256 == selection.sha256


def test_critic_rejects_a_failed_quality_gate() -> None:
    page, gates, _, selection = _inputs()
    broken = tuple(
        replace(gate, passed=False, score=35, failures=("conversion proof is missing",))
        if gate.gate == "conversion"
        else gate
        for gate in gates
    )
    critique = critique_design(page, broken, calculate_agency_quality(broken), selection)

    assert critique.release_recommendation == "reject"
    assert any("conversion" in blocker for blocker in critique.blockers)


def test_critic_requires_the_complete_gate_contract() -> None:
    page, gates, quality, selection = _inputs()
    incomplete = tuple(gate for gate in gates if gate.gate != "motion")
    with pytest.raises(DesignCriticError, match="missing QA gates"):
        critique_design(page, incomplete, quality, selection)
