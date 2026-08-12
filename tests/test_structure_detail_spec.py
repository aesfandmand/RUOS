from pathlib import Path

import pytest

from ruos.architecture_registry import StructureRecord
from ruos.block_composer import compose_page
from ruos.block_page import load_page_spec, render_page
from ruos.block_registry import load_library
from ruos.structure_detail_spec import (
    StructureDetailSpecError,
    build_product_page_spec,
    build_structure_detail_spec,
)

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
        # Owner-supplied photography needs no provenance/credit caption —
        # see 05-rules/website/red-umbrella-design-model-v1.md §4.
        assert "caption" not in item
        assert item["alt"] == _structure().name_fa


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


def test_default_shell_mega_menu_has_real_identical_family_cards_on_every_page() -> None:
    """The owner asked for the mega-menu's category cards to look the same
    on every page — not a page-specific subset, and never an in-page
    anchor that only makes sense on the page that defines it."""
    from ruos.architecture_registry import load_structures

    billboard = next(s for s in load_structures() if s.id == "STR-001")
    lightbox = next(s for s in load_structures() if s.id == "STR-015")
    spec_a = build_structure_detail_spec(billboard)  # uses the default shell
    spec_b = build_structure_detail_spec(lightbox)
    nav_a = spec_a["shell"]["site-header"]["nav"]
    nav_b = spec_b["shell"]["site-header"]["nav"]
    cards_a = next(item["children"] for item in nav_a if "children" in item)
    cards_b = next(item["children"] for item in nav_b if "children" in item)
    assert cards_a == cards_b
    assert len(cards_a) >= 2
    for card in cards_a:
        assert card["href"].startswith("/"), f"mega-menu card must be a real path, not an anchor: {card}"


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


# ── build_product_page_spec — the generalized product-archetype generator ──
# The design-model-v1.1 spine (product-hero, spec sheet, FAQ, lead form),
# reusing the same real-data helpers as build_structure_detail_spec above,
# instead of hand-authoring a content brief like pages/blocks/straboard.json.


def test_a_structure_with_enough_attributes_builds_a_composable_product_page() -> None:
    spec = build_product_page_spec(_structure(), SHELL)
    assert spec["slug"] == "test-billboard"
    page = render_page(spec, load_library())
    composed_ids = [b.block_id for b in page.composed.blocks]
    assert composed_ids[0] == "product-hero"
    assert composed_ids[-1] == "lead-form"
    assert "structure-specs" in composed_ids
    assert "faq-section-final" in composed_ids


def test_a_structure_with_fewer_than_three_attributes_is_rejected_not_padded_for_the_product_page() -> None:
    sparse = _structure(context=None, orientation=None, dimensions=None)
    with pytest.raises(StructureDetailSpecError, match="not enough"):
        build_product_page_spec(sparse, SHELL)


def test_hero_stats_never_include_the_family_row_and_never_fabricate_a_missing_one() -> None:
    """'خانواده سازه' is already said by the title, so it never becomes a
    hero stat even though it is always the first real spec row; and a stat
    for an attribute the registry does not have (here: dimensions,
    orientation) must never appear."""
    spec = build_product_page_spec(
        _structure(context=None, orientation=None, dimensions=None,
                   face_count="one_or_two", mounting="wall"),
        SHELL,
    )
    stats = spec["blocks"][0]["data"]["stats"]
    labels = [s["label"] for s in stats]
    assert labels == ["تعداد رو", "نوع نصب"]
    assert "خانواده سازه" not in labels
    assert "ابعاد" not in labels
    assert "جهت" not in labels


def test_hero_stats_prioritise_dimension_and_orientation_over_context() -> None:
    spec = build_product_page_spec(_structure(), SHELL)  # context, orientation, dimensions all real
    stats = spec["blocks"][0]["data"]["stats"]
    labels = [s["label"] for s in stats]
    assert labels[:2] == ["ابعاد", "جهت"]
    assert len(stats) <= 3
    for stat in stats:
        assert stat["value"]  # every stat traces to a real spec value
        assert stat["icon"].startswith("icon-")


