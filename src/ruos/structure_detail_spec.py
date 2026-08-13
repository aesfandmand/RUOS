"""Build a real Structure Detail page spec from registry data.

Every field here traces to a real source: the structure registry
(dimensions, orientation, context...), the persona journey matrix (hero
message, conversion intent), the service registry (cross-sell services),
or the persona registry (real researched buyer objections, answered
honestly using only what the page itself already states). Nothing here
is invented marketing copy, a fabricated statistic, or a made-up
warranty/experience claim. A structure whose registry record does not
yet carry enough attributes to fill ``structure-specs``' minimum of
three rows is rejected rather than padded with fabricated specs; see
``StructureDetailSpecError``.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Mapping

from .architecture_registry import ServiceRecord, StructureRecord, load_services, load_structures
from .content_draft import lorem_ipsum_of_length
from .persona_registry import journey_rows_for_entry_page, load_personas

# Real, non-AI installation photography, organized by structure ID — see
# media/structures/README.md for provenance (Didanshow, the owner's own OOH
# company) and the honesty rule: caption as a real installation sample,
# never implied to be Chatreghermez's own client work. A structure with no
# directory here has no confirmed real photo yet, so it gets the honest
# CSS-drawn dimension diagram instead — never a stock or generated image.
_MEDIA_ROOT = Path(__file__).resolve().parents[2] / "media" / "structures"
_MEDIA_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

_DEFAULT_CTA_LABEL = "درخواست استعلام فنی"

_ORIENTATION_FA = {"vertical": "عمودی", "horizontal": "افقی"}
_CONTEXT_FA = {
    "outdoor": "محیط شهری (بیرون)",
    "outdoor_organizational": "محیط سازمانی (بیرون)",
    "indoor": "داخل ساختمان",
}
_FACE_COUNT_FA = {"one_or_two": "یک یا دو رو، بسته به موقعیت"}
_MOUNTING_FA = {"wall": "نصب دیواری", "standing": "استند ایستاده"}

# Real service_landing-registry IDs curated per structure family — never invented
# names. A family missing here falls back to _DEFAULT_SERVICE_IDS.
_SERVICE_IDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "بیلبورد": ("GD-011", "PRN-002", "OOH-003"),
    "استرابورد": ("GD-009", "PRN-002", "OOH-003"),
    "برایت‌بورد": ("GD-013", "PRN-004", "OOH-003"),
    "لایت‌باکس": ("GD-013", "PRN-005", "OOH-003"),
    "لایت‌برد": ("GD-013", "PRN-004", "OOH-003"),
    "لایت‌باکس ایندور": ("GD-013", "PRN-005"),
    "سازه سازمانی": ("GD-009", "PRN-002"),
}
_DEFAULT_SERVICE_IDS = ("GD-009", "PRN-002", "OOH-003")

_STRUCTURES_HUB_URL = "/structures/"


class StructureDetailSpecError(ValueError):
    """Raised when a structure's registry record cannot yet support a real spec."""


