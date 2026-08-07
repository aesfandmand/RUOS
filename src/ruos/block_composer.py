"""Compose a page from the block library.

The composer is the piece that turns a library into a page: it validates a
declared block sequence against the contracts, enforces the composition rules
that keep a long page from degenerating into repeated card grids, and assembles
only the CSS and JavaScript the chosen blocks actually need.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .block_library import render_block
from .block_registry import BlockContract, BlockLibrary

# A page may not run more than this many same-surface sections back to back.
MAX_CONSECUTIVE_SURFACE = 2

# A grid of repeated cards is the fallback shape: it carries no argument of its
# own, so a page built mostly out of them reads as a list, not a designed page.
# These caps exist because labelling blocks with different families was not
# enough — six card grids in a row all passed the family rule.
MAX_CARD_GRIDS_PER_PAGE = 2
CARD_LAYOUTS = frozenset({"card-grid"})


class BlockCompositionError(ValueError):
    """Raised when a requested block sequence violates the composition contract."""


@dataclass(frozen=True)
class PlacedBlock:
    index: int
    block_id: str
    section_id: str
    family: str
    surface: str
    html: str

    def payload(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "block": self.block_id,
            "section_id": self.section_id,
            "family": self.family,
            "surface": self.surface,
        }


@dataclass(frozen=True)
class ComposedPage:
    slug: str
    blocks: tuple[PlacedBlock, ...]
    body: str
    css: str
    script: str
    used_blocks: tuple[str, ...]

    def manifest(self) -> dict[str, Any]:
        return {
            "page_slug": self.slug,
            "sequence": [block.payload() for block in self.blocks],
            "used_blocks": list(self.used_blocks),
            "surfaces": [block.surface for block in self.blocks],
            "families": [block.family for block in self.blocks],
            "css_sha256": hashlib.sha256(self.css.encode("utf-8")).hexdigest(),
            "script_sha256": hashlib.sha256(self.script.encode("utf-8")).hexdigest(),
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.manifest(), ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_slots(contract: BlockContract, data: Mapping[str, Any]) -> None:
    for slot in contract.slots:
        value = data.get(slot.name)
        present = value not in (None, "", [], {})
        if slot.required and not present:
            raise BlockCompositionError(
                f"Block '{contract.id}' is missing required slot '{slot.name}'"
            )
        if not present:
            continue
        if slot.type == "list":
            if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
                raise BlockCompositionError(
                    f"Block '{contract.id}' slot '{slot.name}' must be a list"
                )
            if slot.minimum is not None and len(value) < slot.minimum:
                raise BlockCompositionError(
                    f"Block '{contract.id}' slot '{slot.name}' needs at least "
                    f"{slot.minimum} entries, got {len(value)}"
                )
            if slot.maximum is not None and len(value) > slot.maximum:
                raise BlockCompositionError(
                    f"Block '{contract.id}' slot '{slot.name}' accepts at most "
                    f"{slot.maximum} entries, got {len(value)}"
                )
        elif slot.type in {"object", "map"} and not isinstance(value, Mapping):
            raise BlockCompositionError(
                f"Block '{contract.id}' slot '{slot.name}' must be an object"
            )
        elif slot.type == "text" and not isinstance(value, str):
            raise BlockCompositionError(
                f"Block '{contract.id}' slot '{slot.name}' must be text"
            )

    unknown = sorted(set(data) - {slot.name for slot in contract.slots})
    if unknown:
        raise BlockCompositionError(
            f"Block '{contract.id}' received unknown slots: {', '.join(unknown)}"
        )


def _validate_sequence(contracts: Sequence[BlockContract]) -> None:
    if not contracts:
        raise BlockCompositionError("A page needs at least one content block")

    first, last = contracts[0], contracts[-1]
    if first.position != "first":
        raise BlockCompositionError(
            f"A page must open with a block declaring position 'first'; got '{first.id}'"
        )
    if last.position != "last":
        raise BlockCompositionError(
            f"A page must close with a block declaring position 'last'; got '{last.id}'"
        )
    for middle in contracts[1:-1]:
        if middle.position != "any":
            raise BlockCompositionError(
                f"Block '{middle.id}' is pinned to position '{middle.position}' "
                "and cannot sit in the middle of a page"
            )

    # The anti-repetition rule: no two neighbours from the same composition family.
    for previous, current in zip(contracts, contracts[1:]):
        if current.not_after_same_family and previous.family == current.family:
            raise BlockCompositionError(
                f"'{current.id}' cannot follow '{previous.id}': both are "
                f"'{current.family}' blocks, which reads as a repeated pattern"
            )

    # Shape, not meaning: two blocks may mean different things and still land as
    # the same repeated grid. This is the rule the family check could not make.
    for previous, current in zip(contracts, contracts[1:]):
        if previous.layout == current.layout and current.layout != "editorial":
            raise BlockCompositionError(
                f"'{current.id}' cannot follow '{previous.id}': both use the "
                f"'{current.layout}' layout, so the two sections read as one "
                "repeated pattern"
            )

    card_blocks = [c.id for c in contracts if c.layout in CARD_LAYOUTS]
    if len(card_blocks) > MAX_CARD_GRIDS_PER_PAGE:
        raise BlockCompositionError(
            f"{len(card_blocks)} card-grid sections on one page "
            f"({', '.join(card_blocks)}); at most {MAX_CARD_GRIDS_PER_PAGE} are "
            "allowed before the page reads as a list of cards"
        )

    # Visual rhythm: never let the eye cross more than two identical surfaces in a row.
    run_surface, run_length = None, 0
    for contract in contracts:
        if contract.surface == run_surface:
            run_length += 1
        else:
            run_surface, run_length = contract.surface, 1
        if run_length > MAX_CONSECUTIVE_SURFACE:
            raise BlockCompositionError(
                f"More than {MAX_CONSECUTIVE_SURFACE} consecutive '{run_surface}' "
                f"surfaces around '{contract.id}' flattens the page rhythm"
            )


def compose_page(
    library: BlockLibrary,
    slug: str,
    sequence: Sequence[Mapping[str, Any]],
    shell: Mapping[str, Any] | None = None,
) -> ComposedPage:
    """Validate and render a declared block sequence into one page."""
    contracts: list[BlockContract] = []
    section_ids: set[str] = set()

    for entry in sequence:
        block_id = str(entry.get("block", ""))
        contract = library.get(block_id)
        if contract.role != "content":
            raise BlockCompositionError(
                f"Block '{block_id}' has role '{contract.role}' and cannot be placed "
                "in the page sequence"
            )
        section_id = str(entry.get("id", ""))
        if section_id and section_id in section_ids:
            raise BlockCompositionError(f"Duplicate section id '{section_id}'")
        section_ids.add(section_id)
        _validate_slots(contract, entry.get("data", {}))
        contracts.append(contract)

    _validate_sequence(contracts)

    placed: list[PlacedBlock] = []
    for index, (entry, contract) in enumerate(zip(sequence, contracts), start=1):
        section_id = str(entry.get("id", ""))
        placed.append(
            PlacedBlock(
                index=index,
                block_id=contract.id,
                section_id=section_id,
                family=contract.family,
                surface=contract.surface,
                html=render_block(contract, section_id, entry.get("data", {})),
            )
        )

    shell = shell or {}
    header = shell.get("site-header")
    footer = shell.get("site-footer")
    jump_nav = shell.get("bottom-nav")
    sheet = shell.get("contact-sheet")

    # Foundation first, then shell, then content blocks in the order they appear:
    # the cascade must follow the document.
    used: list[str] = ["_tokens", "_foundation"]
    for shell_id, shell_data in (("site-header", header), ("bottom-nav", jump_nav),
                                 ("contact-sheet", sheet), ("site-footer", footer)):
        if shell_data is not None:
            used.append(shell_id)
    for block in placed:
        if block.block_id not in used:
            used.append(block.block_id)

    css = "\n".join(library.get(block_id).style for block_id in used)
    scripts = [library.get(block_id).script for block_id in used
               if library.get(block_id).behavior]
    script = "\n".join(part for part in scripts if part)

    # Document order: header, the page's own sections, then the shell furniture
    # that closes the page or overlays it.
    body_parts: list[str] = []
    if header is not None:
        body_parts.append(render_block(library.get("site-header"), "", header))
    body_parts.append('<main id="main">' + "".join(block.html for block in placed) + "</main>")
    if footer is not None:
        body_parts.append(render_block(library.get("site-footer"), "", footer))
    if jump_nav is not None:
        body_parts.append(render_block(library.get("bottom-nav"), "", jump_nav))
    if sheet is not None:
        body_parts.append(render_block(library.get("contact-sheet"), "", sheet))

    return ComposedPage(
        slug=slug,
        blocks=tuple(placed),
        body="".join(body_parts),
        css=css,
        script=script,
        used_blocks=tuple(used),
    )
