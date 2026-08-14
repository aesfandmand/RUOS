"""The Structure Detail page lock.

The owner approved the straboard page (mobile, then desktop, through three
full rounds of review fixes and a palette pass) on 2026-08-14 and locked it
for the remainder of the project: it is the design, and it is the mandatory
template for every other structure's page — same blocks, same order, only
the data changes.

These tests are the enforcement. If you are an assistant working in this
repository and one of them fails, you have edited a locked file, or you have
changed straboard.json's block composition. That is not a test to update —
it is a change to revert. See ``05-rules/website/structure-page-lock.md``
for the one procedure allowed to move these hashes, which requires the
owner's explicit approval first.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ruos.structure_page_lock import LOCKED_BLOCK_ORDER, LOCKED_FILES, UNLOCK_NOTICE

ROOT = Path(__file__).resolve().parents[1]
_UNLOCK = "\n\n" + UNLOCK_NOTICE


@pytest.mark.parametrize("relative_path", sorted(LOCKED_FILES))
def test_locked_structure_page_file_is_unchanged(relative_path: str) -> None:
    path = ROOT / relative_path
    assert path.is_file(), f"Locked structure-page file is missing: {relative_path}{_UNLOCK}"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == LOCKED_FILES[relative_path], (
        f"{relative_path} has been modified.{_UNLOCK}"
    )


def test_the_approved_straboard_page_keeps_the_locked_block_order() -> None:
    """pages/blocks/straboard.json is the promoted, approved page. Its own
    block sequence must stay exactly what the owner approved -- this is what
    a future structure's page is required to copy."""
    spec = json.loads((ROOT / "pages/blocks/straboard.json").read_text(encoding="utf-8"))
    actual_order = tuple(block["id"] for block in spec["blocks"])
    assert actual_order == LOCKED_BLOCK_ORDER, (
        f"straboard.json's block order changed: {actual_order}{_UNLOCK}"
    )


def test_every_locked_block_is_used_by_the_approved_page() -> None:
    """Catches the inverse mistake: a file added to LOCKED_FILES for a block
    straboard.json no longer actually uses (e.g. after a future edit drops a
    section), which would lock a file for no reason and hide a real change
    behind a lock failure that looks like tampering."""
    spec = json.loads((ROOT / "pages/blocks/straboard.json").read_text(encoding="utf-8"))
    used_blocks = {block["block"] for block in spec["blocks"]}
    used_blocks |= {"_tokens", "_foundation", "site-footer"}
    locked_blocks = {path.split("/")[1] for path in LOCKED_FILES if path.startswith("blocks/")}
    assert locked_blocks <= used_blocks, (
        f"LOCKED_FILES pins blocks straboard.json does not use: {locked_blocks - used_blocks}{_UNLOCK}"
    )
