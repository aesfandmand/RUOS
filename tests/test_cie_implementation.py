from pathlib import Path

from ruos.cie_build import generate_cie_blueprint
from ruos.spec_loader import load_page_spec


def test_ui_implementation_contract_is_complete_for_every_section():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    contract = blueprint["ui_implementation_contract"]
    assert contract["status"] == "ready"
    assert contract["blockers"] == []
    assert contract["execution_model"] == "single-codebase-progressive-enhancement"
    assert len(contract["sections"]) == len(page.sections)
    assert contract["global_contract"]["semantic_html_first"] is True
    assert contract["global_contract"]["mobile_touch_first"] is True
    assert contract["global_contract"]["reduced_motion_required"] is True

    for section in contract["sections"]:
        assert section["section_id"]
        assert section["component"]["variant"]
        assert section["dom"]["root"] == "section"
        assert section["dom"]["semantic_parity_required"] is True
        assert section["css"]["responsive_strategy"] == "single-codebase-fluid-layout"
        assert section["interaction_hooks"]["touch_required"] is True
        assert "reduced_motion_fallback" in section["motion_hooks"]
        assert section["responsive"]["touch_targets_min_px"] >= 44
        assert section["responsive"]["hover_only_forbidden"] is True
        assert section["qa_assertions"]
        assert section["schema_mapping"]
        assert section["evidence"]


def test_ui_contract_contains_implementation_hooks_for_runtime_and_qa():
    page = load_page_spec(Path("pages/structures.json"))
    contract = generate_cie_blueprint(page)["ui_implementation_contract"]
    section_ids = {section.id for section in page.sections}
    emitted_ids = {section["section_id"] for section in contract["sections"]}
    assert emitted_ids == section_ids

    for section in contract["sections"]:
        attrs = section["interaction_hooks"]["data_attributes"]
        assert any(value.startswith("data-ruos-section=") for value in attrs)
        assert any(value.startswith("data-ruos-variant=") for value in attrs)
        qa_ids = {check["id"] for check in section["qa_assertions"]}
        assert f"{section['section_id']}:responsive-parity" in qa_ids
        assert f"{section['section_id']}:reduced-motion" in qa_ids
        assert f"{section['section_id']}:anti-copy" in qa_ids
