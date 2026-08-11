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
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# sha256 of every file that makes up the two locked components.
LOCKED_FILES: dict[str, str] = {
    "blocks/site-header/markup.html":
        "ceecf927b5f40a2ad42af45ad4396dcd1170cc47ff314c2b3a48f45d4031183e",
    "blocks/site-header/style.css":
        "76fe8312bd11a67d3836b90548f8a78ed1a59dc1bb87d410b2038030258d5ba5",
    "blocks/site-header/behavior.js":
        "64e4705d374d3a106a64693fc7eb668b65dfae41271af56b2abef97a46e9cc68",
    "blocks/bottom-nav/markup.html":
        "9d244031a3cbc523149b029c0758dd00a79197f7b71342dfaab5dc0a2af7a397",
    "blocks/bottom-nav/style.css":
        "cd1cf6f09b0de7da63b1b0d96a39db8c273fd342c7029ee1ab4499229f1e70b8",
    "blocks/bottom-nav/behavior.js":
        "2d173c83ab1d7cda1c1deeaef6d6cc6e75e9417e8191bafff21524bf77589ac6",
}

_UNLOCK = (
    "\n\nThis file is LOCKED by owner decision (2026-08-11). Revert your edit. "
    "Changing it needs the owner's explicit approval first, then the procedure "
    "in 05-rules/website/navigation-lock.md."
)


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
    # The class prefixes the two locked components own.
    guarded = re.compile(
        r"\.(site-header|mega-|nav-link|nav-ico|menu-button|menu-ico|mobile-menu|m-group|m-cards|m-card|m-link|m-all|m-cta|bottom-nav|bn-)"
    )
    offenders = []
    for stylesheet in sorted((ROOT / "blocks").glob("*/style.css")):
        if stylesheet.parent.name in owners:
            continue
        for number, line in enumerate(stylesheet.read_text(encoding="utf-8").splitlines(), start=1):
            selector = line.split("{", 1)[0]
            if guarded.search(selector):
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
