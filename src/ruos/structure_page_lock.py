"""The single source of truth for the Structure Detail page lock.

The owner approved the straboard page — mobile and desktop, the full
19-block archetype in ``pages/blocks/straboard.json`` — on 2026-08-14 and
locked it for the remainder of the project: this is the design, it is not
to change again by accident, and it is the mandatory template for every
other structure's page. See ``05-rules/website/structure-page-lock.md``.

This module holds the data both the enforcement test
(``tests/test_structure_page_lock.py``) and the page critic
(``page_critic.py``) need, so the two can never drift apart. Mirrors
``navigation_lock.py``'s shape on purpose — same pattern, same procedure,
a different set of files.
"""
from __future__ import annotations

# The exact block order the owner approved, twice (mobile, then desktop) and
# through three full rounds of review fixes. This is `pages/blocks/
# straboard.json`'s own `blocks[*].id` sequence — reproduced here so
# `tests/test_structure_page_lock.py` can assert the promoted page file
# itself has not silently reordered, dropped, or added a section.
LOCKED_BLOCK_ORDER: tuple[str, ...] = (
    "top", "what", "why", "models", "gallery", "parts", "compare", "specs",
    "color", "price", "projects", "factory", "knowledge", "fit", "paths",
    "services", "others", "faq", "quote",
)

