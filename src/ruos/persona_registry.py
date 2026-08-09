"""Load the Red Umbrella persona/buying-behavior research registries.

These are the machine-readable materialization of the owner-supplied
persona research PDF (``11-projects/red-umbrella/registries/persona-*.yaml``).
Unlike the architecture registry, this data is explicitly
``desk_validated_field_provisional`` — no direct interviews with real
buyers have been run yet. Callers should use it to select hero
messages, evidence sequencing, CTAs and forbidden phrasing for a page's
content, not to fabricate specific claims (numbers, named clients,
guarantees) that still need real evidence from ``live_research``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from .architecture_registry import DEFAULT_REGISTRY_ROOT, ArchitectureRegistryError


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


@dataclass(frozen=True)
class Persona:
    id: str
    name_fa: str
    name_en: str | None
    evidence_strength: str
    central_mental_statement: str | None
    dominant_buying_role: tuple[str, ...]
    contexts: tuple[str, ...]
    profile: Mapping[str, Any]
    is_overlay: bool = False


def _tuple_field(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = row.get(key)
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ArchitectureRegistryError(f"Field '{key}' must be a list, got {type(value).__name__}")
    return tuple(str(item) for item in value)


def _persona_from_row(row: Mapping[str, Any], is_overlay: bool) -> Persona:
    persona_id = row.get("id")
    if not persona_id:
        raise ArchitectureRegistryError(f"Persona record is missing an id: {row}")
    profile = row.get("profile", {}) if not is_overlay else {
        k: v for k, v in row.items()
        if k not in ("id", "name_fa", "name_en", "evidence_strength", "central_mental_statement",
                      "central_question", "dominant_buying_role", "contexts")
    }
    return Persona(
        id=str(persona_id),
        name_fa=str(row.get("name_fa", "")),
        name_en=row.get("name_en"),
        evidence_strength=str(row.get("evidence_strength", "")),
        central_mental_statement=row.get("central_mental_statement") or row.get("central_question"),
        dominant_buying_role=_tuple_field(row, "dominant_buying_role"),
        contexts=_tuple_field(row, "contexts"),
        profile=profile,
        is_overlay=is_overlay,
    )


def load_personas(root: Path | None = None) -> tuple[tuple[Persona, ...], tuple[Persona, ...]]:
    """Return (core_personas, overlays)."""
    root = root or DEFAULT_REGISTRY_ROOT
    data = _load_yaml(root / "persona-registry-v1.yaml")
    core = tuple(_persona_from_row(row, is_overlay=False) for row in data.get("core_personas", []))
    overlays = tuple(_persona_from_row(row, is_overlay=True) for row in data.get("overlays", []))
    return core, overlays


def load_buying_situations(root: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    root = root or DEFAULT_REGISTRY_ROOT
    data = _load_yaml(root / "persona-buying-situations-v1.yaml")
    return tuple(data.get("records", []))


def load_journey_matrix(root: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    root = root or DEFAULT_REGISTRY_ROOT
    data = _load_yaml(root / "persona-journey-matrix-v1.yaml")
    return tuple(data.get("records", []))


def journey_rows_for_entry_page(entry_page: str, root: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    """Rows whose entry_page matches (as a string or inside a list of pages)."""
    matches = []
    for row in load_journey_matrix(root):
        entry = row.get("entry_page")
        if entry == entry_page or (isinstance(entry, list) and entry_page in entry):
            matches.append(row)
    return tuple(matches)


def load_behavioral_guardrails(root: Path | None = None) -> tuple[Mapping[str, Any], ...]:
    root = root or DEFAULT_REGISTRY_ROOT
    data = _load_yaml(root / "behavioral-guardrails-v1.yaml")
    return tuple(data.get("records", []))


def load_pricing_presentation_model(root: Path | None = None) -> Mapping[str, Any]:
    root = root or DEFAULT_REGISTRY_ROOT
    return _load_yaml(root / "pricing-presentation-model-v1.yaml")
