from pathlib import Path

from ruos.cie_build import generate_cie_blueprint
from ruos.spec_loader import load_page_spec


def test_creative_director_produces_one_executable_decision_per_section():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    director = blueprint["creative_director"]
    assert director["status"] == "ready"
    assert director["blockers"] == []
    assert len(director["sections"]) == len(page.sections)
    assert director["global_rules"]["single_codebase"] is True
    assert director["global_rules"]["mobile_touch_first"] is True
    assert director["global_rules"]["reduced_motion_required"] is True
    for decision in director["sections"]:
        assert decision["section_id"]
        assert decision["intent"]
        assert decision["visual_treatment"]
        assert decision["mobile_translation"]
        assert decision["fallback"]
        assert decision["schema_mapping"]
        assert decision["evidence"]


def test_structure_director_includes_industrial_provider_guidance():
    page = load_page_spec(Path("pages/structures.json"))
    director = generate_cie_blueprint(page)["creative_director"]
    assert all("industrial_product" in section["provider_guidance"] for section in director["sections"])
