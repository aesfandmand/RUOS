from pathlib import Path

from ruos.cie_build import compile_page_with_cie, generate_cie_blueprint
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


def test_structures_experience_patterns_are_resolved_for_every_section():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    plan = blueprint["experience_patterns"]
    assert plan["status"] == "ready"
    assert len(plan["sections"]) == len(page.sections)
    by_id = {item["section_id"]: item for item in plan["sections"]}
    assert by_id["hero"]["pattern"] == "cinematic-scroll-stage"
    assert any(item["pattern"] == "structure-anatomy-explorer" for item in plan["sections"])
    assert by_id["interaction"]["pattern"] == "hotspot-decision-explorer"
    assert all(item["semantic_parity_required"] for item in plan["sections"])
    assert all(item["reduced_motion_required"] for item in plan["sections"])


def test_experience_patterns_reach_native_html_css_runtime(tmp_path):
    page = load_page_spec(Path("pages/structures.json"))
    result = compile_page_with_cie(page, BuildContext(project_root=Path("."), output_root=tmp_path, strict=False))
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    css = (result.output_dir / "assets/styles.css").read_text(encoding="utf-8")
    runtime = (result.output_dir / "assets/runtime.js").read_text(encoding="utf-8")
    assert 'data-cie-experience="cinematic-scroll-stage"' in html
    assert 'data-cie-experience="structure-anatomy-explorer"' in html
    assert "cie-pattern--horizontal-journey" in css
    assert "contract.experience.pattern==='cinematic-scroll-stage'" in runtime
    assert "data-cie-industrial-anatomy" in html
