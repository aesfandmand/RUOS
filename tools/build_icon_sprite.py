#!/usr/bin/env python3
"""Rebuild blocks/_foundation/assets/icon-sprite.svg from Phosphor Icons.

The owner approved Phosphor as the site's single icon family. This script
is the repeatable way to regenerate the sprite so nobody hand-edits SVG
path data or quietly mixes in an icon from another family.

Usage:
    npm install @phosphor-icons/core   # in some scratch dir
    python3 tools/build_icon_sprite.py /path/to/node_modules/@phosphor-icons/core

Every id below is referenced from block markup as
``<svg><use href="#icon-name"></use></svg>``. Adding an icon here is the
only supported way to add one to the site.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "blocks/_foundation/assets/icon-sprite.svg"

# id -> (phosphor name, weight). "fill" variants back the active state of
# a nav item, which is why Phosphor was chosen over a single-weight family.
ICONS: dict[str, tuple[str, str]] = {
    # --- content icons already in use by built blocks ---
    "icon-ruler": ("ruler", "regular"),
    "icon-location": ("map-pin", "regular"),
    "icon-shield": ("shield", "regular"),
    "icon-faq": ("question", "regular"),
    "icon-related": ("link-simple", "regular"),
    "icon-services": ("wrench", "regular"),
    "icon-chevron-left": ("caret-left", "regular"),
    "icon-chevron-right": ("caret-right", "regular"),
    "icon-external": ("arrow-square-out", "regular"),
    "icon-datasheet": ("file-text", "regular"),

    # --- product-page content icons (straboard archetype) ---
    "icon-tension": ("arrows-out-line-horizontal", "regular"),
    "icon-cost": ("currency-circle-dollar", "regular"),
    "icon-transport": ("truck", "regular"),
    "icon-repair": ("wrench", "regular"),
    "icon-city": ("buildings", "regular"),
    "icon-clean-view": ("eye", "regular"),
    "icon-check": ("check", "bold"),
    "icon-play": ("play", "fill"),
    "icon-arrow-left": ("arrow-left", "regular"),
    "icon-compare": ("scales", "regular"),
    "icon-factory": ("factory", "regular"),
    "icon-palette": ("palette", "regular"),
    "icon-article": ("article", "regular"),
    "icon-user": ("user", "regular"),
    "icon-phone": ("phone", "regular"),
    "icon-pin-area": ("map-trifold", "regular"),
    "icon-lightbulb": ("lightbulb", "regular"),
    "icon-orientation": ("frame-corners", "regular"),
    "icon-faces": ("copy", "regular"),

    # --- navigation chrome ---
    "icon-menu": ("list", "regular"),
    "icon-close": ("x", "regular"),
    "icon-search": ("magnifying-glass", "regular"),
    "icon-caret-down": ("caret-down", "regular"),

    # --- top-level nav sections (regular = idle, fill = active) ---
    "icon-home": ("house", "regular"),
    "icon-home-active": ("house", "fill"),
    "icon-structures": ("squares-four", "regular"),
    "icon-structures-active": ("squares-four", "fill"),
    "icon-investment": ("chart-line-up", "regular"),
    "icon-investment-active": ("chart-line-up", "fill"),
    "icon-services-nav": ("wrench", "regular"),
    "icon-services-nav-active": ("wrench", "fill"),
    "icon-rfq": ("note-pencil", "regular"),
    "icon-rfq-active": ("note-pencil", "fill"),
    "icon-contact": ("phone", "regular"),
    "icon-contact-active": ("phone", "fill"),
    "icon-solutions": ("target", "regular"),
    "icon-solutions-active": ("target", "fill"),
    "icon-portfolio": ("images-square", "regular"),
    "icon-portfolio-active": ("images-square", "fill"),
    "icon-knowledge": ("book-open-text", "regular"),
    "icon-knowledge-active": ("book-open-text", "fill"),
    "icon-projects": ("folders", "regular"),
    "icon-projects-active": ("folders", "fill"),

    # --- one icon per real service family, for the Services mega panel.
    # The six families are the registry's own first layer
    # (architecture registry v2.1, ServiceRecord.family) -- not a set
    # invented for the menu.
    "icon-fam-outdoor": ("road-horizon", "regular"),
    "icon-fam-digital": ("cursor-click", "regular"),
    "icon-fam-graphic": ("pen-nib", "regular"),
    "icon-fam-print": ("printer", "regular"),
    "icon-fam-photo": ("camera", "regular"),
    "icon-fam-consult": ("chats-circle", "regular"),

    # --- one icon per Solutions audience, and the portfolio/knowledge
    # card sets ---
    "icon-sol-public": ("bank", "regular"),
    "icon-sol-industrial": ("factory", "regular"),
    "icon-sol-expo": ("tent", "regular"),
    "icon-sol-local": ("storefront", "regular"),
    "icon-fam-web": ("browsers", "regular"),
    "icon-fam-social": ("instagram-logo", "regular"),
    "icon-fam-video": ("video-camera", "regular"),
    "icon-glossary": ("book-bookmark", "regular"),

    # --- investment panel cards ---
    "icon-partnership": ("handshake", "regular"),
    "icon-purchase": ("shopping-bag", "regular"),
    "icon-process": ("path", "regular"),

    # --- one icon per real structure family, for the mega-menu cards ---
    "icon-fam-billboard": ("projector-screen", "regular"),
    "icon-fam-straboard": ("frame-corners", "regular"),
    "icon-fam-lightbox": ("lightbulb", "regular"),
    "icon-fam-lightboard": ("lamp", "regular"),
    "icon-fam-brightboard": ("sun", "regular"),
    "icon-fam-org": ("buildings", "regular"),
    "icon-fam-indoor": ("storefront", "regular"),
    "icon-fam-bridge": ("bridge", "regular"),
}


def build(core_root: Path) -> str:
    symbols: list[str] = []
    missing: list[str] = []
    for symbol_id, (name, weight) in ICONS.items():
        suffix = "" if weight == "regular" else f"-{weight}"
        path = core_root / "assets" / weight / f"{name}{suffix}.svg"
        if not path.is_file():
            missing.append(f"{symbol_id} -> {path}")
            continue
        svg = path.read_text(encoding="utf-8")
        viewbox = re.search(r'viewBox="([^"]+)"', svg).group(1)
        inner = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1).strip()
        symbols.append(f'<symbol id="{symbol_id}" viewBox="{viewbox}">{inner}</symbol>')
    if missing:
        raise SystemExit("Missing Phosphor sources:\n  " + "\n  ".join(missing))
    return '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">' + "".join(symbols) + "</svg>"


if __name__ == "__main__":
    core = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("node_modules/@phosphor-icons/core")
    sprite = build(core)
    OUT.write_text(sprite, encoding="utf-8")
    print(f"{OUT}: {len(sprite)} bytes, {len(ICONS)} icons")
