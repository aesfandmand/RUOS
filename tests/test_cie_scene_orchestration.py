from pathlib import Path

from ruos.cie_build import compile_page_with_cie, generate_cie_blueprint
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


def test_scene_orchestration_resolves_every_structures_section():
    page=load_page_spec(Path("pages/structures.json"))
    blueprint=generate_cie_blueprint(page)
    plan=blueprint["scene_orchestration"]
    assert plan["status"]=="ready"
    assert len(plan["sections"])==len(page.sections)
    by_id={item["section_id"]:item for item in plan["sections"]}
    hero=by_id["hero"]
    assert hero["pattern"]=="cinematic-scroll-stage"
    assert [scene["id"] for scene in hero["scenes"]]==["establish","depth","focus","handoff"]
    assert hero["scenes"][-1]["range"]==[0.75,1.0]
    interaction=by_id["interaction"]
    assert interaction["driver"]=="interaction-and-scroll"
    assert interaction["final_state"]=="resolve"


def test_scene_orchestration_is_bound_to_implementation_and_runtime(tmp_path):
    page=load_page_spec(Path("pages/structures.json"))
    blueprint=generate_cie_blueprint(page)
    implementation=blueprint["ui_implementation_contract"]
    assert implementation["version"]=="1.2"
    assert implementation["global_contract"]["scene_orchestration_required"] is True
    assert all(section["scene_orchestration"]["scenes"] for section in implementation["sections"])
    result=compile_page_with_cie(page,BuildContext(project_root=Path("."),output_root=tmp_path,strict=False))
    html=(result.output_dir/"index.html").read_text(encoding="utf-8")
    runtime=(result.output_dir/"assets/runtime.js").read_text(encoding="utf-8")
    assert "data-cie-scene=" in html
    assert "RUOS_CIE_SCENES" in runtime
    assert "cieSceneProgress" in runtime
    assert "data-cie-scene-visible" in (result.output_dir/"assets/styles.css").read_text(encoding="utf-8")
