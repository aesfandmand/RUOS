import copy
import json
from pathlib import Path

import pytest

from ruos.block_composer import BlockCompositionError, compose_page
from ruos.block_page import load_page_spec, render_page
from ruos.block_registry import load_library

SPEC_PATH = Path("pages/blocks/structures.json")


def _spec() -> dict:
    return copy.deepcopy(load_page_spec(SPEC_PATH))


def _entry(spec: dict, block_id: str) -> dict:
    return next(entry for entry in spec["blocks"] if entry["block"] == block_id)


def test_reference_page_composes_cleanly() -> None:
    spec = _spec()
    composed = compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])
    assert [block.block_id for block in composed.blocks] == [
        "hero-split-scene", "answer-statement", "index-strip", "sticky-narrative",
        "decision-finder", "family-stack", "comparison-table", "process-line",
        "faq-grid", "closing-band",
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
                      if entry["block"] not in {"comparison-table", "process-line", "faq-grid"}]
    composed = compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])
    assert "sp-table-wrap" not in composed.css
    assert "sp-process-line" not in composed.css
    assert "sp-faq" not in composed.css
    assert "sp-hero" in composed.css


def test_two_blocks_of_the_same_family_may_not_be_adjacent() -> None:
    """The anti-repetition rule: this is what stops a page becoming card grids."""
    spec = _spec()
    catalog = _entry(spec, "family-stack")
    twin = copy.deepcopy(catalog)
    twin["id"] = "structure-catalog-2"
    index = spec["blocks"].index(catalog)
    spec["blocks"].insert(index + 1, twin)
    with pytest.raises(BlockCompositionError, match="repeated pattern"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_more_than_two_identical_surfaces_in_a_row_is_rejected() -> None:
    spec = _spec()
    faq = _entry(spec, "faq-grid")
    extra = copy.deepcopy(_entry(spec, "comparison-table"))
    extra["id"] = "comparison-2"
    # comparison(light) -> faq(light) -> comparison(light) is three light surfaces.
    spec["blocks"] = [
        _entry(spec, "hero-split-scene"),
        _entry(spec, "comparison-table"),
        faq,
        extra,
        _entry(spec, "closing-band"),
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
    second_hero = copy.deepcopy(_entry(spec, "hero-split-scene"))
    second_hero["id"] = "hero-2"
    spec["blocks"].insert(3, second_hero)
    with pytest.raises(BlockCompositionError, match="pinned to position"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_missing_required_slot_is_rejected() -> None:
    spec = _spec()
    _entry(spec, "sticky-narrative")["data"].pop("title")
    with pytest.raises(BlockCompositionError, match="required slot 'title'"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_list_slot_bounds_are_enforced() -> None:
    spec = _spec()
    _entry(spec, "sticky-narrative")["data"]["steps"] = [{"title": "x", "body": "y"}]
    with pytest.raises(BlockCompositionError, match="at least 3 entries"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_unknown_slot_is_rejected() -> None:
    spec = _spec()
    _entry(spec, "faq-grid")["data"]["subtitle"] = "unexpected"
    with pytest.raises(BlockCompositionError, match="unknown slots: subtitle"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_shell_blocks_cannot_be_placed_in_the_page_sequence() -> None:
    spec = _spec()
    spec["blocks"].insert(1, {"block": "site-footer", "id": "footer", "data": {}})
    with pytest.raises(BlockCompositionError, match="role 'shell'"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_duplicate_section_ids_are_rejected() -> None:
    spec = _spec()
    _entry(spec, "faq-grid")["id"] = "process"
    with pytest.raises(BlockCompositionError, match="Duplicate section id"):
        compose_page(load_library(), spec["slug"], spec["blocks"], spec["shell"])


def test_rendered_document_carries_one_h1_and_a_schema_graph() -> None:
    page = render_page(_spec())
    assert page.html.count("<h1>") == 1
    payload = page.html.split('<script type="application/ld+json">')[1].split("</script>")[0]
    graph = json.loads(payload)["@graph"]
    assert [node["@type"] for node in graph] == ["WebPage", "ItemList", "FAQPage"]


def test_finder_outcomes_must_cover_the_default_combination() -> None:
    spec = _spec()
    finder = _entry(spec, "decision-finder")
    finder["data"]["outcomes"] = {"indoor|pause|buy": finder["data"]["outcomes"]["indoor|pause|buy"]}
    with pytest.raises(Exception, match="default combination"):
        render_page(spec)


def test_comparison_rows_must_match_the_declared_columns() -> None:
    spec = _spec()
    _entry(spec, "comparison-table")["data"]["rows"][0]["cells"].pop()
    with pytest.raises(Exception, match="declares 5 data columns"):
        render_page(spec)


def test_page_content_is_escaped() -> None:
    spec = _spec()
    _entry(spec, "answer-statement")["data"]["title"] = '<img src=x onerror="alert(1)">'
    page = render_page(spec)
    assert "<img src=x" not in page.html
    assert "&lt;img src=x" in page.html
