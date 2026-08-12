"""The navigation lock.

The owner approved the site header (desktop mega-menu + mobile glass drawer)
and the mobile bottom nav on 2026-08-11 and locked them for the remainder of
the project: they are identical on every page and they do not change again.

These tests are the enforcement. If you are an assistant working in this
repository and one of them fails, you have edited a locked file. That is not
a test to update — it is a change to revert. See
``05-rules/website/navigation-lock.md`` for the one procedure that is allowed
to move these hashes, which requires the owner's explicit approval first.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ruos.navigation_lock import GUARDED_CLASS_PATTERN, LOCKED_FILES, UNLOCK_NOTICE

ROOT = Path(__file__).resolve().parents[1]
_UNLOCK = "\n\n" + UNLOCK_NOTICE


@pytest.mark.parametrize("relative_path", sorted(LOCKED_FILES))
def test_locked_navigation_file_is_unchanged(relative_path: str) -> None:
    path = ROOT / relative_path
    assert path.is_file(), f"Locked navigation file is missing: {relative_path}{_UNLOCK}"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == LOCKED_FILES[relative_path], (
        f"{relative_path} has been modified.{_UNLOCK}"
    )


def test_no_page_may_restyle_the_locked_navigation() -> None:
    """A page-level stylesheet cannot smuggle in a per-page nav variation.

    The lock above protects the two blocks' own files; this catches the other
    route to the same damage — some other block's CSS targeting a nav class.
    """
    owners = {"site-header", "bottom-nav", "_tokens"}
    offenders = []
    for stylesheet in sorted((ROOT / "blocks").glob("*/style.css")):
        if stylesheet.parent.name in owners:
            continue
        for number, line in enumerate(stylesheet.read_text(encoding="utf-8").splitlines(), start=1):
            selector = line.split("{", 1)[0]
            if GUARDED_CLASS_PATTERN.search(selector):
                offenders.append(f"{stylesheet.relative_to(ROOT)}:{number}")
    assert not offenders, (
        "These stylesheets target the locked navigation's classes, which would make the "
        f"nav differ between pages: {offenders}{_UNLOCK}"
    )


def test_every_composed_page_gets_the_same_navigation() -> None:
    """Shell data may differ per page in principle; it must not in practice."""
    from ruos.architecture_registry import load_structures
    from ruos.structure_detail_spec import _real_shell, _specs, build_structure_detail_spec

    buildable = [s for s in load_structures() if len(_specs(s)) >= 3]
    assert len(buildable) >= 2, "need at least two real structures to compare shells"

    reference = _real_shell()
    for structure in buildable[:6]:
        shell = build_structure_detail_spec(structure)["shell"]
        assert shell["site-header"] == reference["site-header"], (
            f"{structure.id} renders a different site-header.{_UNLOCK}"
        )
        assert shell["bottom-nav"] == reference["bottom-nav"], (
            f"{structure.id} renders a different bottom-nav.{_UNLOCK}"
        )