def _format_number(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


def _parse_dimensions(raw: str) -> tuple[float, float, str] | None:
    """'5x10' -> (5, 10, 'متر'); '180x120cm' -> (180, 120, 'سانتی‌متر')."""
    unit = "متر"
    value = raw
    if raw.endswith("cm"):
        unit = "سانتی‌متر"
        value = raw[: -len("cm")]
    parts = value.lower().split("x")
    if len(parts) != 2:
        return None
    try:
        width, height = float(parts[0]), float(parts[1])
    except ValueError:
        return None
    return width, height, unit


def _dimension_label(raw: str | None) -> str | None:
    parsed = _parse_dimensions(raw) if raw else None
    if not parsed:
        return None
    width, height, unit = parsed
    return f"{_format_number(width)}×{_format_number(height)} {unit}"


def _diagram(raw: str | None, orientation: str | None) -> dict[str, Any] | None:
    """The registry's raw 'WxH' dimension string is not a reliable source of
    shape on its own — some rows (e.g. STR-002, افقی ۶×۱۲) give a ratio that
    contradicts their own orientation label. `orientation` is the
    owner-authored field and wins: the drawn box is always wider-than-tall
    for 'horizontal' and taller-than-wide for 'vertical', swapping the two
    parsed numbers if the raw string disagrees with it."""
    parsed = _parse_dimensions(raw) if raw else None
    if not parsed:
        return None
    width, height, unit = parsed
    if orientation == "horizontal" and width < height:
        width, height = height, width
    elif orientation == "vertical" and height < width:
        width, height = height, width
    return {
        "ratio": f"{width} / {height}",
        "width_label": f"{_format_number(width)} {unit}",
        "height_label": f"{_format_number(height)} {unit}",
        "aria_label": f"نمودار مقیاس {_format_number(width)} در {_format_number(height)} {unit}",
    }


def _specs(structure: StructureRecord) -> list[dict[str, str]]:
    rows = [{"label": "خانواده سازه", "value": structure.family}]
    if structure.context:
        rows.append({"label": "محیط نصب", "value": _CONTEXT_FA.get(structure.context, structure.context)})
    if structure.orientation:
        rows.append({"label": "جهت", "value": _ORIENTATION_FA.get(structure.orientation, structure.orientation)})
    dimension_label = _dimension_label(structure.dimensions)
    if dimension_label:
        rows.append({"label": "ابعاد", "value": dimension_label})
    if structure.face_count:
        rows.append({"label": "تعداد رو", "value": _FACE_COUNT_FA.get(structure.face_count, structure.face_count)})
    if structure.mounting:
        rows.append({"label": "نوع نصب", "value": _MOUNTING_FA.get(structure.mounting, structure.mounting)})
    return rows


# One Phosphor sprite id per real structure family, so every mega-menu
# card carries an icon that actually means something for that family
# rather than a repeated generic glyph. Families are the real registry
# values; a new family falls back to the generic structures icon.
_FAMILY_ICONS: dict[str, str] = {
    "بیلبورد": "icon-fam-billboard",
    "استرابورد": "icon-fam-straboard",
    "لایت‌باکس": "icon-fam-lightbox",
    "لایت‌برد": "icon-fam-lightboard",
    "برایت‌بورد": "icon-fam-brightboard",
    "سازه سازمانی": "icon-fam-org",
    "لایت‌باکس ایندور": "icon-fam-indoor",
    "عرشه پل": "icon-fam-bridge",
}


def _family_nav_cards(registry_root=None) -> list[dict[str, str]]:
    """Real category cards for the header mega-menu: one representative,
    already-buildable structure per family, with a real context/dimension
    note — never an invented description. Same card set on every page, per
    the owner's request that the mega-menu look identical everywhere."""
    seen: dict[str, StructureRecord] = {}
    for structure in load_structures(registry_root):
        if structure.family in seen or len(_specs(structure)) < 3:
            continue
        seen[structure.family] = structure
    cards = []
    for family, structure in seen.items():
        note_parts = [
            part for part in (
                _CONTEXT_FA.get(structure.context, structure.context),
                _dimension_label(structure.dimensions),
            ) if part
        ]
        cards.append({
            "label": family,
            "href": structure.url,
            "icon": _FAMILY_ICONS.get(family, "icon-structures"),
            "note": " · ".join(note_parts) if note_parts else "مشاهده مشخصات",
        })
    return cards


def _real_shell(registry_root=None) -> dict[str, Any]:
    """Site chrome with real, working site-wide URLs — not the page-specific
    in-page anchors urban-investment.json's shell uses (#structures, #model...),
    which only make sense on that one page and are broken everywhere else."""
    brand = {
        "name": "چتر قرمز",
        "tagline": "به آسمان سلام کن",
        "aria": "چتر قرمز، ابتدای صفحه",
        "logo_alt": "نشان چتر قرمز",
    }
    return {
        "site-header": {
            "brand": brand,
            "cta": {"label": "درخواست بررسی", "href": "#review"},
            "nav": [
                {"label": "خانه", "href": "/", "icon": "icon-home"},
                {
                    "label": "سازه‌ها و تابلوها",
                    "href": _STRUCTURES_HUB_URL,
                    "icon": "icon-structures",
                    "note": "هر خانواده سازه با ابعاد، محیط نصب و کاربرد خودش. "
                            "برای دیدن مشخصات فنی کامل، یکی را باز کنید.",
                    "all_label": "دیدن همهٔ سازه‌ها",
                    "children": _family_nav_cards(registry_root),
                },
                {"label": "سرمایه‌گذاری", "href": "/investment/", "icon": "icon-investment"},
            ],
        },
        "site-footer": {
            "brand": brand,
            "summary": "از امکان‌سنجی و سرمایه‌گذاری تا تولید، نصب و بهره‌برداری رسانه‌های محیطی.",
            "columns": [
                {
                    "title": "راهکارها",
                    "links": [
                        {"label": "همهٔ سازه‌ها و تابلوها", "href": _STRUCTURES_HUB_URL},
                        {"label": "سرمایه‌گذاری", "href": "/investment/"},
                    ],
                },
            ],
            "contact": {"title": "شروع گفت‌وگو", "label": "درخواست بررسی موقعیت ←"},
            "copyright": "© چتر قرمز؛ همه حقوق محفوظ است.",
        },
        "bottom-nav": {
            "entries": [
                {"href": "/", "icon": "icon-home", "icon_active": "icon-home-active",
                 "label": "خانه"},
                {"href": _STRUCTURES_HUB_URL, "icon": "icon-structures",
                 "icon_active": "icon-structures-active", "label": "سازه‌ها", "active": True},
                {"href": "/investment/", "icon": "icon-investment",
                 "icon_active": "icon-investment-active", "label": "سرمایه‌گذاری"},
                {"href": "#review", "icon": "icon-rfq", "icon_active": "icon-rfq-active",
                 "label": "استعلام"},
            ]
        },
    }


def _related_structures(structure: StructureRecord, all_structures: tuple[StructureRecord, ...],
                         buildable_ids: set[str]) -> list[dict[str, str]]:
    items = []
    for other in all_structures:
        if other.id == structure.id or other.family != structure.family or other.id not in buildable_ids:
            continue
        meta_parts = [p for p in (_dimension_label(other.dimensions), _CONTEXT_FA.get(other.context, other.context)) if p]
        items.append({
            "title": other.name_fa,
            "meta": " · ".join(meta_parts) if meta_parts else other.family,
            "href": other.url,
        })
    return items


def _cross_sell_services(structure: StructureRecord, services_by_id: Mapping[str, ServiceRecord]) -> list[dict[str, str]]:
    ids = _SERVICE_IDS_BY_FAMILY.get(structure.family, _DEFAULT_SERVICE_IDS)
    items = []
    for service_id in ids:
        service = services_by_id.get(service_id)
        if service is None:
            continue
        items.append({"title": service.name, "note": service.subgroup or service.family})
    return items


def _faq(structure: StructureRecord, registry_root=None) -> list[dict[str, str]]:
    """Real, researched buyer objections (Public Project Steward persona)
    answered honestly with only what this page already states or a real
    next step — never a fabricated year count, certification or warranty
    figure."""
    core, _ = load_personas(registry_root)
    steward = next((p for p in core if p.id == "PERSONA-004"), None)
    dimension_label = _dimension_label(structure.dimensions)
    questions = [
        {
            "q": f"ابعاد و مشخصات فنی {structure.name_fa} چیست؟",
            "a": (
                f"مشخصات کامل (خانواده، محیط نصب، جهت{'، ابعاد ' + dimension_label if dimension_label else ''}) "
                "در بخش «مشخصات فنی» همین صفحه آمده است."
            ),
        },
        {
            "q": "زمان ساخت و نصب این سازه چقدر طول می‌کشد؟",
            "a": "زمان دقیق به موقعیت، شرایط دسترسی و حجم پروژه بستگی دارد؛ برای برآورد واقعی، مشخصات پروژه را در فرم استعلام ثبت کنید.",
        },
        {
            "q": "برای پروژه‌های سازمانی و شهرداری چه مدارکی لازم است؟",
            "a": "مدارک ارزیابی، سابقه اجرایی و توان فنی از طریق فرآیند استعلام رسمی ارائه می‌شود؛ برای شروع، درخواست بررسی موقعیت را ثبت کنید.",
        },
        {
            "q": "آیا امکان تغییر ابعاد یا مدل این سازه هست؟",
            "a": f"بله؛ سایر مدل‌های خانواده «{structure.family}» با ابعاد و کاربرد متفاوت در بخش «سازه‌های مرتبط» همین صفحه قابل‌مشاهده‌اند.",
        },
        {
            "q": "طراحی و چاپ روکش این سازه هم انجام می‌شود؟",
            "a": "بله؛ خدمات طراحی و چاپ مرتبط با این نوع سازه در بخش «خدمات مرتبط» همین صفحه فهرست شده‌اند.",
        },
    ]
    return questions


def _structure_media_dir(structure: StructureRecord, media_root: Path | None = None) -> Path:
    return (media_root or _MEDIA_ROOT) / structure.id


def _gallery_items(structure: StructureRecord, media_root: Path | None = None) -> list[dict[str, str]]:
    directory = _structure_media_dir(structure, media_root)
    if not directory.is_dir():
        return []
    items = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() not in _MEDIA_EXTENSIONS:
            continue
        items.append({
            "src": f"assets/{path.name}",
            "alt": structure.name_fa,
        })
    return items


def copy_structure_media(structure: StructureRecord, output_dir: Path, media_root: Path | None = None) -> list[Path]:
    """Copy this structure's real photos (if any) into a composed page's
    output assets/ directory. Call after render_page + writing the page's
    other assets. Returns the paths written, empty if this structure has
    no real photos yet."""
    directory = _structure_media_dir(structure, media_root)
    if not directory.is_dir():
        return []
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() not in _MEDIA_EXTENSIONS:
            continue
        destination = assets_dir / path.name
        shutil.copyfile(path, destination)
        written.append(destination)
    return written


_PERSIAN_DIGIT_MAP = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _persian_digits(value: int) -> str:
    return str(value).translate(_PERSIAN_DIGIT_MAP)


# One hero-stat icon per real spec row, keyed on the same labels `_specs()`
# emits — so a stat only ever appears when the registry actually carries
# that attribute. Ordered by how much a hero stat strip actually needs to
# say, not by `_specs()`'s own row order: "خانواده سازه" and "محیط نصب"
# are skipped entirely because both are already carried by the title and
# the eyebrow, so repeating them as a stat would waste one of only three
# slots on something the reader already read a second ago.
_HERO_STAT_PRIORITY: tuple[tuple[str, str], ...] = (
    ("ابعاد", "icon-ruler"),
    ("جهت", "icon-orientation"),
    ("تعداد رو", "icon-faces"),
    ("نوع نصب", "icon-structures"),
    ("محیط نصب", "icon-location"),
)
_MAX_HERO_SLIDES = 3


def _hero_stats(specs: list[dict[str, str]]) -> list[dict[str, str]]:
    by_label = {row["label"]: row["value"] for row in specs}
    stats = []
    for label, icon in _HERO_STAT_PRIORITY:
        value = by_label.get(label)
        if value is None:
            continue
        stats.append({"value": value, "label": label, "icon": icon})
        if len(stats) == 3:
            break
    return stats


def build_product_page_spec(
    structure: StructureRecord,
    shell: Mapping[str, Any] | None = None,
    registry_root=None,
    media_root: Path | None = None,
) -> dict[str, Any]:
    """Build a full product-archetype page (design model v1.1, the straboard
    shape) for ANY structure that has enough real registry data — not just
    the ones an owner has hand-authored a content brief for.

    Sections that need owner-supplied engineering/marketing prose
    (numbered-features, parts-zigzag, checklist-section, workshop-gallery,
    knowledge-carousel) are never fabricated here; they simply don't run
    for a structure without a brief. What always ships is the part that
    traces to the registry: an opening scene, the real spec sheet, real
    installation photos when they exist, real sibling models, real
    cross-sell services, real FAQ, and the lead form. See
    ``build_structure_detail_spec`` for the older, narrower version of the
    same idea and ``05-rules/website/red-umbrella-design-model-v1.md`` for
    why the richer sections are conditional rather than padded.
    """
    specs = _specs(structure)
    if len(specs) < 3:
        raise StructureDetailSpecError(
            f"{structure.id} ({structure.name_fa}) only has {len(specs)} registry attribute(s) "
            "recorded — not enough for a real spec sheet yet. Needs richer registry data, not "
            "invented specs."
        )

    slug = structure.url.strip("/").rsplit("/", 1)[-1]
    journey_rows = journey_rows_for_entry_page(structure.url, registry_root)
    journey = journey_rows[0] if journey_rows else None

    all_structures = load_structures(registry_root)
    buildable_ids = {other.id for other in all_structures if len(_specs(other)) >= 3}
    related = _related_structures(structure, all_structures, buildable_ids)

    services_by_id = {s.id: s for s in load_services(registry_root)}
    cross_sell = _cross_sell_services(structure, services_by_id)

    all_photos = _gallery_items(structure, media_root)
    hero_photos, gallery_photos = all_photos[:_MAX_HERO_SLIDES], all_photos[_MAX_HERO_SLIDES:]

    if hero_photos:
        slides = [
            {"label": f"اسلاید {_persian_digits(i)}", "alt": photo["alt"], "src": photo["src"],
             "caption": structure.family}
            for i, photo in enumerate(hero_photos, start=1)
        ]
    else:
        # No confirmed real photo yet: one honest placeholder slide, never a
        # stock or generated image (design model §4).
        slides = [{"label": "تصویر سازه", "alt": structure.name_fa}]

    blocks = [
        {
            "block": "product-hero",
            "id": "top",
            "data": {
                "breadcrumb": [
                    {"label": "خانه", "href": "/"},
                    {"label": "سازه‌های تبلیغات محیطی", "href": _STRUCTURES_HUB_URL},
                ],
                "title": structure.name_fa,
                "lead": journey["hero_message"] if journey else "",
                "slides": slides,
                "primary": {"label": "استعلام قیمت", "href": "#quote"},
                "secondary": {"label": "دیدن مشخصات فنی", "href": "#specs"},
                "stats": _hero_stats(specs),
                "count": _persian_digits(len(slides)),
            },
        },
        {
            "block": "structure-specs",
            "id": "specs",
            "data": {
                "eyebrow": "مشخصات",
                "title": f"مشخصات فنی {structure.name_fa}",
                "specs": specs,
            },
        },
    ]

    if len(gallery_photos) >= 2:
        blocks.append({
            "block": "structure-gallery",
            "id": "gallery",
            "data": {
                "eyebrow": "نمونهٔ نصب واقعی",
                "title": f"{structure.name_fa} در محیط واقعی",
                "lead": "چند نمونه از نصب واقعی این خانواده سازه در فضای شهری — آرشیو دیده‌شو.",
                "items": gallery_photos,
            },
        })

    if len(related) >= 2:
        blocks.append({
            "block": "structure-related",
            "id": "related",
            "data": {
                "eyebrow": "سازه‌های مرتبط",
                "title": f"سایر مدل‌های خانواده «{structure.family}»",
                "lead": "ابعاد و کاربرد جایگزین را ببینید.",
                "all_link": {"label": "دیدن همهٔ سازه‌ها", "href": _STRUCTURES_HUB_URL},
                "items": related,
            },
        })

    if len(cross_sell) >= 2:
        blocks.append({
            "block": "structure-services",
            "id": "services",
            "data": {
                "eyebrow": "خدمات مرتبط",
                "title": "کنار این سازه چه خدماتی لازم دارید؟",
                "lead": "طراحی، چاپ و برنامه‌ریزی رسانه — هرکدام لازم بود، جدا سفارش بدهید.",
                "services": cross_sell,
            },
        })

    blocks.append({
        "block": "faq-section-final",
        "id": "faq",
        "data": {
            "eyebrow": "سؤالات متداول",
            "title": f"سؤالات متداول {structure.name_fa}",
            "lead": "این سؤالات از پژوهش رفتار خرید سازمانی/شهرداری چتر قرمز جمع‌آوری شده‌اند.",
            "questions": _faq(structure, registry_root),
        },
    })

    blocks.append({
        "block": "lead-form",
        "id": "quote",
        "data": {
            "eyebrow": "استعلام و مشاوره",
            "title": f"برای پروژه شما {structure.name_fa} مناسب است؟",
            "lead": "برای شروع بررسی، همین سه مورد کافی است. بعد از دریافت اطلاعات، جزئیات فنی، قیمت و شرایط اجرا بررسی می‌شود.",
            "fields": [
                {"name": "name", "label": "نام", "type": "text", "inputmode": "text",
                 "autocomplete": "name", "placeholder": "مثلاً علی", "icon": "icon-user"},
                {"name": "phone", "label": "شماره تماس", "type": "tel", "inputmode": "tel",
                 "autocomplete": "tel", "placeholder": "۰۹۱۲۳۴۵۶۷۸۹", "icon": "icon-phone"},
                {"name": "project", "label": "محل یا نوع پروژه", "multiline": True,
                 "placeholder": "مثلاً شهرک صنعتی، مجتمع تجاری، پروژه شهری یا نام شهر",
                 "icon": "icon-pin-area"},
            ],
            "submit": "ثبت درخواست بررسی",
        },
    })

    return {
        "slug": slug,
        "lang": "fa",
        "direction": "rtl",
        "title": f"{structure.name_fa} | مشخصات فنی و اجرا | چتر قرمز",
        "description": f"{structure.name_fa}: مشخصات فنی، ابعاد و مسیر اجرای پروژه از چتر قرمز.",
        "canonical": f"https://chatreghermez.ir{structure.url}",
        "shell": dict(shell) if shell else _real_shell(registry_root),
        "blocks": blocks,
    }


def build_structure_detail_spec(
    structure: StructureRecord,
    shell: Mapping[str, Any] | None = None,
    registry_root=None,
    media_root: Path | None = None,
) -> dict[str, Any]:
    specs = _specs(structure)
    if len(specs) < 3:
        raise StructureDetailSpecError(
            f"{structure.id} ({structure.name_fa}) only has {len(specs)} registry attribute(s) "
            "recorded — not enough for a real spec sheet yet. Needs richer registry data, not "
            "invented specs."
        )

    slug = structure.url.strip("/").rsplit("/", 1)[-1]
    journey_rows = journey_rows_for_entry_page(structure.url, registry_root)
    journey = journey_rows[0] if journey_rows else None

    all_structures = load_structures(registry_root)
    buildable_ids = set()
    for other in all_structures:
        if len(_specs(other)) >= 3:
            buildable_ids.add(other.id)
    related = _related_structures(structure, all_structures, buildable_ids)

    services_by_id = {s.id: s for s in load_services(registry_root)}
    cross_sell = _cross_sell_services(structure, services_by_id)

    all_photos = _gallery_items(structure, media_root)
    # A photo used as the hero doesn't need to repeat as a gallery card too —
    # reserve it for the hero only when enough remain to still clear the
    # gallery block's own minimum of 2 real photos.
    if len(all_photos) >= 3:
        hero_image, gallery_items = dict(all_photos[0]), all_photos[1:]
    elif len(all_photos) == 1:
        hero_image, gallery_items = dict(all_photos[0]), []
    else:
        hero_image, gallery_items = None, all_photos

    blocks = [
        {
            "block": "structure-hero",
            "id": "top",
            "data": {
                "eyebrow": structure.family,
                "title": structure.name_fa,
                "lead": journey["hero_message"] if journey else "",
                "dimension_label": _dimension_label(structure.dimensions),
                "diagram": None if hero_image else _diagram(structure.dimensions, structure.orientation),
                "image": hero_image,
                "primary": {"label": "درخواست بررسی فنی و قیمت", "href": "#review"},
            },
        },
        {
            "block": "structure-specs",
            "id": "specs",
            "data": {
                "eyebrow": "مشخصات",
                "title": f"مشخصات فنی {structure.name_fa}",
                "specs": specs,
            },
        },
    ]

    if len(gallery_items) >= 2:
        blocks.append({
            "block": "structure-gallery",
            "id": "gallery",
            "data": {
                "eyebrow": "نمونهٔ نصب واقعی",
                "title": f"{structure.name_fa} در محیط واقعی",
                "lead": "چند نمونه از نصب واقعی این خانواده سازه در فضای شهری — آرشیو دیده‌شو.",
                "items": gallery_items,
            },
        })

    if len(related) >= 2:
        blocks.append({
            "block": "structure-related",
            "id": "related",
            "data": {
                "eyebrow": "سازه‌های مرتبط",
                "title": f"سایر مدل‌های خانواده «{structure.family}»",
                "lead": "ابعاد و کاربرد جایگزین را ببینید.",
                "all_link": {"label": "دیدن همهٔ سازه‌ها", "href": _STRUCTURES_HUB_URL},
                "items": related,
            },
        })

    if len(cross_sell) >= 2:
        blocks.append({
            "block": "structure-services",
            "id": "services",
            "data": {
                "eyebrow": "خدمات مرتبط",
                "title": "کنار این سازه چه خدماتی لازم دارید؟",
                "lead": "طراحی، چاپ و برنامه‌ریزی رسانه — هرکدام لازم بود، جدا سفارش بدهید.",
                "services": cross_sell,
            },
        })

    blocks.append({
        "block": "faq-section-final",
        "id": "faq",
        "data": {
            "eyebrow": "پرسش‌ها",
            "title": f"پرسش‌های پرتکرار دربارهٔ {structure.name_fa}",
            "lead": "این سؤالات از پژوهش رفتار خرید سازمانی/شهرداری چتر قرمز جمع‌آوری شده‌اند.",
            "questions": _faq(structure, registry_root),
        },
    })

    blocks.append({
        "block": "review-gate",
        "id": "review",
        "data": {
            "eyebrow": "قدم بعدی",
            "title": "برای این سازه استعلام فنی و قیمت بگیرید.",
            "body": "ابعاد، محل نصب و شرایط پروژه را بگویید تا بررسی فنی و برآورد اجرا برایتان آماده شود.",
            "primary": {"label": journey["conversion"] if journey else _DEFAULT_CTA_LABEL},
            "secondary": {"label": "دیدن دوبارهٔ مشخصات ↑", "href": "#top"},
        },
    })

    return {
        "slug": slug,
        "lang": "fa",
        "direction": "rtl",
        "title": f"{structure.name_fa} | مشخصات فنی و اجرا | چتر قرمز",
        "description": f"{structure.name_fa}: مشخصات فنی، ابعاد و مسیر اجرای پروژه از چتر قرمز.",
        "canonical": f"https://chatreghermez.ir{structure.url}",
        "shell": dict(shell) if shell else _real_shell(registry_root),
        "blocks": blocks,
    }


# ── the always-complete draft archetype ─────────────────────────────────
# Per the owner's explicit instruction (2026-08-13): the engine should make
# every effort to source real content, and where none exists, fill the slot
# with real Lorem Ipsum and tag it a placeholder rather than omit the
# section. This is §18's honest, registry-only spine (build_product_page_spec,
# untouched, still the pure/tested/documented function) PLUS the rich
# sections (numbered-features, parts-zigzag, checklist-section, compare-cards)
# that §18 deliberately left out for lack of an owner brief. See design
# model §19/§20 and content-voice-v1.md for why a Lorem Ipsum paragraph is
# the no-fabrication rule applied to prose, not a relaxation of it.
#
# Block order below is load-bearing, not cosmetic: it is the only ordering
# of (2 guaranteed process-family blocks + compare-cards + services? +
# checklist + gallery? + faq) that keeps every surface run at or under
# block_composer.MAX_CONSECUTIVE_SURFACE (2) regardless of which optional
# blocks (gallery/services) the registry can support — verified against
# every real composable structure, including the برایت‌بورد family whose
# real siblings (compare-cards) but no real photos (no gallery) is exactly
# the combination that breaks a naively-ordered sequence.
_DRAFT_ITEMS_PER_FEATURE_LIST = 4
_DRAFT_ITEMS_PER_CHECKLIST = 5
_DRAFT_TITLE_CHARS = 26
_DRAFT_BODY_CHARS = 220
_DRAFT_CHECKLIST_ITEM_CHARS = 90


def _draft_numbered_features(structure: StructureRecord) -> dict[str, Any]:
    items = [
        {
            "index": _persian_digits(i),
            "title": lorem_ipsum_of_length(_DRAFT_TITLE_CHARS),
            "body": lorem_ipsum_of_length(_DRAFT_BODY_CHARS),
            "icon": "icon-check",
            "placeholder": True,
        }
        for i in range(1, _DRAFT_ITEMS_PER_FEATURE_LIST + 1)
    ]
    return {
        "block": "numbered-features",
        "id": "why",
        "data": {
            "eyebrow": "چرا این سازه؟",
            "title": f"چرا {structure.name_fa}؟",
            "items": items,
        },
    }


def _draft_parts_zigzag(structure: StructureRecord) -> dict[str, Any]:
    sides = ("start", "end")
    items = [
        {
            "label": "تصویر نمونه",
            "alt": f"{structure.name_fa} — جزء سازه",
            "title": lorem_ipsum_of_length(_DRAFT_TITLE_CHARS),
            "body": lorem_ipsum_of_length(_DRAFT_BODY_CHARS),
            "side": sides[i % 2],
            "icon": "icon-structures",
            "placeholder": True,
        }
        for i in range(_DRAFT_ITEMS_PER_FEATURE_LIST)
    ]
    return {
        "block": "parts-zigzag",
        "id": "parts",
        "data": {
            "eyebrow": "اجزای سازه",
            "title": f"{structure.name_fa} از چه بخش‌هایی ساخته می‌شود؟",
            "items": items,
        },
    }


def _draft_checklist_section(structure: StructureRecord) -> dict[str, Any]:
    items = [
        {"value": lorem_ipsum_of_length(_DRAFT_CHECKLIST_ITEM_CHARS), "placeholder": True}
        for _ in range(_DRAFT_ITEMS_PER_CHECKLIST)
    ]
    return {
        "block": "checklist-section",
        "id": "fit",
        "data": {
            "eyebrow": "راهنمای انتخاب",
            "title": f"چه زمانی {structure.name_fa} انتخاب مناسبی است؟",
            "items": items,
        },
    }


def _draft_compare_cards(structure: StructureRecord, related: list[dict[str, str]]) -> dict[str, Any]:
    """Real sibling structures become real comparison cards (title/meta are
    already-verified registry facts, so they are not placeholder-tagged);
    padded with Lorem Ipsum cards only if fewer than 2 real siblings exist,
    so the block's own real-data path (§18) is reused rather than
    duplicated."""
    items = []
    for index, sibling in enumerate(related[:4], start=1):
        items.append({
            "title": sibling["title"],
            "body": sibling["meta"] or "مدل جایگزین همین خانواده سازه.",
            "index": _persian_digits(index),
            "icon": "icon-compare",
            "cta": {"label": "مشاهده سازه", "href": sibling["href"]},
        })
    while len(items) < 2:
        items.append({
            "title": lorem_ipsum_of_length(_DRAFT_TITLE_CHARS),
            "body": lorem_ipsum_of_length(_DRAFT_BODY_CHARS),
            "index": _persian_digits(len(items) + 1),
            "icon": "icon-compare",
            "placeholder": True,
        })
    return {
        "block": "compare-cards",
        "id": "compare",
        "data": {
            "eyebrow": "مقایسه و مدل‌های مرتبط",
            "title": f"{structure.name_fa} را با گزینه‌های دیگر مقایسه کنید",
            "items": items,
        },
    }


def build_complete_draft_spec(
    structure: StructureRecord,
    shell: Mapping[str, Any] | None = None,
    registry_root=None,
    media_root: Path | None = None,
) -> dict[str, Any]:
    """The always-complete draft: §18's honest spine plus every rich
    section, real where the registry/content pipeline has real data,
    Lorem-Ipsum-and-tagged everywhere it does not. Never committed to
    ``pages/blocks/`` without the owner's explicit approval — see design
    model §20."""
    base = build_product_page_spec(structure, shell, registry_root, media_root)

    by_block_id: dict[str, list[dict[str, Any]]] = {}
    for entry in base["blocks"]:
        by_block_id.setdefault(entry["block"], []).append(entry)

    hero = by_block_id["product-hero"][0]
    specs = by_block_id["structure-specs"][0]
    gallery = by_block_id.get("structure-gallery", [None])[0]
    services = by_block_id.get("structure-services", [None])[0]
    faq = by_block_id["faq-section-final"][0]
    lead_form = by_block_id["lead-form"][0]

    all_structures = load_structures(registry_root)
    buildable_ids = {other.id for other in all_structures if len(_specs(other)) >= 3}
    related = _related_structures(structure, all_structures, buildable_ids)

    blocks = [
        hero,
        specs,
        _draft_numbered_features(structure),
        _draft_parts_zigzag(structure),
        _draft_compare_cards(structure, related),
    ]
    if services:
        blocks.append(services)
    blocks.append(_draft_checklist_section(structure))
    if gallery:
        blocks.append(gallery)
    blocks.append(faq)
    blocks.append(lead_form)

    return {**base, "blocks": blocks}
