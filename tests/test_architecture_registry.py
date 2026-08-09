from pathlib import Path

import pytest
import yaml

from ruos.architecture_registry import (
    ArchitectureRegistryError,
    load_entities,
    load_services,
    load_structures,
)


def _write(root: Path, filename: str, payload: dict) -> None:
    (root / filename).write_text(yaml.dump(payload, allow_unicode=True), encoding="utf-8")


def test_loads_entities_with_list_and_scalar_fields(tmp_path: Path) -> None:
    _write(tmp_path, "architecture-entity-registry-v2.1.yaml", {
        "records": [{
            "id": "CORE-001",
            "parent_id": None,
            "name_fa": "خانه",
            "name_en": "Home",
            "commercial_status": "ACTIVE",
            "url_candidate": "/",
            "url_status": "KEEP",
            "main_relations": ["Services", "Projects"],
        }]
    })
    entities = load_entities(tmp_path)
    assert len(entities) == 1
    assert entities[0].id == "CORE-001"
    assert entities[0].main_relations == ("Services", "Projects")
    assert entities[0].parent_id is None


def test_entity_without_id_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "architecture-entity-registry-v2.1.yaml", {"records": [{"name_fa": "بی‌نام"}]})
    with pytest.raises(ArchitectureRegistryError, match="missing an id"):
        load_entities(tmp_path)


def test_missing_registry_file_is_a_clear_error(tmp_path: Path) -> None:
    with pytest.raises(ArchitectureRegistryError, match="not found"):
        load_entities(tmp_path)


def test_loads_services_with_display_contexts(tmp_path: Path) -> None:
    _write(tmp_path, "service-landing-registry-v2.1.yaml", {
        "records": [{
            "id": "WEB-002",
            "family": "دیجیتال مارکتینگ",
            "commercial_status": "ACTIVE",
            "research_decision": "CONFIRMED HIGH",
            "display_contexts": ["B2B Solution", "Portfolio"],
        }]
    })
    services = load_services(tmp_path)
    assert services[0].display_contexts == ("B2B Solution", "Portfolio")
    assert services[0].research_decision == "CONFIRMED HIGH"


def test_loads_structures(tmp_path: Path) -> None:
    _write(tmp_path, "structure-page-registry-v2.1.yaml", {
        "records": [{
            "id": "STR-001",
            "name_fa": "بیلبورد عمودی ۵×۱۰",
            "family": "بیلبورد",
            "url": "/structures/billboard-vertical-5x10/",
            "route": "outdoor_purchase",
        }]
    })
    structures = load_structures(tmp_path)
    assert structures[0].url == "/structures/billboard-vertical-5x10/"


def test_a_list_field_that_is_actually_a_scalar_is_rejected(tmp_path: Path) -> None:
    _write(tmp_path, "architecture-entity-registry-v2.1.yaml", {
        "records": [{"id": "CORE-001", "main_relations": "Services"}]
    })
    with pytest.raises(ArchitectureRegistryError, match="must be a list"):
        load_entities(tmp_path)
