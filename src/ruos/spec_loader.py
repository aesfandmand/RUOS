from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import PageSpec, SectionSpec


class SpecError(ValueError):
    pass


def _required(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if value in (None, "", []):
        raise SpecError(f"Missing required field: {key}")
    return value


def load_page_spec(path: Path) -> PageSpec:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SpecError(f"Page spec not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SpecError(f"Invalid JSON in {path}: {exc}") from exc

    section_rows = _required(raw, "sections")
    sections: list[SectionSpec] = []
    seen: set[str] = set()
    for row in section_rows:
        section_id = _required(row, "id")
        if section_id in seen:
            raise SpecError(f"Duplicate section id: {section_id}")
        seen.add(section_id)
        sections.append(
            SectionSpec(
                id=section_id,
                kind=_required(row, "kind"),
                title=_required(row, "title"),
                body=row.get("body", ""),
                eyebrow=row.get("eyebrow", ""),
                cta_label=row.get("cta_label", ""),
                cta_href=row.get("cta_href", ""),
                items=tuple(row.get("items", [])),
            )
        )

    return PageSpec(
        slug=_required(raw, "slug"),
        lang=raw.get("lang", "fa"),
        direction=raw.get("direction", "rtl"),
        title=_required(raw, "title"),
        description=_required(raw, "description"),
        brand=_required(raw, "brand"),
        visual_profile=_required(raw, "visual_profile"),
        sections=tuple(sections),
        metadata=dict(raw.get("metadata", {})),
    )
