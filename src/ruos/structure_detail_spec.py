"""Build a real Structure Detail page spec from registry data.

Every field here traces to either the structure registry (dimensions,
orientation, context...) or the persona journey matrix (hero message,
conversion intent) — nothing is invented marketing copy. A structure
whose registry record does not yet carry enough attributes to fill
``structure-specs``' minimum of three rows is rejected rather than
padded with fabricated specs; see ``StructureDetailSpecError``.

Manufacturing-process and FAQ content are deliberately left out of the
composed sequence: no verified copy for either exists yet. Adding
either block back in is a content-authoring task, not a design one —
see design_approach.py's note on this archetype.
"""
from __future__ import annotations

from typing import Any, Mapping

from .architecture_registry import StructureRecord
from .persona_registry import journey_rows_for_entry_page

_DEFAULT_CTA_LABEL = "درخواست استعلام فنی"

_ORIENTATION_FA = {"vertical": "عمودی", "horizontal": "افقی"}
_CONTEXT_FA = {
    "outdoor": "محیط شهری (بیرون)",
    "outdoor_organizational": "محیط سازمانی (بیرون)",
    "indoor": "داخل ساختمان",
}
_FACE_COUNT_FA = {"one_or_two": "یک یا دو رو، بسته به موقعیت"}
_MOUNTING_FA = {"wall": "نصب دیواری", "standing": "استند ایستاده"}


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


def _diagram(raw: str | None) -> dict[str, Any] | None:
    parsed = _parse_dimensions(raw) if raw else None
    if not parsed:
        return None
    width, height, unit = parsed
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


def build_structure_detail_spec(
    structure: StructureRecord,
    shell: Mapping[str, Any],
    registry_root=None,
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

    blocks = [
        {
            "block": "structure-hero",
            "id": "top",
            "data": {
                "eyebrow": structure.family,
                "title": structure.name_fa,
                "lead": journey["hero_message"] if journey else "",
                "dimension_label": _dimension_label(structure.dimensions),
                "diagram": _diagram(structure.dimensions),
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
        {
            "block": "review-gate",
            "id": "review",
            "data": {
                "eyebrow": "قدم بعدی",
                "title": "برای این سازه استعلام فنی و قیمت بگیرید.",
                "body": "ابعاد، محل نصب و شرایط پروژه را بگویید تا بررسی فنی و برآورد اجرا برایتان آماده شود.",
                "primary": {"label": journey["conversion"] if journey else _DEFAULT_CTA_LABEL},
                "secondary": {"label": "دیدن دوبارهٔ مشخصات ↑", "href": "#top"},
            },
        },
    ]

    return {
        "slug": slug,
        "lang": "fa",
        "direction": "rtl",
        "title": f"{structure.name_fa} | مشخصات فنی و اجرا | چتر قرمز",
        "description": f"{structure.name_fa}: مشخصات فنی، ابعاد و مسیر اجرای پروژه از چتر قرمز.",
        "canonical": f"https://chatreghermez.ir{structure.url}",
        "shell": dict(shell),
        "blocks": blocks,
    }
