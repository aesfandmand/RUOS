from pathlib import Path

import pytest

from ruos.architecture_registry import StructureRecord
from ruos.block_composer import compose_page
from ruos.block_page import load_page_spec, render_page
from ruos.block_registry import load_library
from ruos.structure_detail_spec import StructureDetailSpecError, build_structure_detail_spec

SHELL = load_page_spec(Path("pages/blocks/urban-investment.json"))["shell"]


def _structure(**overrides) -> StructureRecord:
    base = dict(
        id="STR-TEST", name_fa="بیلبورد آزمایشی", family="بیلبورد", context="outdoor",
        url="/structures/test-billboard/", route="outdoor_purchase",
        orientation="vertical", dimensions="5x10", face_count=None, mounting=None,
    )
    base.update(overrides)
    return StructureRecord(**base)


def test_a_structure_with_enough_attributes_builds_a_composable_spec() -> None:
    spec = build_structure_detail_spec(_structure(), SHELL)
    assert spec["slug"] == "test-billboard"
    page = render_page(spec, load_library())
    assert [b.block_id for b in page.composed.blocks] == ["structure-hero", "structure-specs", "review-gate"]


def test_a_structure_with_fewer_than_three_attributes_is_rejected_not_padded() -> None:
    sparse = _structure(context=None, orientation=None, dimensions=None)
    with pytest.raises(StructureDetailSpecError, match="not enough"):
        build_structure_detail_spec(sparse, SHELL)


def test_dimension_label_and_diagram_are_derived_from_real_dimensions() -> None:
    spec = build_structure_detail_spec(_structure(dimensions="180x120cm"), SHELL)
    hero_data = spec["blocks"][0]["data"]
    assert hero_data["dimension_label"] == "180×120 سانتی‌متر"
    assert hero_data["diagram"]["ratio"] == "180.0 / 120.0"


def test_a_structure_with_no_dimensions_gets_no_fabricated_diagram() -> None:
    spec = build_structure_detail_spec(_structure(dimensions=None, face_count="one_or_two"), SHELL)
    hero_data = spec["blocks"][0]["data"]
    assert hero_data["dimension_label"] is None
    assert hero_data["diagram"] is None


def test_a_structure_with_a_researched_journey_row_uses_its_real_copy() -> None:
    spec = build_structure_detail_spec(
        _structure(url="/structures/billboard-vertical-5x10/"), SHELL,
    )
    hero_data = spec["blocks"][0]["data"]
    review_data = spec["blocks"][2]["data"]
    assert "بیلبورد عمودی" in hero_data["lead"]
    assert review_data["primary"]["label"] == "RFQ فنی"


def test_a_structure_with_no_journey_row_falls_back_to_a_generic_cta() -> None:
    spec = build_structure_detail_spec(_structure(url="/structures/no-journey-row/"), SHELL)
    review_data = spec["blocks"][2]["data"]
    assert review_data["primary"]["label"] == "درخواست استعلام فنی"


def test_all_fourteen_composable_real_structures_actually_compose() -> None:
    from ruos.architecture_registry import load_structures

    composed_count = 0
    for structure in load_structures():
        try:
            spec = build_structure_detail_spec(structure, SHELL)
        except StructureDetailSpecError:
            continue
        page = render_page(spec, load_library())
        assert page.composed.blocks
        composed_count += 1
    assert composed_count == 14