def test_a_structure_with_no_real_photos_gets_one_honest_placeholder_slide(tmp_path: Path) -> None:
    spec = build_product_page_spec(_structure(), SHELL, media_root=tmp_path)
    hero_data = spec["blocks"][0]["data"]
    block_ids = [entry["block"] for entry in spec["blocks"]]
    assert "structure-gallery" not in block_ids
    assert len(hero_data["slides"]) == 1
    assert "src" not in hero_data["slides"][0]
    assert hero_data["count"] == "۱"


def test_real_photos_fill_the_hero_slider_first_then_overflow_to_the_gallery(tmp_path: Path) -> None:
    """The hero is itself a slider now (design model §7/§15), so up to three
    real photos go straight into it; a structure with enough real photos
    left over (at least two, the gallery block's own minimum) still gets
    the rest shown, in the gallery block below."""
    directory = tmp_path / "STR-TEST"
    directory.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg", "e.jpg"):
        (directory / name).write_bytes(b"fake")
    spec = build_product_page_spec(_structure(), SHELL, media_root=tmp_path)
    hero_data = spec["blocks"][0]["data"]
    assert [slide["src"] for slide in hero_data["slides"]] == [
        "assets/a.jpg", "assets/b.jpg", "assets/c.jpg",
    ]
    assert hero_data["count"] == "۳"
    gallery = next(entry for entry in spec["blocks"] if entry["block"] == "structure-gallery")
    assert [item["src"] for item in gallery["data"]["items"]] == ["assets/d.jpg", "assets/e.jpg"]
    page = render_page(spec, load_library())
    assert "structure-gallery" in [b.block_id for b in page.composed.blocks]


def test_a_single_leftover_photo_never_makes_a_singleton_gallery(tmp_path: Path) -> None:
    """4 real photos: 3 fill the hero slider, leaving exactly 1 — below the
    gallery block's own minimum of 2, so it is honestly omitted rather than
    forcing a one-item gallery section onto the page."""
    directory = tmp_path / "STR-TEST"
    directory.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg"):
        (directory / name).write_bytes(b"fake")
    spec = build_product_page_spec(_structure(), SHELL, media_root=tmp_path)
    block_ids = [entry["block"] for entry in spec["blocks"]]
    assert "structure-gallery" not in block_ids


def test_related_structures_need_at_least_two_real_siblings() -> None:
    """A family of exactly two (e.g. straboard's own two size variants) means
    only one *other* sibling from either one's point of view — not enough to
    justify a whole cross-reference section, so it is honestly omitted."""
    from ruos.architecture_registry import load_structures

    straboard_variant = next(s for s in load_structures() if s.id == "STR-003")
    spec = build_product_page_spec(straboard_variant)
    assert "structure-related" not in [entry["block"] for entry in spec["blocks"]]

    brightboard_variant = next(s for s in load_structures() if s.id == "STR-008")
    spec = build_product_page_spec(brightboard_variant)
    assert "structure-related" in [entry["block"] for entry in spec["blocks"]]


def test_closes_with_a_real_lead_form_not_a_generic_review_gate() -> None:
    spec = build_product_page_spec(_structure(), SHELL)
    closer = spec["blocks"][-1]
    assert closer["block"] == "lead-form"
    field_names = [f["name"] for f in closer["data"]["fields"]]
    assert field_names == ["name", "phone", "project"]


def test_all_fourteen_composable_real_structures_actually_compose_the_product_page() -> None:
    from ruos.architecture_registry import load_structures

    composed_count = 0
    for structure in load_structures():
        try:
            spec = build_product_page_spec(structure)
        except StructureDetailSpecError:
            continue
        page = render_page(spec, load_library())
        assert page.composed.blocks
        composed_count += 1
    assert composed_count == 14
