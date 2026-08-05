from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .component_resolver import ComponentPlan
from .models import PageSpec


class PatternResolutionError(ValueError):
    """Raised when component composition cannot form a coherent page pattern."""


@dataclass(frozen=True)
class SectionPattern:
    section_id: str
    chapter: int
    entrance: str
    transition: str
    alignment: str
    pacing: str
    motif: str
    attributes: Mapping[str, str]

    def fingerprint_payload(self) -> tuple[tuple[str, str], ...]:
        base = (
            ("section_id", self.section_id),
            ("chapter", str(self.chapter)),
            ("entrance", self.entrance),
            ("transition", self.transition),
            ("alignment", self.alignment),
            ("pacing", self.pacing),
            ("motif", self.motif),
        )
        return base + tuple(sorted(self.attributes.items()))


@dataclass(frozen=True)
class PatternPlan:
    page_slug: str
    narrative_arc: str
    global_motif: str
    scroll_model: str
    sections: tuple[SectionPattern, ...]

    def for_section(self, section_id: str) -> SectionPattern:
        for pattern in self.sections:
            if pattern.section_id == section_id:
                return pattern
        raise PatternResolutionError(f"No pattern resolved for section '{section_id}'")

    def fingerprint_payload(self) -> tuple[tuple[str, object], ...]:
        return (
            ("page_slug", self.page_slug),
            ("narrative_arc", self.narrative_arc),
            ("global_motif", self.global_motif),
            ("scroll_model", self.scroll_model),
            (
                "sections",
                tuple((pattern.section_id, pattern.fingerprint_payload()) for pattern in self.sections),
            ),
        )


def _freeze(values: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(dict(values))


def _section_pattern(kind: str, chapter: int, total: int) -> tuple[str, str, str, str, str, dict[str, str]]:
    if kind == "hero":
        return (
            "reveal-rise",
            "open-field",
            "split",
            "immersive",
            "orbit",
            {"depth": "3", "sticky": "false", "contrast": "maximum"},
        )
    if kind == "story":
        return (
            "editorial-drift",
            "soft-cut",
            "offset",
            "reflective",
            "line",
            {"depth": "1", "sticky": "false", "contrast": "calm"},
        )
    if kind == "knowledge":
        return (
            "stagger-grid",
            "chapter-lock",
            "grid",
            "comparative",
            "index",
            {"depth": "2", "sticky": "false", "contrast": "layered"},
        )
    if kind == "interaction":
        return (
            "focus-console",
            "dark-pivot",
            "center",
            "deliberate",
            "signal",
            {"depth": "2", "sticky": "true", "contrast": "high"},
        )
    if kind == "conversion":
        return (
            "closing-expand",
            "terminal-stage",
            "center",
            "decisive",
            "umbrella",
            {"depth": "3", "sticky": "false", "contrast": "maximum"},
        )
    raise PatternResolutionError(f"Unsupported section kind '{kind}' at chapter {chapter}/{total}")


def resolve_patterns(page: PageSpec, components: ComponentPlan) -> PatternPlan:
    if len(page.sections) != len(components.components):
        raise PatternResolutionError("Pattern resolution requires one component per section")

    patterns: list[SectionPattern] = []
    total = len(page.sections)
    previous_transition = ""

    for chapter, section in enumerate(page.sections, start=1):
        component = components.for_section(section.id)
        entrance, transition, alignment, pacing, motif, attributes = _section_pattern(
            section.kind, chapter, total
        )
        if component.section_id != section.id:
            raise PatternResolutionError(
                f"Component '{component.id}' is not aligned with section '{section.id}'"
            )
        if previous_transition == "terminal-stage":
            raise PatternResolutionError("No section may follow a terminal conversion pattern")
        patterns.append(
            SectionPattern(
                section_id=section.id,
                chapter=chapter,
                entrance=entrance,
                transition=transition,
                alignment=alignment,
                pacing=pacing,
                motif=motif,
                attributes=_freeze(
                    {
                        **attributes,
                        "component_variant": component.variant,
                        "chapter_label": f"{chapter:02d}/{total:02d}",
                    }
                ),
            )
        )
        previous_transition = transition

    if not patterns or patterns[0].motif != "orbit":
        raise PatternResolutionError("The page pattern must open with the orbit motif")
    if patterns[-1].transition != "terminal-stage":
        raise PatternResolutionError("The page pattern must close with a terminal conversion stage")

    return PatternPlan(
        page_slug=page.slug,
        narrative_arc="discover-understand-decide-act",
        global_motif="red-umbrella-orbit",
        scroll_model="chaptered-progressive",
        sections=tuple(patterns),
    )