# sha256 of every block file (markup/style/behavior) that makes up the
# archetype, plus the two shared foundations every page is built on
# (_tokens for the palette/type scale, _foundation for the reveal system and
# base shell classes) and site-footer (the third shell component alongside
# site-header/bottom-nav, which navigation_lock.py already owns — not
# duplicated here). All pinned 2026-08-14, the day the owner approved the
# desktop design and the "سیگنال ایمنی" palette on top of it.
LOCKED_FILES: dict[str, str] = {
    "blocks/_foundation/behavior.js":
        "38c03a450ed6c8c9eb3c978c43f7977d6c5003d15aca9c82fa7d65e21e17d5a2",
    "blocks/_foundation/style.css":
        "60662569662cb07e9795790e29b05e0a1f8a32d613d0762aef76e580fff2ca6d",
    "blocks/_tokens/style.css":
        "e564bcb26582e2b9173c942bfefa6c388c327f8c3daced1c7ff2230ef4cd80f7",
    "blocks/checklist-section/markup.html":
        "33ce5c8524fff3d0be00d7ec0707e5caae635e54689d928cdce7b12da2912d2c",
    "blocks/checklist-section/style.css":
        "27f2723066a7480950feda1e89a9f671ca520f9884bac39ceccc95b1a66b58a6",
    "blocks/compare-cards/markup.html":
        "6a96623a2bc4178ee9ee4b906c5c30bb3b54947c1259358f964d67df10937ea7",
    "blocks/compare-cards/style.css":
        "8547f67a347ee2e8670901ba6a8a67bff8d5a1bd24aea8684fbbbb4efa28552e",
    "blocks/editorial-split/markup.html":
        "0caa8b6e6d3b22920357649906bd6e31e2f962dafbd4b71688e9c3dd21ca0cfc",
    "blocks/editorial-split/style.css":
        "efff9e18fb422117ed3061a20167dd265e9dd10b552c5d0b3635e7020c87ca76",
    "blocks/faq-section-final/markup.html":
        "250e802b9a71261352fa748d6138614655b772f20c01794800a182219df8a638",
    "blocks/faq-section-final/style.css":
        "4df8648c35bbffe88d0efd0306aa6b1fbc94c242de6d6914be028465ebe8517b",
    "blocks/knowledge-carousel/behavior.js":
        "a46348b45ee39daf5a79a85a0fa1e243ff0a71e873d1f61d4580c789652705ff",
    "blocks/knowledge-carousel/markup.html":
        "6b74267e380f568b3cfdc76f55f295fbcbaea90d620316e7b8fd8676465b583c",
    "blocks/knowledge-carousel/style.css":
        "dbf509841bd6497ab71f22a19f7ab78da6d51197f2d17e529efad2509e82f501",
    "blocks/lead-form/behavior.js":
        "24e75bee1d47e558975c4525c487770fec2802c7eedd0bb88a3ad097db1bdaee",
    "blocks/lead-form/markup.html":
        "4db76c29fe2477147241454780c79df1cb631c27b3f76f3e7ed8e1e7ed28fdba",
    "blocks/lead-form/style.css":
        "027af3a620d6ebd0cfdba4c4bd3731ff936092d5f33099ae6aff357e41fe128e",
    "blocks/numbered-features/markup.html":
        "b8453fe9f5da3aa84aff1d9a60e0e9041ff240aefb77a4209d498f214c19f53a",
    "blocks/numbered-features/style.css":
        "4f05ce395bf6ce2f5152af991d9ff8853e41711b35ce2de51b755707cfd76e69",
    "blocks/parts-zigzag/markup.html":
        "81b48e5aaef6fb97ebbde1f520d23427fab07a693d5d4cb7ff0edd68ed510bd9",
    "blocks/parts-zigzag/style.css":
        "519fe23300bcc51c508e989e72d3961e1a1c2e2d4b628b1c250b5f86a4a61c3e",
    "blocks/product-hero/behavior.js":
        "2a29d3c761cfa7cdf1742be3b48d22979a81bf88b5be294ebd1f81788e476810",
    "blocks/product-hero/markup.html":
        "7d48dc18cc002a1590a29812d9c49839ed2da56fc1c75dc150f8fa7a4c73674b",
    "blocks/product-hero/style.css":
        "b99c84fcfdaedac65488e0fcb112cb16dd8c6eccc6e973d9a8e5ec81c7c6f253",
    "blocks/site-footer/markup.html":
        "b0634bb77b3133b6d89041c7c7c0b1e64269b12a9201104d1957f2398f83679b",
    "blocks/site-footer/style.css":
        "55121aa84dac2b45743e92e350256a8a46a0c21e61782d3ed9636c8a606321c3",
    "blocks/spec-table/markup.html":
        "83c7cc238e68ace81f79418b0012d5ae13c6792c2c6f9c171ab9def12d56d5d6",
    "blocks/spec-table/style.css":
        "3732514e1d82f3c8a8d855e8bd2712098fd7aceb537462d8d473edc00476ae72",
    "blocks/structure-gallery/behavior.js":
        "6dfa34ba15dc0522cba4ea1814e752984d587253ef1f1347618a1e8f12c69a7c",
    "blocks/structure-gallery/markup.html":
        "646b9ac01d98c179342e5ffd9bb465f795750e1da2d324af815f316fd1f76e5d",
    "blocks/structure-gallery/style.css":
        "2b1a67dc755d0a34fa4bbd406a3abc6a02bc0a221c20b63dd973fcace7bef410",
    "blocks/structure-related/behavior.js":
        "831c51ca893a930a3a822eb6cb36a40a479b3059a9fa40b3525f8cb5376c4f6f",
    "blocks/structure-related/markup.html":
        "e8cae80f5a336c116a1ceea506380ffec86284bf19d3dc2e6fcb42f0769609f3",
    "blocks/structure-related/style.css":
        "abb660524a8d7418aa648fc3b22fb3f1c01d7fce0b4353be7337c25ac289f23f",
    "blocks/structure-services/markup.html":
        "9396eef2d9725c2f8b7e4767bbcdb6d79edd1a9cff7704f42d88a7be3bf2f75b",
    "blocks/structure-services/style.css":
        "13b93bbfeaf4534d950bb4ceec499821c8f197b1b2c912b8f838a82a21d9b564",
    "blocks/variant-carousel/behavior.js":
        "cf1879dd2b8e12f9e6ea63b1642c7770f8de49c6138805d6e61f7f5f99c3316b",
    "blocks/variant-carousel/markup.html":
        "b5e6d5c6123ba73f7341eaecd91366c532cf6de29fbc64a935f2761fd12b0278",
    "blocks/variant-carousel/style.css":
        "5ee69bf5662ca88f65f0ac635f5b41693134c687e7bc51103fc029043f8702db",
    "blocks/workshop-gallery/markup.html":
        "4fe61ff2d56d52982777f9574414ef7bb8dd03a9d06252855898663296603072",
    "blocks/workshop-gallery/style.css":
        "00ba59928f2801df36274d8277237beca4049c988d0ef9942557e40e17d01d4a",
}

UNLOCK_NOTICE = (
    "This file is part of the LOCKED Structure Detail page archetype (owner "
    "decision, 2026-08-14). Revert your edit. Changing it needs the owner's "
    "explicit approval first, then the procedure in "
    "05-rules/website/structure-page-lock.md."
)
