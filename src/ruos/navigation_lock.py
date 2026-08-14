"""The single source of truth for the navigation lock.

The owner approved the site header (desktop mega-menu + mobile glass drawer)
and the mobile bottom nav on 2026-08-11 and locked them for the remainder of
the project — see ``05-rules/website/navigation-lock.md``. This module holds
the data both the enforcement test (``tests/test_navigation_lock.py``) and
the page critic (``page_critic.py``) need, so the two can never drift apart.
"""
from __future__ import annotations

import re

# sha256 of every file that makes up the two locked components.
#
# bottom-nav/style.css was re-pinned on 2026-08-13 under the procedure in
# navigation-lock.md, for the owner's explicitly approved change: the red
# reference finish on the bar, the active bubble reduced to 20% protrusion,
# and the ring between the icon and the bubble tightened by 30%.
#
# site-header/style.css was re-pinned on 2026-08-14 under the same procedure,
# for the owner's explicitly approved change — "نوار منو در هنگام باز شدن نرم
# باز نمیشود / در زمان بسته شدن که کلا حرکتی ندارد که آن هم باید خیلی نرم
# بسته شود": the mega-menu's open and close curves, which had shared one
# heavily front-loaded easing. Only the transitions changed; the panel's
# geometry, colour and behaviour are untouched. The other four files are
# still on their original 2026-08-11 hashes.
LOCKED_FILES: dict[str, str] = {
    "blocks/site-header/markup.html":
        "ceecf927b5f40a2ad42af45ad4396dcd1170cc47ff314c2b3a48f45d4031183e",
    "blocks/site-header/style.css":
        "493ae9e9fb9d3aa5862483cd68cb9574cf4210c67981f732340965f70c4ff96f",
    "blocks/site-header/behavior.js":
        "64e4705d374d3a106a64693fc7eb668b65dfae41271af56b2abef97a46e9cc68",
    "blocks/bottom-nav/markup.html":
        "9d244031a3cbc523149b029c0758dd00a79197f7b71342dfaab5dc0a2af7a397",
    "blocks/bottom-nav/style.css":
        "8dcc3a55446aec639cf5a3d5c6787744b52510b37d92afb15970ac45aa79994b",
    "blocks/bottom-nav/behavior.js":
        "2d173c83ab1d7cda1c1deeaef6d6cc6e75e9417e8191bafff21524bf77589ac6",
}

# The class prefixes the two locked components own — a page-level stylesheet
# targeting one of these would smuggle in a per-page nav variation.
GUARDED_CLASS_PATTERN = re.compile(
    r"\.(site-header|mega-|nav-link|nav-ico|menu-button|menu-ico|mobile-menu|m-group|m-cards|m-card|m-link|m-all|m-cta|bottom-nav|bn-)"
)

UNLOCK_NOTICE = (
    "This file is LOCKED by owner decision (2026-08-11). Revert your edit. "
    "Changing it needs the owner's explicit approval first, then the procedure "
    "in 05-rules/website/navigation-lock.md."
)
