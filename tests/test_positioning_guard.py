"""Positioning guards (design model §25).

The owner set two standing rules on 2026-10-14 that are easy to break by
accident, because both of them break by a writer reaching for the nearest
familiar example rather than by anyone deciding to break them:

1. Red Umbrella does not make shopfront signage, and no copy anywhere may
   refer to it until he says otherwise.
2. A services hub is not the outdoor-advertising page.

A rule nobody can check is a rule that comes back. These read the page specs,
which is where the copy actually lives.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC_DIRS = (ROOT / "pages" / "blocks", ROOT / "pages" / "drafts")

# «ما تابلوساز نیستیم که تابلو سر در مغازه بسازیم» — owner, 2026-10-14
SHOPFRONT_TERMS = ("سردر", "سر در مغازه", "مغازه", "ویترین", "تابلوی سردر")

UNLOCK = (
    "\n\nThis is design model §25, a standing owner rule. If the copy genuinely "
    "needs one of these words, that is a conversation with the owner, not a "
    "test to relax."
)


def _specs() -> list[tuple[str, str]]:
    out = []
    for directory in SPEC_DIRS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            out.append((path.name, path.read_text(encoding="utf-8")))
    return out


@pytest.mark.parametrize("name,text", _specs(), ids=lambda v: v if isinstance(v, str) and v.endswith(".json") else "")
def test_no_shopfront_signage_anywhere(name: str, text: str) -> None:
    hits = [term for term in SHOPFRONT_TERMS if term in text]
    assert not hits, (
        f"{name} contains shopfront vocabulary {hits}. Red Umbrella does not "
        f"make shopfront signs and no page may say it does — in copy, alt text, "
        f"a form placeholder or an example.{UNLOCK}"
    )


def test_the_services_hub_is_not_the_outdoor_page() -> None:
    """Every section of the hub has to be true of all six service areas. The
    cheap, catchable version of the failure: outdoor words dominating the
    sections that are supposed to speak for the whole agency."""
    path = ROOT / "pages" / "drafts" / "services.json"
    if not path.is_file():
        path = ROOT / "pages" / "blocks" / "services.json"
    if not path.is_file():
        pytest.skip("no services hub spec yet")

    spec = json.loads(path.read_text(encoding="utf-8"))
    by_block = {b["block"]: b for b in spec["blocks"]}
    outdoor = ("بیلبورد", "استرابورد", "سازه", "بنر", "اکران", "نصب", "تابلو")

    # The sections that speak for the agency rather than for one service.
    for block_id in ("hub-hero", "product-hero", "process-section-final", "editorial-split"):
        entry = by_block.get(block_id)
        if entry is None:
            continue
        text = json.dumps(entry["data"], ensure_ascii=False)
        hits = sorted({term for term in outdoor if term in text})
        assert len(hits) <= 1, (
            f"{block_id} leans on outdoor vocabulary {hits}. This section "
            f"speaks for the whole agency; if it needs billboards to make its "
            f"point it belongs on the outdoor page.{UNLOCK}"
        )


def test_the_hub_names_every_service_area() -> None:
    """The counter-check to the one above: the hub must actually cover the six
    areas, not merely avoid naming one of them too often."""
    path = ROOT / "pages" / "drafts" / "services.json"
    if not path.is_file():
        pytest.skip("no services hub draft")
    text = path.read_text(encoding="utf-8")
    areas = {
        "consulting": "مشاوره",
        "graphic": "گرافیک",
        "web/social": "اینستاگرام",
        "photo/video": "ویدیو",
        "print": "چاپ",
        "outdoor": "محیطی",
    }
    missing = [name for name, term in areas.items() if term not in text]
    assert not missing, f"the services hub never mentions: {missing}{UNLOCK}"
