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
    composed_ids = [b.block_id for b in page.composed.blocks]
    assert composed_ids[:2] == ["structure-hero", "structure-specs"]
    assert composed_ids[-2:] == ["faq-section-final", "review-gate"]


def test_a_structure_with_fewer_than_three_attributes_is_rejected_not_padded() -> None:
    sparse = _structure(context=None, orientation=None, dimensions=None)
    with pytest.raises(StructureDetailSpecError, match="not enough"):
        build_structure_detail_spec(sparse, SHELL)


def test_dimension_label_and_diagram_are_derived_from_real_dimensions() -> None:
    spec = build_structure_detail_spec(_structure(dimensions="180x120cm", orientation="horizontal"), SHELL)
    hero_data = spec["blocks"][0]["data"]
    assert hero_data["dimension_label"] == "180×120 سانتی‌متر"
    assert hero_data["diagram"]["ratio"] == "180.0 / 120.0"


def test_a_structure_with_no_dimensions_gets_no_fabricated_diagram() -> None:
    spec = build_structure_detail_spec(_structure(dimensions=None, face_count="one_or_two"), SHELL)
    hero_data = spec["blocks"][0]["data"]
    assert hero_data["dimension_label"] is None
    assert hero_data["diagram"] is None


def test_diagram_shape_follows_orientation_even_when_the_raw_string_disagrees() -> None:
    """Real registry rows exist (STR-002, افقی ۶×۱۲) where the raw 'WxH' string
    alone gives the same ratio as a vertical structure's. The orientation
    field is owner-authored and must win, or a horizontal structure gets
    drawn as a tall portrait box."""
    horizontal = build_structure_detail_spec(
        _structure(dimensions="6x12", orientation="horizontal"), SHELL,
    )
    vertical = build_structure_detail_spec(
        _structure(dimensions="5x10", orientation="vertical"), SHELL,
    )
    horizontal_ratio = horizontal["blocks"][0]["data"]["diagram"]["ratio"]
    vertical_ratio = vertical["blocks"][0]["data"]["diagram"]["ratio"]
    h_width, h_height = (float(part) for part in horizontal_ratio.split(" / "))
    v_width, v_height = (float(part) for part in vertical_ratio.split(" / "))
    assert h_width > h_height
    assert v_height > v_width


def test_a_structure_with_a_researched_journey_row_uses_its_real_copy() -> None:
    spec = build_structure_detail_spec(
        _structure(url="/structures/billboard-vertical-5x10/"), SHELL,
    )
    hero_data = spec["blocks"][0]["data"]
    review_data = spec["blocks"][-1]["data"]
    assert "بیلبورد عمودی" in hero_data["lead"]
    assert review_data["primary"]["label"] == "RFQ فنی"


def test_a_structure_with_no_journey_row_falls_back_to_a_generic_cta() -> None:
    spec = build_structure_detail_spec(_structure(url="/structures/no-journey-row/"), SHELL)
    review_data = spec["blocks"][-1]["data"]
    assert review_data["primary"]["label"] == "درخواست استعلام فنی"


def test_a_structure_with_no_real_photos_gets_no_gallery_block(tmp_path: Path) -> None:
    spec = build_structure_detail_spec(_structure(), SHELL, media_root=tmp_path)
    block_ids = [entry["block"] for entry in spec["blocks"]]
    assert "structure-gallery" not in block_ids
    assert spec["blocks"][0]["data"]["image"] is None
    assert spec["blocks"][0]["data"]["diagram"] is not None


def test_a_structure_with_one_real_photo_becomes_the_hero_image_no_gallery(tmp_path: Path) -> None:
    (tmp_path / "STR-TEST").mkdir()
    (tmp_path / "STR-TEST" / "shot.jpg").write_bytes(b"fake-jpeg-bytes")
    spec = build_structure_detail_spec(_structure(), SHELL, media_root=tmp_path)
    block_ids = [entry["block"] for entry in spec["blocks"]]
    assert "structure-gallery" not in block_ids
    hero_data = spec["blocks"][0]["data"]
    assert hero_data["image"]["src"] == "assets/shot.jpg"
    assert hero_data["diagram"] is None


def test_a_structure_with_two_real_photos_uses_both_in_the_gallery_not_the_hero(tmp_path: Path) -> None:
    """Only 2 photos means reserving one for the hero would leave the gallery
    below its own minimum of 2 — so with exactly 2, the hero falls back to
    the honest diagram and both real photos go into the gallery instead."""
    directory = tmp_path / "STR-TEST"
    directory.mkdir()
    (directory / "a.jpg").write_bytes(b"fake")
    (directory / "b.jpg").write_bytes(b"fake")
    (directory / "notes.txt").write_bytes(b"not an image")
    spec = build_structure_detail_spec(_structure(), SHELL, media_root=tmp_path)
    hero_data = spec["blocks"][0]["data"]
    assert hero_data["image"] is None
    assert hero_data["diagram"] is not None
    gallery = next(entry for entry in spec["blocks"] if entry["block"] == "structure-gallery")
    assert [item["src"] for item in gallery["data"]["items"]] == ["assets/a.jpg", "assets/b.jpg"]
    for item in gallery["data"]["items"]:
        assert item["caption"] == "نمونه نصب واقعی — دیده‌شو"


def test_a_structure_with_three_real_photos_reserves_one_for_the_hero(tmp_path: Path) -> None:
    directory = tmp_path / "STR-TEST"
    directory.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        (directory / name).write_bytes(b"fake")
    spec = build_structure_detail_spec(_structure(), SHELL, media_root=tmp_path)
    hero_data = spec["blocks"][0]["data"]
    assert hero_data["image"]["src"] == "assets/a.jpg"
    gallery = next(entry for entry in spec["blocks"] if entry["block"] == "structure-gallery")
    assert [item["src"] for item in gallery["data"]["items"]] == ["assets/b.jpg", "assets/c.jpg"]
    page = render_page(spec, load_library())
    assert "structure-gallery" in [b.block_id for b in page.composed.blocks]


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
