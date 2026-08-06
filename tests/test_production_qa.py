from pathlib import Path

from ruos.models import PageSpec, SectionSpec
from ruos.qa import evaluate
from ruos.render import render_css, render_document, render_runtime
from ruos.component_resolver import resolve_components
from ruos.spec_loader import load_page_spec
from ruos.visual_dna import resolve_visual_dna


def _production_inputs():
    page = load_page_spec(Path("pages/structures.json"))
    html = render_document(page, resolve_components(page))
    css = render_css(resolve_visual_dna(page.visual_profile))
    runtime = render_runtime() + "\nconst reduceMotion=true;const target={animate(){}};"
    return page, html, css, runtime


def test_production_page_passes_all_ten_gates() -> None:
    page, html, css, runtime = _production_inputs()
    gates = evaluate(page, html, css, runtime)
    assert len(gates) == 10
    assert all(gate.passed for gate in gates)
    assert {gate.gate for gate in gates} == {
        "creative-direction",
        "reading-experience",
        "visual-rhythm",
        "storytelling",
        "interaction-accessibility",
        "motion",
        "conversion",
        "seo-query-alignment",
        "ai-readiness",
        "performance",
    }


def test_query_gate_rejects_missing_pillar() -> None:
    page, html, css, runtime = _production_inputs()
    broken = PageSpec(
        slug=page.slug,
        lang=page.lang,
        direction=page.direction,
        title=page.title,
        description=page.description,
        brand=page.brand,
        visual_profile=page.visual_profile,
        metadata={"primary_conversion": "qualified-conversation"},
        sections=page.sections,
    )
    gates = evaluate(broken, html, css, runtime)
    seo = next(gate for gate in gates if gate.gate == "seo-query-alignment")
    assert not seo.passed
    assert "primary query pillar is missing" in seo.failures


def test_conversion_gate_rejects_single_cta() -> None:
    page, html, css, runtime = _production_inputs()
    sections = tuple(
        SectionSpec(
            id=section.id,
            kind=section.kind,
            eyebrow=section.eyebrow,
            title=section.title,
            body=section.body,
            items=section.items,
            cta_label="" if section.kind == "hero" else section.cta_label,
            cta_href="" if section.kind == "hero" else section.cta_href,
        )
        for section in page.sections
    )
    broken = PageSpec(
        slug=page.slug,
        lang=page.lang,
        direction=page.direction,
        title=page.title,
        description=page.description,
        brand=page.brand,
        visual_profile=page.visual_profile,
        metadata=page.metadata,
        sections=sections,
    )
    conversion = next(gate for gate in evaluate(broken, html, css, runtime) if gate.gate == "conversion")
    assert not conversion.passed
    assert "sales journey requires contextual and closing CTAs" in conversion.failures


def test_accessibility_gate_rejects_inert_interaction() -> None:
    page, html, css, runtime = _production_inputs()
    gates = evaluate(page, html.replace("aria-live", "data-live"), css, runtime.replace("aria-pressed", "data-pressed"))
    interaction = next(gate for gate in gates if gate.gate == "interaction-accessibility")
    assert not interaction.passed
