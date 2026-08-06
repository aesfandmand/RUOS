from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .models import PageSpec
from .voice_studio import select_voice


class ContentCompositionError(ValueError):
    """Raised when page copy cannot form a production semantic content plan."""


@dataclass(frozen=True)
class ContentBlock:
    section_id: str
    role: str
    heading_level: int
    intent: str
    title: str
    body: str
    cta_label: str
    cta_href: str
    entities: tuple[str, ...]
    attributes: Mapping[str, str]

    def fingerprint_payload(self) -> tuple[tuple[str, str], ...]:
        base = (
            ("section_id", self.section_id),
            ("role", self.role),
            ("heading_level", str(self.heading_level)),
            ("intent", self.intent),
            ("title", self.title),
            ("body", self.body),
            ("cta_label", self.cta_label),
            ("cta_href", self.cta_href),
            ("entities", ",".join(self.entities)),
        )
        return base + tuple(sorted(self.attributes.items()))


@dataclass(frozen=True)
class ContentPlan:
    page_slug: str
    language: str
    direction: str
    primary_intent: str
    blocks: tuple[ContentBlock, ...]

    def fingerprint_payload(self) -> tuple[tuple[str, object], ...]:
        return (
            ("page_slug", self.page_slug),
            ("language", self.language),
            ("direction", self.direction),
            ("primary_intent", self.primary_intent),
            ("blocks", tuple((block.section_id, block.fingerprint_payload()) for block in self.blocks)),
        )


def _freeze(values: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(dict(values))


def _intent(kind: str) -> tuple[str, str]:
    table = {
        "hero": ("orientation", "promise"),
        "story": ("understanding", "narrative"),
        "knowledge": ("comparison", "knowledge"),
        "interaction": ("decision", "tool"),
        "conversion": ("action", "conversion"),
    }
    try:
        return table[kind]
    except KeyError as exc:
        raise ContentCompositionError(f"Unsupported content kind '{kind}'") from exc


def compose_content(page: PageSpec) -> ContentPlan:
    if not page.title.strip() or not page.description.strip():
        raise ContentCompositionError("Page title and description are required")

    voice = select_voice(page)
    approved_voice = voice.approved
    blocks: list[ContentBlock] = []
    for section in page.sections:
        if not section.title.strip():
            raise ContentCompositionError(f"Section '{section.id}' requires a title")
        intent, role = _intent(section.kind)
        if section.kind not in {"interaction", "conversion"} and len(section.body.strip()) < 40:
            raise ContentCompositionError(f"Section '{section.id}' body is too thin for production content")
        if bool(section.cta_label) != bool(section.cta_href):
            raise ContentCompositionError(f"Section '{section.id}' CTA label and href must be paired")
        entities = tuple(
            sorted(
                {
                    str(item.get("title", "")).strip()
                    for item in section.items
                    if str(item.get("title", "")).strip()
                }
            )
        )
        blocks.append(
            ContentBlock(
                section_id=section.id,
                role=role,
                heading_level=1 if section.kind == "hero" else 2,
                intent=intent,
                title=section.title.strip(),
                body=section.body.strip(),
                cta_label=section.cta_label.strip(),
                cta_href=section.cta_href.strip(),
                entities=entities,
                attributes=_freeze(
                    {
                        "eyebrow": section.eyebrow.strip(),
                        "item_count": str(len(section.items)),
                        "has_cta": str(bool(section.cta_href)).lower(),
                        "voice_id": approved_voice.id,
                        "voice_label": approved_voice.label,
                        "voice_approval_sha256": voice.sha256,
                    }
                ),
            )
        )

    if not blocks or blocks[0].heading_level != 1:
        raise ContentCompositionError("Content plan requires exactly one primary opening heading")
    if sum(block.heading_level == 1 for block in blocks) != 1:
        raise ContentCompositionError("Content plan must contain exactly one H1 block")
    if blocks[-1].role != "conversion":
        raise ContentCompositionError("Content plan must end with a conversion block")

    return ContentPlan(
        page_slug=page.slug,
        language=page.lang,
        direction=page.direction,
        primary_intent=str(page.metadata.get("primary_conversion", "qualified-action")),
        blocks=tuple(blocks),
    )
