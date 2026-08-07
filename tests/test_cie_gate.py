from dataclasses import replace
from pathlib import Path

import pytest

from ruos.cie_build import generate_cie_blueprint
from ruos.cie_gate import evaluate_cie_gate
from ruos.spec_loader import load_page_spec


def _page():
    return load_page_spec(Path("pages/structures.json"))


def test_structure_blueprint_uses_nrg_and_responsive_single_system() -> None:
    blueprint = generate_cie_blueprint(_page())
    references = {item["reference"] for item in blueprint["reference_translation"]}

    assert "NRG Build Your Data Center" in references
    assert blueprint["responsive_strategy"]["single_codebase"] is True
    assert blueprint["interaction_model"]["mobile"]
    assert blueprint["interaction_model"]["reduced_motion"]
    assert blueprint["gate"]["status"] in {"pass", "pass_with_conditions"}
    assert blueprint["gate_report"]["score"] >= 75


def test_unsupported_claims_are_a_hard_blocker() -> None:
    page = _page()
    metadata = dict(page.metadata)
    metadata["unsupported_claims"] = ["invented wind-load value"]
    blocked_page = replace(page, metadata=metadata)

    blueprint = generate_cie_blueprint(blocked_page)

    assert blueprint["gate"]["status"] == "blocked"
    assert "CIE-006" in blueprint["gate"]["failed_rules"]
    assert blueprint["gate_report"]["evidence_needed"]


def test_gate_rejects_missing_mobile_translation() -> None:
    page = _page()
    blueprint = generate_cie_blueprint(page)
    blueprint["interaction_model"] = dict(blueprint["interaction_model"])
    blueprint["interaction_model"]["mobile"] = ""

    gate = evaluate_cie_gate(blueprint, page)

    assert gate.status == "blocked"
    assert "CIE-007" in gate.failed_rules


def test_reference_translation_has_explicit_anti_copy_constraint() -> None:
    blueprint = generate_cie_blueprint(_page())

    assert blueprint["reference_translation"]
    assert all(item["anti_copy_constraint"] for item in blueprint["reference_translation"])
    assert all(item["source_url"].startswith("https://") for item in blueprint["reference_translation"])
