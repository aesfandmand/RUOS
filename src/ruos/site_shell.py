"""The one site shell: header mega-menu, bottom nav and footer.

The navigation is locked (``05-rules/website/navigation-lock.md``) and the
lock's third clause is that **two composed pages may not end up with
different ``site-header`` or ``bottom-nav`` shell data**. Until now that
clause was enforced by a test comparing pages that each carried their own
verbatim copy of the data -- so the rule held only as long as nobody edited
one copy. This module makes it structural: there is one shell, every page
resolves to it, and divergence is no longer something a page *can* express.
A page spec asks for it by writing ``"shell": "@site"`` (see
``block_page.load_page_spec``).

Nothing here is composed by taste. Every top-level entry, every card and
every URL comes from the architecture registry v2.1 --
``EntityRecord.navigation`` says what belongs in the nav, ``parent_id`` says
which panel it belongs to, and ``url_candidate``/``url_status`` say where it
points and whether that is settled. The structure panel's cards come from
the structure registry the same way they always did.

## Provisional URLs

The registry records most of these pages as ``PENDING_AUDIT``: the owner's
standing rule is that no live URL moves just to tidy the architecture, so
the final path waits on a live URL audit. Three paths are settled (``/``,
``/structures/``, ``/investment/`` -- all ``KEEP``), two more carry a real
candidate (``/services/``, ``/solutions/``, ``/consulting/``, ``/portfolio/``,
``/projects/``), and the rest are still ``PENDING``.

Those are given a provisional path derived from the registry's own
``name_en``, and the nav entry carries ``url_status`` and
``provisional: True`` so the audit has one file to correct and no reader
mistakes a provisional path for a decided one. ``provisional_nav_urls()``
lists them.

The derivation puts a service family at the **root**, not under
``/services/``: ``مشاوره`` is the one family in that set whose URL candidate
the registry actually records, and it records ``/consulting/`` -- not
``/services/consulting/``. Registry sheet 05's own warning is that the IA
hierarchy is not the URL hierarchy, so following the one decided sibling is
better grounded than inventing a nesting the registry never states.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .architecture_registry import EntityRecord, load_entities, load_services

SITE_SHELL_REF = "@site"

_BRAND = {
    "name": "چتر قرمز",
    "tagline": "به آسمان سلام کن",
    "aria": "چتر قرمز، ابتدای صفحه",
    "logo_alt": "نشان چتر قرمز",
}

# Registry ids, in the order the owner approved for the nav row: Home as a
# plain link, then the six mega panels. Every id here is an entity whose
# `navigation` field puts it in the main nav or the mega menu.
_HOME_ID = "CORE-001"
_PANEL_IDS = ("SRV-000", "SOL-000", "STR-000", "INV-000", "PRT-000", "KNW-000")

# Which registry children fill each panel. Services and Solutions are the
# registry's own parent_id children; Structures is the live structure
# registry (eight real families); Investment and Portfolio pull in the
# related hubs the registry links them to.
_PANEL_CHILD_IDS: dict[str, tuple[str, ...]] = {
    # The six families, plus the two layer-2 hubs the registry also records
    # as `navigation = Mega menu` (SRV-DM-WEB, SRV-DM-SOC). Eight cards fill
    # the locked panel's 4-column grid in two clean rows, and every entity
    # the registry registered for the mega menu now has a place in it.
    "SRV-000": ("SRV-OOH", "SRV-DM", "SRV-DM-WEB", "SRV-DM-SOC",
                "SRV-GD", "SRV-PRN", "SRV-PHOTO", "SRV-CONS"),
    "SOL-000": ("SOL-PUBLIC", "SOL-B2B", "SOL-EXPO", "SOL-LOCAL"),
    "KNW-000": ("KNW-ART-*", "KNW-VID-*"),
}

# The portfolio panel. The archive's real filters have to come from real
# work-sample data, and no work-sample registry exists yet -- so rather than
# invent filter names, the cards are the service families the owner states
# the agency actually produces work in (BOLT outdoor, graphic design,
# websites, Instagram, video), each a view of the archive, plus the Projects
# registry, which the archive links to but never duplicates. Entity id ->
# (path under /portfolio/, label override or None).
_PORTFOLIO_CARDS: tuple[tuple[str, str | None], ...] = (
    ("SRV-OOH", "تبلیغات محیطی و BOLT"),
    ("SRV-GD", None),
    ("SRV-DM-WEB", "طراحی وب‌سایت"),
    ("SRV-DM-SOC", "اینستاگرام و سوشال"),
    ("SRV-PHOTO", "عکس و ویدئو"),
)

# Icons are Phosphor ids from blocks/_foundation/assets/icon-sprite.svg.
_ENTITY_ICONS: dict[str, str] = {
    "CORE-001": "icon-home",
    "SRV-000": "icon-services-nav",
    "SOL-000": "icon-solutions",
    "STR-000": "icon-structures",
    "INV-000": "icon-investment",
    "PRT-000": "icon-portfolio",
    "KNW-000": "icon-knowledge",
    "PRJ-000": "icon-projects",
    "CNT-000": "icon-contact",
    "SRV-OOH": "icon-fam-outdoor",
    "SRV-DM": "icon-fam-digital",
    "SRV-DM-WEB": "icon-fam-web",
    "SRV-DM-SOC": "icon-fam-social",
    "SRV-GD": "icon-fam-graphic",
    "SRV-PRN": "icon-fam-print",
    "SRV-PHOTO": "icon-fam-photo",
    "SRV-CONS": "icon-fam-consult",
    "SOL-PUBLIC": "icon-sol-public",
    "SOL-B2B": "icon-sol-industrial",
    "SOL-EXPO": "icon-sol-expo",
    "SOL-LOCAL": "icon-sol-local",
    "KNW-ART-*": "icon-article",
    "KNW-VID-*": "icon-fam-video",
}

# Nav labels, where the registry's `name_fa` is an internal architecture
# name rather than something a visitor should read. STR-000 is recorded as
# "سازه‌ها / استراکچر"; the label the owner approved in the nav is
# "سازه‌ها و تابلوها". The registry record is untouched -- this only governs
# how the entry is presented.
_NAV_LABELS: dict[str, str] = {
    "STR-000": "سازه‌ها و تابلوها",
}

# Where the registry's recorded candidate is 'PENDING' but the decision is
# narrowed to a known shortlist, the provisional path comes from that
# shortlist rather than from an English-name slug. The Knowledge hub's
# display name is settled; its URL is recorded as still undecided between
# /blog/ and /knowledge/, so /knowledge/ is used provisionally and the
# entry stays flagged. Same for the two Trust/Conversion endpoints, whose
# registry note is "only one canonical URL may remain" between two spellings.
# A derived slug comes from the registry's `name_en`, which for two entries
# is an architecture word rather than anything that belongs in a URL:
# "Website Ecosystem" and "Social Media Ecosystem" are named that way to
# make the point that the hub is wider than one service ("Website مترادف
# طراحی سایت نیست"), not to be typed by a visitor.
_SLUG_OVERRIDES: dict[str, str] = {
    "SRV-DM-WEB": "website",
    "SRV-DM-SOC": "social-media",
}

_SHORTLISTED_URLS: dict[str, str] = {
    "KNW-000": "/knowledge/",
    "ABT-000": "/about/",
    "CNT-000": "/contact/",
    "FAC-000": "/facilities/",
}

# The "see all" label for each panel's hero card. The locked markup renders
# this in `.mega-lead` -- a 250px paper card with the panel title, a note and
# this link -- which is the per-panel hero card the owner approved.
_ALL_LABELS: dict[str, str] = {
    "SRV-000": "دیدن همهٔ خدمات",
    "SOL-000": "دیدن همهٔ راهکارها",
    "STR-000": "دیدن همهٔ سازه‌ها",
    "INV-000": "مسیر کامل سرمایه‌گذاری",
    "PRT-000": "دیدن همهٔ نمونه‌کارها",
    "KNW-000": "ورود به مرکز دانش",
}

# One panel note per pillar. Each is the registry's own `primary_role` for
# that entity, written out as a sentence a visitor can read -- not new
# marketing copy, and not a claim the registry does not make.
_PANEL_NOTES: dict[str, str] = {
    "SRV-000": "شش خانوادهٔ خدمت، هر یک با زیرشاخه‌ها و مسیر اقدام خودش. "
               "اگر می‌دانید چه می‌خواهید، از همین‌جا وارد شوید.",
    "SOL-000": "دسته‌بندی بر اساس مسئله و نوع مخاطب، نه بر اساس فهرست خدمات. "
               "هر راهکار ترکیبی از چند خدمت است.",
    "STR-000": "هر خانواده سازه با ابعاد، محیط نصب و کاربرد خودش. "
               "برای دیدن مشخصات فنی کامل، یکی را باز کنید.",
    "INV-000": "مسیر مستقل سرمایه‌گذاری و مدل همکاری؛ "
               "از انتخاب مسیر تا امکان‌سنجی موقعیت و تعهدات طرفین.",
    "PRT-000": "ویترین خروجی‌های واقعی. هر نمونه‌کار به خدمت مرتبطش وصل است "
               "و اگر بخشی از پروژه‌ای بزرگ‌تر باشد، به صفحهٔ همان پروژه.",
    "KNW-000": "مقاله و ویدئو، به‌عنوان موجودیت‌های مستقل که به خدمات، "
               "سازه‌ها، پروژه‌ها و راهکارها وصل می‌شوند.",
}

# Notes on the cards whose destination is a hub rather than a single
# service. Family cards get a real, counted note instead (see _family_note).
_CARD_NOTES: dict[str, str] = {
    "SRV-DM-WEB": "چرخهٔ کامل ساخت، رشد و نگهداری وب‌سایت",
    "SRV-DM-SOC": "هاب خدمات شبکه‌های اجتماعی",
    "SRV-CONS": "تشخیص مسئله و هدایت به اقدام",
    "SOL-PUBLIC": "ترکیب خدمات سازمانی، سازه، پروژه و مسیر سرمایه‌گذاری",
    "SOL-B2B": "پکیج چندخدمتی برای شرکت و کارخانه",
    "SOL-EXPO": "بستهٔ زمانی و چندخدمتی نمایشگاه",
    "SOL-LOCAL": "راهکار رشد و دیده‌شدن محلی",
    "PRJ-000": "رجیستری پروژه‌های واقعی — مرجع کانونیکال هر پروژه",
    "KNW-ART-*": "پاسخ‌های دانشی و راهنماهای فنی",
    "KNW-VID-*": "ویدئو همراه متن و رونویسی",
}

_DIGITS_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _fa(number: int) -> str:
    return str(number).translate(_DIGITS_FA)


def _slug(entity: EntityRecord) -> str:
    """Registry entity -> a URL slug. 'Printing & Production' ->
    'printing-production'."""
    if entity.id in _SLUG_OVERRIDES:
        return _SLUG_OVERRIDES[entity.id]
    return re.sub(r"[^a-z0-9]+", "-", entity.name_en.lower()).strip("-")


def _resolve_url(entity: EntityRecord) -> tuple[str, bool]:
    """(href, provisional). A recorded candidate is used as recorded; a
    'PENDING' one gets a shortlisted or derived path, flagged either way."""
    candidate = (entity.url_candidate or "").strip()
    if candidate and candidate.upper() != "PENDING":
        # A dynamic collection records its pattern, e.g.
        # '/portfolio/{work-sample-slug}/'. The hub, not the pattern, is what
        # a menu links to.
        if "{" in candidate:
            return candidate.split("{", 1)[0], True
        return candidate, (entity.url_status or "").upper() != "KEEP"
    if entity.id in _SHORTLISTED_URLS:
        return _SHORTLISTED_URLS[entity.id], True
    return f"/{_slug(entity)}/", True


def _entities_by_id(registry_root=None) -> dict[str, EntityRecord]:
    return {entity.id: entity for entity in load_entities(registry_root)}


def _structure_cards(registry_root=None) -> list[dict[str, Any]]:
    """One representative, already-buildable structure per family, with a
    real context/dimension note -- never an invented description.

    This reuses ``structure_detail_spec._family_nav_cards`` rather than
    reimplementing it: that is the builder whose output the owner already
    approved, and it owns the registry's Persian label maps and the
    dimension parser (which has a real quirk -- some rows' raw 'WxH' string
    contradicts their own orientation field). Imported inside the function
    because ``structure_detail_spec`` resolves its shell from here.
    """
    from .structure_detail_spec import _family_nav_cards

    return _family_nav_cards(registry_root)


def _family_note(family: str, services) -> str:
    """A counted note from the service registry: how many services are in
    this family and across how many subgroups. Real numbers, so the card
    says something true rather than something written to fill the slot."""
    rows = [service for service in services if service.family == family]
    if not rows:
        return "مشاهدهٔ خدمات این خانواده"
    subgroups = {service.subgroup for service in rows if service.subgroup}
    if len(subgroups) > 1:
        return f"{_fa(len(rows))} خدمت در {_fa(len(subgroups))} زیرشاخه"
    return f"{_fa(len(rows))} خدمت"


def _investment_cards() -> list[dict[str, Any]]:
    """The investment panel's cards are the real sections of the approved
    investment page, addressed absolutely so they work from any page -- not
    bare in-page anchors, which only resolve on that one page."""
    base = "/investment/"
    return [
        {"label": "مشارکت سرمایه‌گذاری", "href": f"{base}#paths",
         "icon": "icon-partnership", "note": "سرمایه و اجرا با شریک؛ سهم درآمد قراردادی"},
        {"label": "خرید مستقیم سازه", "href": f"{base}#structures",
         "icon": "icon-purchase", "note": "مالکیت پس از تحویل، با بودجهٔ ساخت"},
        {"label": "امکان‌سنجی موقعیت", "href": f"{base}#assessment",
         "icon": "icon-pin-area", "note": "بررسی فنی، حقوقی و بازارِ یک موقعیت"},
        {"label": "فرایند و تعهدات", "href": f"{base}#process",
         "icon": "icon-process", "note": "مراحل کار و تعهدات دو طرف، پیش از شروع"},
        {"label": "پرسش‌های متداول", "href": f"{base}#faq",
         "icon": "icon-faq", "note": "پاسخ پرسش‌های حقوقی، مالی و اجرایی"},
    ]


def _portfolio_cards(entities: Mapping[str, EntityRecord]) -> list[dict[str, Any]]:
    """Archive views for the families the agency really has work in, then the
    Projects registry. Every href lives under /portfolio/, so a work sample
    never claims a project's canonical URL -- the registry's own rule is that
    the archive may show a project but never republishes it."""
    cards: list[dict[str, Any]] = []
    for entity_id, label in _PORTFOLIO_CARDS:
        entity = entities[entity_id]
        cards.append({
            "label": label or entity.name_fa,
            "href": f"/portfolio/{_slug(entity)}/",
            "icon": _ENTITY_ICONS[entity_id],
            "note": "نمونه‌کارهای این خانواده",
            "url_status": "PENDING_AUDIT",
            "provisional": True,
        })
    projects = entities["PRJ-000"]
    href, _ = _resolve_url(projects)
    cards.append({
        "label": projects.name_fa,
        "href": href,
        "icon": _ENTITY_ICONS["PRJ-000"],
        "note": _CARD_NOTES["PRJ-000"],
        "url_status": projects.url_status or "PENDING_AUDIT",
        "provisional": True,
    })
    return cards


def _knowledge_cards(entities: Mapping[str, EntityRecord]) -> list[dict[str, Any]]:
    """The registry's Knowledge children are the dynamic article and video
    item patterns, not destinations. A menu links to their listings, which
    hang off whichever hub path the URL audit settles on."""
    hub, _ = _resolve_url(entities["KNW-000"])
    return [
        {"label": "مقاله‌ها", "href": f"{hub}articles/", "icon": _ENTITY_ICONS["KNW-ART-*"],
         "note": _CARD_NOTES["KNW-ART-*"], "url_status": "PENDING_URL_AUDIT",
         "provisional": True},
        {"label": "ویدئوها", "href": f"{hub}videos/", "icon": _ENTITY_ICONS["KNW-VID-*"],
         "note": _CARD_NOTES["KNW-VID-*"], "url_status": "PENDING_URL_AUDIT",
         "provisional": True},
    ]


def _nav_entry(entity: EntityRecord, children: list[dict[str, Any]]) -> dict[str, Any]:
    href, provisional = _resolve_url(entity)
    entry: dict[str, Any] = {
        "label": _NAV_LABELS.get(entity.id, entity.name_fa),
        "href": href,
        "icon": _ENTITY_ICONS.get(entity.id, "icon-structures"),
    }
    if children:
        entry["note"] = _PANEL_NOTES[entity.id]
        entry["all_label"] = _ALL_LABELS[entity.id]
        entry["children"] = children
    if provisional:
        entry["url_status"] = entity.url_status or "PENDING_AUDIT"
        entry["provisional"] = True
    return entry


def site_nav(registry_root=None) -> list[dict[str, Any]]:
    """The approved nav row: Home, then six mega panels, each with a hero
    card and real cards. Built from the registry, in registry order."""
    entities = _entities_by_id(registry_root)
    services = tuple(load_services(registry_root))

    def cards_for(panel_id: str) -> list[dict[str, Any]]:
        if panel_id == "STR-000":
            return _structure_cards(registry_root)
        if panel_id == "INV-000":
            return _investment_cards()
        if panel_id == "PRT-000":
            return _portfolio_cards(entities)
        if panel_id == "KNW-000":
            return _knowledge_cards(entities)
        cards = []
        for child_id in _PANEL_CHILD_IDS.get(panel_id, ()):
            child = entities[child_id]
            href, provisional = _resolve_url(child)
            note = _CARD_NOTES.get(child_id)
            if note is None and panel_id == "SRV-000":
                note = _family_note(child.name_fa, services)
            card: dict[str, Any] = {
                "label": child.name_fa,
                "href": href,
                "icon": _ENTITY_ICONS.get(child_id, "icon-services"),
                "note": note or child.primary_role,
            }
            if provisional:
                card["url_status"] = child.url_status or "PENDING_AUDIT"
                card["provisional"] = True
            cards.append(card)
        return cards

    nav = [_nav_entry(entities[_HOME_ID], [])]
    nav.extend(_nav_entry(entities[panel_id], cards_for(panel_id)) for panel_id in _PANEL_IDS)
    return nav


def _bottom_nav(registry_root=None, active_href: str | None = None) -> dict[str, Any]:
    """خانه · نمونه‌کارها · سازه‌ها · سرمایه‌گذاری · تماس — the five entries
    the owner chose. Icons come in idle/active pairs, as the locked bar's
    filled active state requires.

    ``active_href`` marks the section the current page sits in, which is
    what the liquid bubble rests on. This is page state, not navigation:
    the five entries, their order, labels, icons and hrefs are identical
    everywhere, and only the flag differs. Without it the bubble defaults
    to the first entry on every page.
    """
    entities = _entities_by_id(registry_root)
    order = ("CORE-001", "PRT-000", "STR-000", "INV-000", "CNT-000")
    labels = {"STR-000": "سازه‌ها", "PRT-000": "نمونه‌کارها", "CNT-000": "تماس"}
    entries = []
    for entity_id in order:
        entity = entities[entity_id]
        href, provisional = _resolve_url(entity)
        icon = _ENTITY_ICONS[entity_id]
        entry: dict[str, Any] = {
            "href": href,
            "icon": icon,
            "icon_active": f"{icon}-active",
            "label": labels.get(entity_id, entity.name_fa),
        }
        if provisional:
            entry["url_status"] = entity.url_status or "PENDING_AUDIT"
            entry["provisional"] = True
        if active_href and href == active_href:
            entry["active"] = True
        entries.append(entry)
    return {"entries": entries}


def _site_footer(registry_root=None) -> dict[str, Any]:
    """The footer carries the registry entries that are not in the nav row:
    the Trust layer, the city hub and the capability page."""
    entities = _entities_by_id(registry_root)

    def link(entity_id: str, label: str | None = None) -> dict[str, Any]:
        entity = entities[entity_id]
        href, _ = _resolve_url(entity)
        return {"label": label or entity.name_fa, "href": href}

    return {
        "brand": _BRAND,
        "summary": "از امکان‌سنجی و سرمایه‌گذاری تا تولید، نصب و بهره‌برداری رسانه‌های محیطی.",
        "columns": [
            {
                "title": "خدمات و راهکارها",
                "links": [link("SRV-000"), link("SOL-000"),
                          link("STR-000", "همهٔ سازه‌ها و تابلوها"), link("INV-000")],
            },
            {
                "title": "کارنامه",
                "links": [link("PRT-000"), link("PRJ-000"), link("KNW-000"), link("CITY-000")],
            },
            {
                "title": "دربارهٔ چتر قرمز",
                "links": [link("ABT-000"), link("LIC-000"), link("FAC-000"), link("CNT-000")],
            },
        ],
        "contact": {"title": "شروع گفت‌وگو", "label": "درخواست بررسی موقعیت ←"},
        "copyright": "© چتر قرمز؛ همه حقوق محفوظ است.",
    }


def site_shell(registry_root=None, active_href: str | None = None) -> dict[str, Any]:
    """The whole shell. One definition; every page gets this one.

    ``active_href`` only marks which bottom-nav section the page is in.
    """
    return {
        "site-header": {
            "brand": _BRAND,
            "cta": {"label": "درخواست بررسی", "href": "#review"},
            "nav": site_nav(registry_root),
        },
        "site-footer": _site_footer(registry_root),
        "bottom-nav": _bottom_nav(registry_root, active_href),
    }


def provisional_nav_urls(registry_root=None) -> list[tuple[str, str, str]]:
    """(label, href, url_status) for every nav destination whose path is not
    settled yet. This is the list the live URL audit has to close."""
    found: dict[str, tuple[str, str, str]] = {}

    def walk(entries: Any) -> None:
        for entry in entries:
            if entry.get("provisional"):
                found.setdefault(
                    entry["href"], (entry["label"], entry["href"], entry["url_status"])
                )
            walk(entry.get("children", ()))

    shell = site_shell(registry_root)
    walk(shell["site-header"]["nav"])
    walk(shell["bottom-nav"]["entries"])
    return sorted(found.values(), key=lambda row: row[1])
