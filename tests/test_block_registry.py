import json

import pytest

from ruos.block_library import RENDERERS
from ruos.block_registry import BlockRegistryError, load_library


def test_library_loads_and_is_internally_consistent() -> None:
    library = load_library()
    assert library.blocks, "the block library must not be empty"
    assert "_tokens" in library.blocks
    assert "_foundation" in library.blocks
    assert len(library.content_blocks()) >= 8


def test_every_contract_has_a_renderer_and_every_renderer_has_a_contract() -> None:
    library = load_library()
    contracts = {block_id for block_id in library.blocks if not block_id.startswith("_")}
    assert contracts == set(RENDERERS)


def test_content_blocks_declare_intents_and_a_composition() -> None:
    for block in load_library().content_blocks():
        assert block.serves_intent, f"{block.id} declares no intent it serves"
        assert block.composition, f"{block.id} declares no composition pattern"
        assert block.source["page"], f"{block.id} does not record where it came from"


def test_exactly_one_opening_and_one_closing_block_exist() -> None:
    content = load_library().content_blocks()
    assert [b.id for b in content if b.position == "first"] == ["hero-split-scene"]
    assert [b.id for b in content if b.position == "last"] == ["closing-band"]


def test_declared_behavior_matches_shipped_scripts() -> None:
    for block in load_library().blocks.values():
        script_exists = (block.style is not None) and bool(block.script)
        assert block.behavior == script_exists, (
            f"{block.id} declares behavior={block.behavior} but "
            f"{'ships' if script_exists else 'ships no'} a script"
        )


def test_library_fingerprint_is_deterministic() -> None:
    assert load_library().sha256 == load_library().sha256


def test_contract_rejects_directory_and_id_mismatch(tmp_path) -> None:
    block = tmp_path / "example"
    block.mkdir()
    (block / "block.json").write_text(json.dumps({
        "id": "something-else", "name": {"fa": "x"}, "role": "content",
        "family": "test", "surface": "light", "composition": "x",
    }), encoding="utf-8")
    (block / "style.css").write_text(".x{color:red}", encoding="utf-8")
    with pytest.raises(BlockRegistryError, match="mismatched id"):
        load_library(tmp_path)


def test_contract_rejects_undeclared_behavior_script(tmp_path) -> None:
    block = tmp_path / "example"
    block.mkdir()
    (block / "block.json").write_text(json.dumps({
        "id": "example", "name": {"fa": "x"}, "role": "content",
        "family": "test", "surface": "light", "composition": "x", "behavior": False,
    }), encoding="utf-8")
    (block / "style.css").write_text(".x{color:red}", encoding="utf-8")
    (block / "behavior.js").write_text("console.log(1)", encoding="utf-8")
    with pytest.raises(BlockRegistryError, match="without declaring behavior"):
        load_library(tmp_path)


def test_library_requires_the_foundation_blocks(tmp_path) -> None:
    block = tmp_path / "example"
    block.mkdir()
    (block / "block.json").write_text(json.dumps({
        "id": "example", "name": {"fa": "x"}, "role": "content",
        "family": "test", "surface": "light", "composition": "x",
    }), encoding="utf-8")
    (block / "style.css").write_text(".x{color:red}", encoding="utf-8")
    with pytest.raises(BlockRegistryError, match="_tokens"):
        load_library(tmp_path)
