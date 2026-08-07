"""Load and validate the block library that lives in ``blocks/``.

A block is a directory holding a contract (``block.json``), a scoped stylesheet
(``style.css``) and an optional behaviour script (``behavior.js``). Contracts are
JSON rather than YAML so the engine keeps its zero-dependency install.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

DEFAULT_LIBRARY_ROOT = Path(__file__).resolve().parents[2] / "blocks"

ROLES = frozenset({"content", "shell", "foundation"})
SURFACES = frozenset({"dark", "light", "paper", "accent", "none"})
POSITIONS = frozenset({"first", "last", "any"})
SLOT_TYPES = frozenset({"text", "list", "object", "map"})


class BlockRegistryError(ValueError):
    """Raised when the block library on disk is not internally consistent."""


@dataclass(frozen=True)
class Slot:
    name: str
    type: str
    required: bool
    minimum: int | None = None
    maximum: int | None = None


@dataclass(frozen=True)
class BlockContract:
    id: str
    name: Mapping[str, str]
    role: str
    family: str
    surface: str
    composition: str
    serves_intent: tuple[str, ...]
    position: str
    behavior: bool
    slots: tuple[Slot, ...]
    not_after_same_family: bool
    source: Mapping[str, str]
    style: str
    script: str
    markup: str
    assets: tuple[Path, ...]

    def slot(self, name: str) -> Slot | None:
        for slot in self.slots:
            if slot.name == name:
                return slot
        return None

    @property
    def sha256(self) -> str:
        payload = {
            "id": self.id,
            "family": self.family,
            "surface": self.surface,
            "position": self.position,
            "slots": [(s.name, s.type, s.required, s.minimum, s.maximum) for s in self.slots],
            "style": hashlib.sha256(self.style.encode("utf-8")).hexdigest(),
            "script": hashlib.sha256(self.script.encode("utf-8")).hexdigest(),
            "markup": hashlib.sha256(self.markup.encode("utf-8")).hexdigest(),
            "assets": sorted(path.name for path in self.assets),
        }
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BlockLibrary:
    root: Path
    blocks: Mapping[str, BlockContract]

    def get(self, block_id: str) -> BlockContract:
        try:
            return self.blocks[block_id]
        except KeyError as exc:
            available = ", ".join(sorted(self.blocks))
            raise BlockRegistryError(f"Unknown block '{block_id}'. Available: {available}") from exc

    def content_blocks(self) -> tuple[BlockContract, ...]:
        return tuple(sorted(
            (block for block in self.blocks.values() if block.role == "content"),
            key=lambda block: block.id,
        ))

    def by_intent(self, intent: str) -> tuple[BlockContract, ...]:
        return tuple(block for block in self.content_blocks() if intent in block.serves_intent)

    @property
    def sha256(self) -> str:
        joined = "".join(f"{key}:{self.blocks[key].sha256}" for key in sorted(self.blocks))
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _require(mapping: Mapping[str, Any], key: str, block_id: str) -> Any:
    if key not in mapping:
        raise BlockRegistryError(f"Block '{block_id}' contract is missing '{key}'")
    return mapping[key]


def _parse_slots(raw: Any, block_id: str) -> tuple[Slot, ...]:
    if not isinstance(raw, Mapping):
        raise BlockRegistryError(f"Block '{block_id}' slots must be an object")
    slots: list[Slot] = []
    for name, spec in raw.items():
        if not isinstance(spec, Mapping):
            raise BlockRegistryError(f"Block '{block_id}' slot '{name}' must be an object")
        slot_type = str(spec.get("type", ""))
        if slot_type not in SLOT_TYPES:
            raise BlockRegistryError(
                f"Block '{block_id}' slot '{name}' has unsupported type '{slot_type}'"
            )
        minimum = spec.get("min")
        maximum = spec.get("max")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise BlockRegistryError(f"Block '{block_id}' slot '{name}' has min above max")
        slots.append(
            Slot(
                name=name,
                type=slot_type,
                required=bool(spec.get("required", False)),
                minimum=minimum,
                maximum=maximum,
            )
        )
    return tuple(sorted(slots, key=lambda slot: slot.name))


def _load_contract(directory: Path) -> BlockContract:
    block_id = directory.name
    contract_path = directory / "block.json"
    if not contract_path.is_file():
        raise BlockRegistryError(f"Block '{block_id}' has no block.json")
    try:
        raw = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BlockRegistryError(f"Block '{block_id}' contract is invalid JSON: {exc}") from exc

    declared_id = _require(raw, "id", block_id)
    if declared_id != block_id:
        raise BlockRegistryError(
            f"Block directory '{block_id}' declares mismatched id '{declared_id}'"
        )

    role = str(_require(raw, "role", block_id))
    if role not in ROLES:
        raise BlockRegistryError(f"Block '{block_id}' has unsupported role '{role}'")
    surface = str(_require(raw, "surface", block_id))
    if surface not in SURFACES:
        raise BlockRegistryError(f"Block '{block_id}' has unsupported surface '{surface}'")
    position = str(raw.get("position", "any"))
    if position not in POSITIONS:
        raise BlockRegistryError(f"Block '{block_id}' has unsupported position '{position}'")

    style_path = directory / "style.css"
    if not style_path.is_file():
        raise BlockRegistryError(f"Block '{block_id}' has no style.css")
    style = style_path.read_text(encoding="utf-8").strip()
    if not style:
        raise BlockRegistryError(f"Block '{block_id}' has an empty stylesheet")

    script_path = directory / "behavior.js"
    behavior = bool(raw.get("behavior", False))
    if behavior and not script_path.is_file():
        raise BlockRegistryError(f"Block '{block_id}' declares behavior but has no behavior.js")
    if script_path.is_file() and not behavior:
        raise BlockRegistryError(f"Block '{block_id}' ships behavior.js without declaring behavior")
    script = script_path.read_text(encoding="utf-8").strip() if behavior else ""

    markup_path = directory / "markup.html"
    if role == "foundation":
        if markup_path.is_file():
            raise BlockRegistryError(f"Foundation block '{block_id}' must not ship markup")
        markup = ""
    else:
        if not markup_path.is_file():
            raise BlockRegistryError(f"Block '{block_id}' has no markup.html")
        markup = markup_path.read_text(encoding="utf-8").strip()
        if not markup:
            raise BlockRegistryError(f"Block '{block_id}' has an empty markup template")

    asset_dir = directory / "assets"
    assets = tuple(sorted(p for p in asset_dir.iterdir() if p.is_file())) \
        if asset_dir.is_dir() else ()

    adjacency = raw.get("adjacency", {})
    if not isinstance(adjacency, Mapping):
        raise BlockRegistryError(f"Block '{block_id}' adjacency must be an object")

    return BlockContract(
        id=block_id,
        name=MappingProxyType(dict(_require(raw, "name", block_id))),
        role=role,
        family=str(_require(raw, "family", block_id)),
        surface=surface,
        composition=str(_require(raw, "composition", block_id)),
        serves_intent=tuple(raw.get("serves_intent", [])),
        position=position,
        behavior=behavior,
        slots=_parse_slots(raw.get("slots", {}), block_id),
        not_after_same_family=bool(adjacency.get("not_after_same_family", False)),
        source=MappingProxyType(dict(raw.get("source", {}))),
        style=style,
        script=script,
        markup=markup,
        assets=assets,
    )


def load_library(root: Path | None = None) -> BlockLibrary:
    """Read every block directory under ``root`` and validate the whole set."""
    library_root = Path(root) if root is not None else DEFAULT_LIBRARY_ROOT
    if not library_root.is_dir():
        raise BlockRegistryError(f"Block library not found at {library_root}")

    blocks: dict[str, BlockContract] = {}
    for directory in sorted(library_root.iterdir()):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        contract = _load_contract(directory)
        blocks[contract.id] = contract

    if not blocks:
        raise BlockRegistryError(f"Block library at {library_root} is empty")
    for required in ("_tokens", "_foundation"):
        if required not in blocks:
            raise BlockRegistryError(f"Block library is missing the '{required}' foundation")
    if not any(block.role == "content" for block in blocks.values()):
        raise BlockRegistryError("Block library defines no content blocks")

    return BlockLibrary(root=library_root, blocks=MappingProxyType(blocks))
