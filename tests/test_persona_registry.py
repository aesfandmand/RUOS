from pathlib import Path

import pytest
import yaml

from ruos.architecture_registry import ArchitectureRegistryError
from ruos.persona_registry import (
    journey_rows_for_entry_page,
    load_behavioral_guardrails,
    load_buying_situations,
    load_journey_matrix,
    load_personas,
    load_pricing_presentation_model,
)

REAL_ROOT = Path("11-projects/red-umbrella/registries")


def _write(root: Path, filename: str, payload: dict) -> None:
    (root / filename).write_text(yaml.dump(payload, allow_unicode=True), encoding="utf-8")


def test_loads_core_personas_and_overlays_from_a_fixture(tmp_path: Path) -> None:
    _write(tmp_path, "persona-registry-v1.yaml", {
        "core_personas": [{
            "id": "PERSONA-001",
            "name_fa": "مدیر بازاریابی",
            "evidence_strength": "strong",
            "central_mental_statement": "باید نتیجه بگیرم",
            "dominant_buying_role": ["Initiator", "Influencer"],
            "contexts": ["Corporate"],
            "profile": {"jtbd": "test"},
        }],
        "overlays": [{
            "id": "OVERLAY-001",
            "name_fa": "خرید/تدارکات",
            "evidence_strength": "very_strong",
            "central_question": "آیا قابل مقایسه است؟",
            "site_must_provide": ["Scope"],
        }],
    })
    core, overlays = load_personas(tmp_path)
    assert len(core) == 1
    assert core[0].dominant_buying_role == ("Initiator", "Influencer")
    assert core[0].profile["jtbd"] == "test"
    assert len(overlays) == 1
    assert overlays[0].central_mental_statement == "آیا قابل مقایسه است؟"
    assert overlays[0].is_overlay is True


def test_persona_without_id_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "persona-registry-v1.yaml", {"core_personas": [{"name_fa": "بی‌نام"}], "overlays": []})
    with pytest.raises(ArchitectureRegistryError, match="missing an id"):
        load_personas(tmp_path)


def test_missing_registry_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ArchitectureRegistryError, match="not found"):
        load_personas(tmp_path)


def test_journey_rows_for_entry_page_matches_scalar_and_list_entries(tmp_path: Path) -> None:
    _write(tmp_path, "persona-journey-matrix-v1.yaml", {
        "records": [
            {"persona_or_situation": "PERSONA-001", "entry_page": "/services/"},
            {"persona_or_situation": "PERSONA-005", "entry_page": ["/solutions/industrial-b2b/", "/corporate-web-design/"]},
        ]
    })
    matches = journey_rows_for_entry_page("/corporate-web-design/", tmp_path)
    assert len(matches) == 1
    assert matches[0]["persona_or_situation"] == "PERSONA-005"


# --- Real, materialized Red Umbrella registry ---

def test_real_persona_registry_has_six_core_personas_and_three_overlays() -> None:
    core, overlays = load_personas(REAL_ROOT)
    assert len(core) == 6
    assert len(overlays) == 3
    assert all(p.evidence_strength for p in core)


def test_real_registry_status_is_marked_provisional() -> None:
    raw = yaml.safe_load((REAL_ROOT / "persona-registry-v1.yaml").read_text(encoding="utf-8"))
    assert raw["status"] == "desk_validated_field_provisional"


def test_real_buying_situations_load() -> None:
    situations = load_buying_situations(REAL_ROOT)
    assert len(situations) == 9


def test_real_journey_matrix_loads_and_is_queryable() -> None:
    rows = load_journey_matrix(REAL_ROOT)
    assert len(rows) == 15
    investment_rows = journey_rows_for_entry_page("/investment/", REAL_ROOT)
    assert len(investment_rows) == 1
    assert investment_rows[0]["persona_or_situation"] == "PERSONA-006"


def test_real_behavioral_guardrails_load() -> None:
    guardrails = load_behavioral_guardrails(REAL_ROOT)
    assert len(guardrails) == 9
    assert all("forbidden_use" in g for g in guardrails)


def test_real_pricing_model_loads() -> None:
    model = load_pricing_presentation_model(REAL_ROOT)
    assert len(model["records"]) == 7
