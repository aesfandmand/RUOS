import json
from dataclasses import replace
from pathlib import Path

import pytest

from ruos.compiler import compile_page
from ruos.component_resolver import ComponentResolutionError, resolve_components
from ruos.models import BuildContext, SectionSpec
from ruos.spec_loader import load_page_spec


def _page():
    return load_page_spec(Path("pages/structures.json"))


def test_structures_resolves_to_production_component_plan() -> None:
    plan = resolve_components(_page())

    assert [component.variant for component in plan.components] == [
        "cinematic-orbit",
        "editorial-statement",
        "knowledge-triptych",
        "decision-console",
        "closing-stage",
    ]
    assert plan.components[0].emphasis == "primary"
    assert plan.components[-1].capabilities == (
        "primary-cta",
        "outcome-copy",
        "high-contrast",
    )
    assert plan.for_section("knowledge").attributes["columns"] == "3"


def test_component_plan_is_deterministic() -> None:
    first = resolve_components(_page()).fingerprint_payload()
    second = resolve_components(_page()).fingerprint_payload()

    assert first == second


def test_component_resolver_rejects_thin_knowledge_sections() -> None:
    page = _page()
    sections = tuple(
        replace(
            section,
            items=({"title": "تنها", "body": "یک گزینه برای مقایسه کافی نیست."},),
        )
        if section.kind == "knowledge"
        else section
        for section in page.sections
    )

    with pytest.raises(ComponentResolutionError, match="requires at least two items"):
        resolve_components(replace(page, sections=sections))


def test_component_resolver_enforces_page_boundaries() -> None:
    page = _page()
    reversed_sections = tuple(reversed(page.sections))

    with pytest.raises(ComponentResolutionError, match="first resolved component must be the hero"):
        resolve_components(replace(page, sections=reversed_sections))


def test_compiler_embeds_component_contract_and_fingerprint(tmp_path: Path) -> None:
    page = _page()
    result = compile_page(
        page,
        BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True),
    )
    manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    runtime = (result.output_dir / "assets/runtime.js").read_text(encoding="utf-8")

    assert len(manifest["component_plan"]) == len(page.sections)
    assert len(manifest["component_plan_sha256"]) == 64
    assert 'data-component-variant="cinematic-orbit"' in html
    assert 'data-component-capabilities="progressive-disclosure keyboard-ready state-feedback"' in html
    assert "decisionCopy" in runtime
    assert "aria-pressed" in runtime


def test_conversion_component_requires_action() -> None:
    page = _page()
    sections: list[SectionSpec] = []
    for section in page.sections:
        if section.kind == "conversion":
            sections.append(replace(section, cta_label="", cta_href=""))
        else:
            sections.append(section)

    with pytest.raises(ComponentResolutionError, match="requires both cta_label and cta_href"):
        resolve_components(replace(page, sections=tuple(sections)))
