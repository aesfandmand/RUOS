"""Load the Red Umbrella architecture v2.1 registries.

These registries are the machine-readable materialization of the owner's
locked architecture workbook (``11-projects/red-umbrella/registries/``).
They are the single source of truth ``page_selector`` reads to decide what
to build next — nothing here invents a URL, a priority, or a status that
is not already recorded in one of the YAML files.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

DEFAULT_REGISTRY_ROOT = Path(__file__).resolve().parents[2] / "11-projects/red-umbrella/registries"


class ArchitectureRegistryError(ValueError):
    """Raised when a registry file is missing or not internally consistent."""


def _load_yaml(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise ArchitectureRegistryError(f"Registry file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ArchitectureRegistryError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(data, Mapping):
        raise ArchitectureRegistryError(f"{path} must contain a mapping at the top level")
    return data


def _tuple_field(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = row.get(key)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ArchitectureRegistryError(f"Field '{key}' must be a list, got {type(value).__name__}")
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class EntityRecord:
    id: str
    parent_id: str | None
    layer: str | None
    name_fa: str | None
    name_en: str | None
    entity_type: str | None
    page_type: str | None
    page_level: str | None
    canonical_owner: str | None
    commercial_status: str | None
    publication_status: str | None
    indexability: str | None
    url_candidate: str | None
    url_status: str | None
    navigation: str | None
    primary_role: str | None
    dominant_intent: str | None
    main_relations: tuple[str, ...]
    knowledge_relation: str | None
    note: str | None


@dataclass(frozen=True)
class ServiceRecord:
    id: str
    family: str | None
    subgroup: str | None
    name: str | None
    entity_type: str | None
    page_level: str | None
    canonical_owner: str | None
    commercial_status: str | None
    publication: str | None
    research_decision: str | None
    display_contexts: tuple[str, ...]
    note: str | None


@dataclass(frozen=True)
class StructureRecord:
    id: str
    name_fa: str
    family: str
    context: str | None
    url: str
    route: str | None
    orientation: str | None
    dimensions: str | None
    face_count: str | None
    mounting: str | None


def _entity_from_row(row: Mapping[str, Any]) -> EntityRecord:
    entity_id = row.get("id")
    if not entity_id:
        raise ArchitectureRegistryError(f"Entity record is missing an id: {row}")
    return EntityRecord(
        id=str(entity_id),
        parent_id=row.get("parent_id"),
        layer=row.get("layer"),
        name_fa=row.get("name_fa"),
        name_en=row.get("name_en"),
        entity_type=row.get("entity_type"),
        page_type=row.get("page_type"),
        page_level=row.get("page_level"),
        canonical_owner=row.get("canonical_owner"),
        commercial_status=row.get("commercial_status"),
        publication_status=row.get("publication_status"),
        indexability=row.get("indexability"),
        url_candidate=row.get("url_candidate"),
        url_status=row.get("url_status"),
        navigation=row.get("navigation"),
        primary_role=row.get("primary_role"),
        dominant_intent=row.get("dominant_intent"),
        main_relations=_tuple_field(row, "main_relations"),
        knowledge_relation=row.get("knowledge_relation"),
        note=row.get("note"),
    )


def _service_from_row(row: Mapping[str, Any]) -> ServiceRecord:
    service_id = row.get("id")
    if not service_id:
        raise ArchitectureRegistryError(f"Service record is missing an id: {row}")
    return ServiceRecord(
        id=str(service_id),
        family=row.get("family"),
        subgroup=row.get("subgroup"),
        name=row.get("name"),
        entity_type=row.get("entity_type"),
        page_level=row.get("page_level"),
        canonical_owner=row.get("canonical_owner"),
        commercial_status=row.get("commercial_status"),
        publication=row.get("publication"),
        research_decision=row.get("research_decision"),
        display_contexts=_tuple_field(row, "display_contexts"),
        note=row.get("note"),
    )


def _structure_from_row(row: Mapping[str, Any]) -> StructureRecord:
    structure_id = row.get("id")
    url = row.get("url")
    if not structure_id or not url:
        raise ArchitectureRegistryError(f"Structure record is missing id or url: {row}")
    return StructureRecord(
        id=str(structure_id),
        name_fa=str(row.get("name_fa", "")),
        family=str(row.get("family", "")),
        context=row.get("context"),
        url=str(url),
        route=row.get("route"),
        orientation=row.get("orientation"),
        dimensions=row.get("dimensions"),
        face_count=row.get("face_count"),
        mounting=row.get("mounting"),
    )


def load_entities(root: Path | None = None) -> tuple[EntityRecord, ...]:
    root = root or DEFAULT_REGISTRY_ROOT
    data = _load_yaml(root / "architecture-entity-registry-v2.1.yaml")
    return tuple(_entity_from_row(row) for row in data.get("records", []))


def load_services(root: Path | None = None) -> tuple[ServiceRecord, ...]:
    root = root or DEFAULT_REGISTRY_ROOT
    data = _load_yaml(root / "service-landing-registry-v2.1.yaml")
    return tuple(_service_from_row(row) for row in data.get("records", []))


def load_structures(root: Path | None = None) -> tuple[StructureRecord, ...]:
    root = root or DEFAULT_REGISTRY_ROOT
    data = _load_yaml(root / "structure-page-registry-v2.1.yaml")
    return tuple(_structure_from_row(row) for row in data.get("records", []))
