import copy
import json
from pathlib import Path

import pytest

from ruos.block_composer import BlockCompositionError, compose_page
from ruos.block_page import load_page_spec, render_page
from ruos.block_registry import load_library

SPEC_PATH = Path("pages/blocks/urban-investment.json")


def _spec() -> dict:
    return copy.deepcopy(load_page_spec(SPEC_PATH))


def _entry(spec: dict, block_id: str) -> dict:
    return next(entry for entry in spec["blocks"] if entry["block"] == block_id)


def test_reference_page_composes_cleanly() -> None:
    spec = _spec()
    composed = compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])
    assert [block.block_id for block in composed.blocks] == [
        "hero-scroll-scene", "opportunity-section", "paths-scroll", "products-section",
        "contract-section", "assessment-section", "proof-section-final",
        "process-section-final", "media-section-final", "audience-section-final",
        "knowledge-section-final", "faq-section-final", "review-gate",
    ]
    # The foundation must be first in the cascade, before any block styles.
    assert composed.used_blocks[:2] == ("_tokens", "_foundation")


def test_composition_is_deterministic() -> None:
    spec = _spec()
    library = load_library()
    first = compose_page(library, spec["slug"], spec["blocks"], spec["shell"])
    second = compose_page(library, spec["slug"], spec["blocks"], spec["shell"])
    assert first.sha256 == second.sha256
    assert first.body == second.body


def test_only_the_used_blocks_contribute_css() -> None:
    spec = _spec()
    spec["blocks"] = [entry for entry in spec["blocks"]
                      if entry["block"] not in {"media-section-final", "process-section-final", "faq-section-final"}]
    composed = compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])
    assert "media-grid" not in composed.css
    assert "process-timeline" not in composed.css
    assert "faq-list" not in composed.css
    assert "hero-scroll" in composed.css


def test_two_blocks_of_the_same_family_may_not_be_adjacent() -> None:
    """The anti-repetition rule: this is what stops a page becoming card grids."""
    spec = _spec()
    catalog = _entry(spec, "products-section")
    twin = copy.deepcopy(catalog)
    twin["id"] = "products-2"
    index = spec["blocks"].index(catalog)
    spec["blocks"].insert(index + 1, twin)
    with pytest.raises(BlockCompositionError, match="repeated pattern"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_more_than_two_identical_surfaces_in_a_row_is_rejected() -> None:
    spec = _spec()
    # products(light) -> assessment(light) -> audiences(light) is three in a row.
    spec["blocks"] = [
        _entry(spec, "hero-scroll-scene"),
        _entry(spec, "products-section"),
        _entry(spec, "assessment-section"),
        _entry(spec, "audience-section-final"),
        _entry(spec, "review-gate"),
    ]
    with pytest.raises(BlockCompositionError, match="consecutive"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_page_must_open_with_a_hero_and_close_with_a_conversion() -> None:
    spec = _spec()
    without_hero = spec["blocks"][1:]
    with pytest.raises(BlockCompositionError, match="position 'first'"):
        compose_page(load_library(), spec["slug"], without_hero, spec["shell"])

    without_closing = spec["blocks"][:-1]
    with pytest.raises(BlockCompositionError, match="position 'last'"):
        compose_page(load_library(), spec["slug"], without_closing, spec["shell"])


def test_a_pinned_block_cannot_sit_in_the_middle() -> None:
    spec = _spec()
    second_hero = copy.deepcopy(_entry(spec, "hero-scroll-scene"))
    second_hero["id"] = "hero-b"
    spec["blocks"].insert(3, second_hero)
    with pytest.raises(BlockCompositionError, match="pinned to position"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_missing_required_slot_is_rejected() -> None:
    spec = _spec()
    _entry(spec, "opportunity-section")["data"].pop("title")
    with pytest.raises(BlockCompositionError, match="required slot 'title'"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_list_slot_bounds_are_enforced() -> None:
    spec = _spec()
    _entry(spec, "opportunity-section")["data"]["stories"] = [{"title": "x"}]
    with pytest.raises(BlockCompositionError, match="at least 3 entries"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_unknown_slot_is_rejected() -> None:
    spec = _spec()
    _entry(spec, "faq-section-final")["data"]["subtitle"] = "unexpected"
    with pytest.raises(BlockCompositionError, match="unknown slots: subtitle"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_shell_blocks_cannot_be_placed_in_the_page_sequence() -> None:
    spec = _spec()
    spec["blocks"].insert(1, {"block": "site-footer", "id": "footer", "data": {}})
    with pytest.raises(BlockCompositionError, match="role 'shell'"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_duplicate_section_ids_are_rejected() -> None:
    spec = _spec()
    _entry(spec, "faq-section-final")["id"] = "process"
    with pytest.raises(BlockCompositionError, match="Duplicate section id"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_rendered_document_carries_one_h1_and_a_schema_graph() -> None:
    page = render_page(_spec())
    assert page.html.count("<h1") == 1
    payload = page.html.split('<script type="application/ld+json">')[1].split("</script>")[0]
    graph = json.loads(payload)["@graph"]
    assert [node["@type"] for node in graph] == ["WebPage", "ItemList", "FAQPage"]


def test_page_content_is_escaped() -> None:
    spec = _spec()
    _entry(spec, "audience-section-final")["data"]["title"] = '<img src=x onerror="alert(1)">'
    page = render_page(spec)
    assert "<img src=x" not in page.html
    assert "&lt;img src=x" in page.html
