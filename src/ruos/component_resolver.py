from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .models import PageSpec, SectionSpec


class ComponentResolutionError(ValueError):
    """Raised when a page cannot be mapped to the production component system."""


@dataclass(frozen=True)
class ComponentSpec:
    id: str
    section_id: str
    family: str
    variant: str
    density: str
    emphasis: str
    capabilities: tuple[str, ...]
    attributes: Mapping[str, str]

    def fingerprint_payload(self) -> tuple[tuple[str, str], ...]:
        base = (
            ("id", self.id),
            ("section_id", self.section_id),
            ("family", self.family),
            ("variant", self.variant),
            ("density", self.density),
            ("emphasis", self.emphasis),
            ("capabilities", ",".join(self.capabilities)),
        )
        return base + tuple(sorted(self.attributes.items()))


@dataclass(frozen=True)
class ComponentPlan:
    page_slug: str
    components: tuple[ComponentSpec, ...]

    def for_section(self, section_id: str) -> ComponentSpec:
        for component in self.components:
            if component.section_id == section_id:
                return component
        raise ComponentResolutionError(f"No component resolved for section '{section_id}'")

    def fingerprint_payload(self) -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
        return tuple((component.id, component.fingerprint_payload()) for component in self.components)


_ALLOWED_KINDS = {"hero", "story", "knowledge", "interaction", "conversion"}


def _freeze(values: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(dict(values))


def _resolve_variant(section: SectionSpec) -> tuple[str, str, str, tuple[str, ...], dict[str, str]]:
    item_count = len(section.items)
    has_cta = bool(section.cta_label and section.cta_href)

    if section.kind == "hero":
        return (
            "hero",
            "cinematic-orbit",
            "spacious",
            ("primary-heading", "ambient-art", "scroll-cue", "primary-cta"),
            {"heading_scale": "display", "surface": "dark", "layout": "split"},
        )
    if section.kind == "story":
        return (
            "narrative",
            "editorial-statement",
            "spacious",
            ("chapter-marker", "longform-copy", "visual-pause"),
            {"heading_scale": "feature", "surface": "light", "layout": "offset"},
        )
    if section.kind == "knowledge":
        if item_count < 2:
            raise ComponentResolutionError(
                f"Knowledge section '{section.id}' requires at least two items for comparison"
            )
        variant = "knowledge-triptych" if item_count == 3 else "knowledge-grid"
        return (
            "collection",
            variant,
            "balanced",
            ("indexed-cards", "semantic-list", "responsive-grid"),
            {
                "heading_scale": "feature",
                "surface": "layered",
                "layout": "grid",
                "columns": str(min(item_count, 3)),
            },
        )
    if section.kind == "interaction":
        return (
            "interactive",
            "decision-console",
            "focused",
            ("progressive-disclosure", "keyboard-ready", "state-feedback"),
            {"heading_scale": "feature", "surface": "dark", "layout": "console"},
        )
    if section.kind == "conversion":
        if not has_cta:
            raise ComponentResolutionError(
                f"Conversion section '{section.id}' requires both cta_label and cta_href"
            )
        return (
            "conversion",
            "closing-stage",
            "focused",
            ("primary-cta", "outcome-copy", "high-contrast"),
            {"heading_scale": "feature", "surface": "accent", "layout": "stage"},
        )
    raise ComponentResolutionError(f"Unsupported section kind '{section.kind}'")


def resolve_components(page: PageSpec) -> ComponentPlan:
    if not page.sections:
        raise ComponentResolutionError("A page requires at least one section")

    components: list[ComponentSpec] = []
    seen_ids: set[str] = set()
    seen_kinds: set[str] = set()

    for index, section in enumerate(page.sections, start=1):
        if section.id in seen_ids:
            raise ComponentResolutionError(f"Duplicate section id '{section.id}'")
        seen_ids.add(section.id)
        if section.kind not in _ALLOWED_KINDS:
            raise ComponentResolutionError(
                f"Section '{section.id}' uses unsupported kind '{section.kind}'"
            )
        family, variant, density, capabilities, attributes = _resolve_variant(section)
        emphasis = "primary" if section.kind in {"hero", "conversion"} else "supporting"
        components.append(
            ComponentSpec(
                id=f"cmp-{index:02d}-{section.id}",
                section_id=section.id,
                family=family,
                variant=variant,
                density=density,
                emphasis=emphasis,
                capabilities=capabilities,
                attributes=_freeze(attributes),
            )
        )
        seen_kinds.add(section.kind)

    required = {"hero", "conversion"}
    missing = sorted(required - seen_kinds)
    if missing:
        raise ComponentResolutionError(
            f"Page '{page.slug}' is missing required component families: {', '.join(missing)}"
        )
    if page.sections[0].kind != "hero":
        raise ComponentResolutionError("The first resolved component must be the hero")
    if page.sections[-1].kind != "conversion":
        raise ComponentResolutionError("The final resolved component must be conversion")

    return ComponentPlan(page_slug=page.slug, components=tuple(components))
