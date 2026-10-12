"""The one site shell.

The navigation is locked and must be identical on every page. ``site_shell``
is what makes that structural rather than merely tested: there is one
definition and every page resolves to it. These tests cover the two ways
that could still go wrong quietly -- a nav entry pointing at an icon the
sprite does not have (which renders as an empty box, not an error), and a
provisional URL losing its flag and passing for a decided one.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from ruos.architecture_registry import load_entities
from ruos.site_shell import (
    provisional_nav_urls, site_nav, site_shell,
)

ROOT = Path(__file__).resolve().parents[1]
SPRITE = ROOT / "blocks/_foundation/assets/icon-sprite.svg"


def _sprite_ids() -> set[str]:
    return set(re.findall(r'<symbol id="([^"]+)"', SPRITE.read_text(encoding="utf-8")))


def _walk(entries):
    for entry in entries:
        yield entry
        yield from _walk(entry.get("children", ()))


def test_the_nav_row_is_home_plus_the_six_approved_panels() -> None:
    nav = site_nav()
    assert [entry["label"] for entry in nav] == [
        "خانه", "خدمات", "راهکارها", "سازه‌ها و تابلوها",
        "سرمایه‌گذاری", "نمونه‌کارها", "مرکز دانش",
    ]
    assert "children" not in nav[0], "Home is a plain link, not a panel"
    panels = nav[1:]
    assert len(panels) == 6
    for panel in panels:
        assert panel["children"], f"{panel['label']} is a panel with no cards"
        # the hero card the owner approved: the locked markup renders `note`
        # and `all_label` into `.mega-lead`, a paper card beside the grid.
        assert panel["note"], f"{panel['label']} has no hero-card note"
        assert panel["all_label"], f"{panel['label']} has no hero-card link"


def test_the_bottom_nav_is_the_five_entries_the_owner_chose() -> None:
    entries = site_shell()["bottom-nav"]["entries"]
    assert [entry["label"] for entry in entries] == [
        "خانه", "نمونه‌کارها", "سازه‌ها", "سرمایه‌گذاری", "تماس",
    ]


def test_every_bottom_nav_entry_has_an_idle_and_an_active_icon() -> None:
    """The locked bar paints the current item with a filled variant; an
    entry whose `-active` id is missing from the sprite goes blank the
    moment the bubble reaches it."""
    sprite = _sprite_ids()
    missing = []
    for entry in site_shell()["bottom-nav"]["entries"]:
        for key in ("icon", "icon_active"):
            if entry[key] not in sprite:
                missing.append(f"{entry['label']}: {entry[key]}")
    assert not missing, f"bottom-nav icons not in the sprite: {missing}"


def test_every_nav_icon_exists_in_the_sprite() -> None:
    """A `<use href="#missing-id">` renders nothing and logs nothing. This is
    the only thing that catches it."""
    sprite = _sprite_ids()
    missing = [
        f"{entry['label']}: {entry['icon']}"
        for entry in _walk(site_nav())
        if entry["icon"] not in sprite
    ]
    assert not missing, f"nav icons not in the sprite: {missing}"


def test_every_footer_link_has_a_label_and_an_href() -> None:
    for column in site_shell()["site-footer"]["columns"]:
        assert column["title"]
        for link in column["links"]:
            assert link["label"] and link["href"], f"{column['title']}: {link}"


def test_no_nav_card_is_missing_its_note() -> None:
    """A card with no note renders a title with an empty line under it."""
    bare = [entry["label"] for entry in _walk(site_nav())
            if entry.get("children") is None and not entry.get("note")]
    # Home is the one entry with no note: it is a plain link, not a card.
    assert bare == ["خانه"], f"cards with no note: {bare}"


@pytest.mark.parametrize("settled", ["/", "/structures/", "/investment/"])
def test_the_three_settled_urls_are_not_flagged_as_provisional(settled: str) -> None:
    """The registry records these as KEEP. Flagging them would send the URL
    audit chasing decisions that are already made."""
    flagged = [href for _, href, _ in provisional_nav_urls()]
    assert settled not in flagged


def test_every_unsettled_nav_url_is_flagged_and_traceable() -> None:
    """The owner's standing rule is that no URL is finalised before a live
    audit. So every nav destination the registry has not settled must carry
    its `url_status`, and `provisional_nav_urls` must list it -- otherwise a
    derived path quietly becomes the decided one.
    """
    settled = {"/"}
    for entity in load_entities():
        if (entity.url_status or "").upper() == "KEEP" and entity.url_candidate:
            settled.add(entity.url_candidate)

    unflagged = []
    for entry in _walk(site_nav()):
        href = entry["href"]
        if href in settled or href.startswith("/investment/#"):
            continue
        if href.startswith("/structures/"):
            continue  # a real structure page under a KEEP hub
        if not entry.get("provisional") or not entry.get("url_status"):
            unflagged.append(f"{entry['label']} -> {href}")
    assert not unflagged, (
        f"these nav destinations are not settled but carry no flag: {unflagged}"
    )

    listed = {href for _, href, _ in provisional_nav_urls()}
    for entry in _walk(site_nav()):
        if entry.get("provisional"):
            assert entry["href"] in listed, (
                f"{entry['label']} is provisional but provisional_nav_urls() omits it"
            )


def test_the_shell_is_the_same_object_graph_for_every_caller() -> None:
    """Two callers must get equal shells, and mutating one must not reach the
    other -- a shared mutable default would let one page's edit follow the
    nav onto every other page."""
    first, second = site_shell(), site_shell()
    assert first == second
    first["site-header"]["nav"][1]["children"][0]["label"] = "tampered"
    assert second["site-header"]["nav"][1]["children"][0]["label"] != "tampered"


def test_marking_a_section_changes_only_that_flag() -> None:
    plain = site_shell()
    marked = site_shell(active_href="/structures/")
    assert plain["site-header"] == marked["site-header"]
    assert [e.get("active") for e in marked["bottom-nav"]["entries"]] == [
        None, None, True, None, None,
    ]
    assert all(e.get("active") is None for e in plain["bottom-nav"]["entries"])
    for left, right in zip(plain["bottom-nav"]["entries"], marked["bottom-nav"]["entries"]):
        assert {k: v for k, v in right.items() if k != "active"} == left


def test_an_unknown_section_marks_nothing_rather_than_guessing() -> None:
    entries = site_shell(active_href="/nope/")["bottom-nav"]["entries"]
    assert all(entry.get("active") is None for entry in entries)
