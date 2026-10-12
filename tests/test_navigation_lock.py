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
import json
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


def _nav_shape(shell: dict) -> tuple:
    """Everything about the nav except which section is marked current.

    ``active`` is page state -- the liquid bubble has to rest on the section
    the visitor is in -- so it is excluded. Entries, order, labels, icons and
    hrefs are the navigation, and those must match everywhere.
    """
    header = shell["site-header"]

    def entry(row: dict) -> tuple:
        return (
            row.get("label"), row.get("href"), row.get("icon"),
            row.get("note"), row.get("all_label"),
            tuple(entry(child) for child in row.get("children", ())),
        )

    return (
        header.get("brand"), header.get("cta"),
        tuple(entry(row) for row in header["nav"]),
        tuple(
            (row.get("label"), row.get("href"), row.get("icon"), row.get("icon_active"))
            for row in shell["bottom-nav"]["entries"]
        ),
    )


def test_every_page_spec_takes_the_shared_shell_rather_than_its_own_copy() -> None:
    """The lock says the nav is identical on every page. A page that writes
    its own copy of the nav data satisfies that only until somebody edits one
    copy, so a page spec must ask for the shared shell by reference
    (``"shell": "@site"``) instead of inlining it. See ruos.site_shell."""
    from ruos.site_shell import SITE_SHELL_REF

    offenders = []
    for spec_path in sorted((ROOT / "pages/blocks").glob("*.json")):
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
        shell = raw.get("shell")
        if shell is None:
            continue
        if shell != SITE_SHELL_REF:
            offenders.append(spec_path.relative_to(ROOT).as_posix())
    assert not offenders, (
        "These page specs carry their own copy of the navigation instead of "
        f'"shell": "{SITE_SHELL_REF}": {offenders}{_UNLOCK}'
    )


def test_pages_in_different_sections_still_render_the_same_navigation() -> None:
    """The structure comparison above only covers Structure Detail pages,
    which all sit in one section. This compares across sections, where a
    per-page variation would actually be tempting."""
    from pathlib import Path as _Path

    from ruos.block_page import load_page_spec

    slugs = ("straboard", "urban-investment")
    shapes = {
        slug: _nav_shape(load_page_spec(_Path(ROOT / f"pages/blocks/{slug}.json"))["shell"])
        for slug in slugs
    }
    first, *rest = slugs
    for slug in rest:
        assert shapes[slug] == shapes[first], (
            f"{slug} renders different navigation from {first}.{_UNLOCK}"
        )

    # ...and each one does mark its own section, or the bubble sits on Home
    # everywhere.
    for slug, section in (("straboard", "/structures/"), ("urban-investment", "/investment/")):
        spec = load_page_spec(_Path(ROOT / f"pages/blocks/{slug}.json"))
        active = [e for e in spec["shell"]["bottom-nav"]["entries"] if e.get("active")]
        assert [e["href"] for e in active] == [section], (
            f"{slug} does not mark {section} as the current bottom-nav section: "
            f"{[e['href'] for e in active]}"
        )
