import json

import pytest

from ruos.block_registry import BlockRegistryError, load_library
from ruos.block_template import TOKEN


def test_library_loads_and_is_internally_consistent() -> None:
    library = load_library()
    assert "_tokens" in library.blocks
    assert "_foundation" in library.blocks
    assert len(library.content_blocks()) >= 10


def test_content_blocks_declare_intents_a_composition_and_markup() -> None:
    for block in load_library().content_blocks():
        assert block.serves_intent, f"{block.id} declares no intent it serves"
        assert block.composition, f"{block.id} declares no composition pattern"
        assert block.source["page"], f"{block.id} does not record where it came from"
        assert block.markup, f"{block.id} ships no markup template"


def test_every_declared_slot_is_actually_used_by_the_template() -> None:
    """A contract that promises a slot the markup ignores is a silent lie."""
    for block in load_library().blocks.values():
        if not block.markup:
            continue
        used = {m.group(3).split(".")[0] for m in TOKEN.finditer(block.markup)
                if m.group(2) != "/" and m.group(2) != "@" and m.group(3)}
        for slot in block.slots:
            assert slot.name in used, f"{block.id} declares unused slot '{slot.name}'"


def test_opening_and_closing_blocks_exist_for_every_archetype() -> None:
    """Different page archetypes open/close with their own blocks; the composer
    still enforces exactly one of each per composed page (see block_composer)."""
    content = load_library().content_blocks()
    openers = {b.id for b in content if b.position == "first"}
    closers = {b.id for b in content if b.position == "last"}
    assert openers == {"hero-scroll-scene", "structure-hero", "product-hero"}
    assert closers == {"review-gate", "lead-form"}


def test_the_brand_font_is_embedded_in_the_token_block() -> None:
    """The page this library came from renders in a fallback font without it."""
    tokens = load_library().get("_tokens")
    assert "@font-face" in tokens.style
    assert "Vazirmatn" in tokens.style
    assert "base64" in tokens.style


def test_foundation_blocks_carry_no_markup() -> None:
    for block_id in ("_tokens", "_foundation"):
        assert load_library().get(block_id).markup == ""


def test_declared_assets_exist_on_disk() -> None:
    for block in load_library().blocks.values():
        for asset in block.assets:
            assert asset.is_file(), f"{block.id} lists a missing asset {asset}"


def test_library_fingerprint_is_deterministic() -> None:
    assert load_library().sha256 == load_library().sha256


def test_contract_rejects_directory_and_id_mismatch(tmp_path) -> None:
    block = tmp_path / "example"
    block.mkdir()
    (block / "block.json").write_text(json.dumps({
        "id": "something-else", "name": {"fa": "x"}, "role": "content",
        "family": "test", "surface": "light", "layout": "card-grid", "composition": "x",
    }), encoding="utf-8")
    (block / "style.css").write_text(".x{color:red}", encoding="utf-8")
    (block / "markup.html").write_text("<section></section>", encoding="utf-8")
    with pytest.raises(BlockRegistryError, match="mismatched id"):
        load_library(tmp_path)


def test_content_block_without_markup_is_rejected(tmp_path) -> None:
    block = tmp_path / "example"
    block.mkdir()
    (block / "block.json").write_text(json.dumps({
        "id": "example", "name": {"fa": "x"}, "role": "content",
        "family": "test", "surface": "light", "layout": "card-grid", "composition": "x",
    }), encoding="utf-8")
    (block / "style.css").write_text(".x{color:red}", encoding="utf-8")
    with pytest.raises(BlockRegistryError, match="no markup.html"):
        load_library(tmp_path)


def test_library_requires_the_foundation_blocks(tmp_path) -> None:
    block = tmp_path / "example"
    block.mkdir()
    (block / "block.json").write_text(json.dumps({
        "id": "example", "name": {"fa": "x"}, "role": "content",
        "family": "test", "surface": "light", "layout": "card-grid", "composition": "x",
    }), encoding="utf-8")
    (block / "style.css").write_text(".x{color:red}", encoding="utf-8")
    (block / "markup.html").write_text("<section></section>", encoding="utf-8")
    with pytest.raises(BlockRegistryError, match="_tokens"):
        load_library(tmp_path)


def test_unknown_vendor_library_is_rejected(tmp_path) -> None:
    block = tmp_path / "example"
    block.mkdir()
    (block / "block.json").write_text(json.dumps({
        "id": "example", "name": {"fa": "x"}, "role": "content",
        "family": "test", "surface": "light", "layout": "card-grid", "composition": "x",
        "behavior": True, "vendor": ["not-a-real-library"],
    }), encoding="utf-8")
    (block / "style.css").write_text(".x{color:red}", encoding="utf-8")
    (block / "markup.html").write_text("<section></section>", encoding="utf-8")
    (block / "behavior.js").write_text("console.log(1);", encoding="utf-8")
    with pytest.raises(BlockRegistryError, match="unknown vendor"):
        load_library(tmp_path)


def test_vendor_library_without_declared_behavior_is_rejected(tmp_path) -> None:
    block = tmp_path / "example"
    block.mkdir()
    (block / "block.json").write_text(json.dumps({
        "id": "example", "name": {"fa": "x"}, "role": "content",
        "family": "test", "surface": "light", "layout": "card-grid", "composition": "x",
        "vendor": ["motion"],
    }), encoding="utf-8")
    (block / "style.css").write_text(".x{color:red}", encoding="utf-8")
    (block / "markup.html").write_text("<section></section>", encoding="utf-8")
    with pytest.raises(BlockRegistryError, match="vendor libraries but no behavior"):
        load_library(tmp_path)


def test_foundation_declares_and_ships_the_motion_vendor_library() -> None:
    foundation = load_library().get("_foundation")
    assert foundation.vendor == ("motion",)
    asset_names = {path.name for path in foundation.assets}
    assert "motion.min.mjs" in asset_names
