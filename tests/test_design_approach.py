import json
from pathlib import Path

import pytest

from ruos.block_composer import BlockCompositionError, compose_page
from ruos.block_page import load_page_spec
from ruos.block_registry import load_library
from ruos.design_approach import MATCHED, NOT_YET_DESIGNED, select_design_approach

REFERENCE_SPEC = Path("pages/blocks/urban-investment.json")


def test_a_page_type_with_no_reference_is_reported_honestly() -> None:
    result = select_design_approach("KNOWLEDGE_HUB")
    assert result.status == NOT_YET_DESIGNED
    assert result.approach is None
    assert "KNOWLEDGE_HUB" in result.reason


def test_missing_page_type_is_reported_honestly() -> None:
    result = select_design_approach(None)
    assert result.status == NOT_YET_DESIGNED


def test_investment_hub_matches_the_v16_sequence() -> None:
    result = select_design_approach("INVESTMENT_HUB")
    assert result.status == MATCHED
    assert result.approach is not None
    assert result.approach.block_sequence[0] == "hero-scroll-scene"
    assert result.approach.block_sequence[-1] == "review-gate"


def test_the_hardcoded_sequence_matches_the_actual_reference_spec_on_disk() -> None:
    """Guards against the catalog silently drifting from its source file."""
    spec = json.loads(REFERENCE_SPEC.read_text(encoding="utf-8"))
    on_disk = tuple(entry["block"] for entry in spec["blocks"])
    result = select_design_approach("INVESTMENT_HUB")
    assert result.approach.block_sequence == on_disk


def test_the_matched_sequence_still_fails_composition_as_documented() -> None:
    """The approach is a real reference, not a guarantee it composes today."""
    spec = load_page_spec(REFERENCE_SPEC)
    with pytest.raises(BlockCompositionError, match="repeated pattern"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_structure_detail_matches_and_actually_composes() -> None:
    from ruos.structure_detail_spec import build_product_page_spec
    from ruos.architecture_registry import load_structures
    from ruos.block_page import render_page

    result = select_design_approach("STRUCTURE_DETAIL")
    assert result.status == MATCHED
    assert result.approach.block_sequence == (
        "product-hero", "structure-specs", "faq-section-final", "lead-form",
    )

    shell = load_page_spec(REFERENCE_SPEC)["shell"]
    billboard = next(s for s in load_structures() if s.id == "STR-001")
    spec = build_product_page_spec(billboard, shell)
    page = render_page(spec, load_library())
    composed_ids = [b.block_id for b in page.composed.blocks]
    # The fixed spine must appear, in order; any blocks in between are the
    # conditional cross-reference/cross-sell ones structure_detail_spec adds
    # only when the registry has real data for them.
    spine_positions = [composed_ids.index(block_id) for block_id in result.approach.block_sequence]
    assert spine_positions == sorted(spine_positions)
    assert set(composed_ids) - set(result.approach.block_sequence) <= {
        "structure-gallery", "structure-related", "structure-services",
    }
