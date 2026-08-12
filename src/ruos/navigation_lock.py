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
