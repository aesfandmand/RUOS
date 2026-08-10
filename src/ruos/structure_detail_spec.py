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


def _real_shell() -> dict[str, Any]:
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
                {"label": "خانه", "href": "/"},
                {"label": "سازه‌ها و تابلوها", "href": _STRUCTURES_HUB_URL},
                {"label": "سرمایه‌گذاری", "href": "/investment/"},
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
                {"href": "/", "icon": "nav-home", "label": "خانه"},
                {"href": _STRUCTURES_HUB_URL, "icon": "nav-work", "label": "سازه‌ها"},
                {"href": "#review", "icon": "nav-services", "label": "استعلام"},
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
            "alt": f"نمونهٔ نصب واقعی {structure.name_fa}",
            "caption": "نمونه نصب واقعی — دیده‌شو",
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
        "shell": dict(shell) if shell else _real_shell(),
        "blocks": blocks,
    }
