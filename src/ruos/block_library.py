"""Render a block from its own markup template.

Blocks used to be rendered by hand-written Python generators, one per block.
They are now rendered from the ``markup.html`` that lives beside each block's
stylesheet, so adding a composition is a matter of adding a folder rather than
editing this module. Escaping is handled centrally by the template engine.
"""
from __future__ import annotations

from typing import Any, Mapping

from .block_registry import BlockContract
from .block_template import TemplateError, render_template


class BlockRenderError(ValueError):
    """Raised when a block cannot be rendered from the supplied data."""


def render_block(contract: BlockContract, section_id: str, data: Mapping[str, Any]) -> str:
    if not contract.markup:
        raise BlockRenderError(f"Block '{contract.id}' has no markup to render")
    # `anchor` is supplied by the composer rather than the page author so that a
    # block can label its own heading without the author repeating the id.
    payload = {**data, "anchor": section_id or contract.id}
    try:
        return render_template(contract.markup, payload)
    except TemplateError as exc:
        raise BlockRenderError(f"Block '{contract.id}': {exc}") from exc
