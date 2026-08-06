from pathlib import Path

from ruos.component_resolver import resolve_components
from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.motion_composer import compose_motion
from ruos.pattern_resolver import resolve_patterns
from ruos.qa import evaluate
from ruos.quality_score import calculate_agency_quality
from ruos.render import render_css, render_document, render_runtime
from ruos.semantic_enhancer import enhance_semantics
from ruos.spec_loader import load_page_spec
from ruos.studio_artifacts import build_studio_artifacts
from ruos.visual_dna import resolve_visual_dna


def _bundle():
    page = load_page_spec(Path("pages/structures.json"))
    dna = resolve_visual_dna(page.visual_profile)
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    components = resolve_components(page)
    patterns = resolve_patterns(page, components)
    motion = compose_motion(patterns, components)
    html = enhance_semantics(page, intelligence, render_document(page, components)).html
    css = render_css(dna)
    runtime = render_runtime() + "\nconst reduceMotion=true;const target=document.body;target.animate([],{duration:0});"
    gates = evaluate(page, html, css, runtime)
    quality = calculate_agency_quality(gates)
    return build_studio_artifacts(page, dna, components, patterns, motion, content, intelligence, gates, quality)


def test_studio_artifact_pipeline_is_complete_and_ordered() -> None:
    bundle = _bundle()
    assert [artifact.name for artifact in bundle.artifacts] == [
        "research.json",
        "query-intelligence.json",
        "competitive-analysis.json",
        "pattern-selection.json",
        "design-brief.json",
        "creative-direction.json",
        "art-direction.json",
        "ux-plan.json",
        "ui-plan.json",
        "motion-plan.json",
        "content-plan.json",
        "seo-plan.json",
        "cro-plan.json",
        "agency-review.json",
    ]
    assert bundle.by_name("research.json").payload["primary_query"] == "سازه‌های تبلیغاتی"
    assert bundle.by_name("design-brief.json").dependencies == (
        "research.json",
        "query-intelligence.json",
        "competitive-analysis.json",
        "pattern-selection.json",
    )
    assert bundle.by_name("creative-direction.json").dependencies == ("design-brief.json",)
    assert bundle.by_name("agency-review.json").payload["publishable"] is True


def test_studio_artifacts_are_deterministic_and_dependency_addressable() -> None:
    first = _bundle()
    second = _bundle()
    assert first.manifest() == second.manifest()
    assert all(len(artifact.sha256) == 64 for artifact in first.artifacts)
    assert first.by_name("ui-plan.json").dependencies == ("art-direction.json", "ux-plan.json")
    assert first.by_name("agency-review.json").dependencies[-1] == "cro-plan.json"
