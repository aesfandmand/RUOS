from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .component_resolver import ComponentPlan
from .pattern_resolver import PatternPlan


class MotionCompositionError(ValueError):
    """Raised when a motion plan cannot be composed safely."""


@dataclass(frozen=True)
class MotionCue:
    section_id: str
    order: int
    trigger: str
    target: str
    effect: str
    duration_ms: int
    delay_ms: int
    easing: str
    once: bool
    reduced_effect: str
    attributes: Mapping[str, str]

    def fingerprint_payload(self) -> tuple[tuple[str, str], ...]:
        base = (
            ("section_id", self.section_id),
            ("order", str(self.order)),
            ("trigger", self.trigger),
            ("target", self.target),
            ("effect", self.effect),
            ("duration_ms", str(self.duration_ms)),
            ("delay_ms", str(self.delay_ms)),
            ("easing", self.easing),
            ("once", str(self.once).lower()),
            ("reduced_effect", self.reduced_effect),
        )
        return base + tuple(sorted(self.attributes.items()))


@dataclass(frozen=True)
class MotionPlan:
    page_slug: str
    strategy: str
    reduced_motion_policy: str
    cues: tuple[MotionCue, ...]

    def fingerprint_payload(self) -> tuple[tuple[str, object], ...]:
        return (
            ("page_slug", self.page_slug),
            ("strategy", self.strategy),
            ("reduced_motion_policy", self.reduced_motion_policy),
            ("cues", tuple((cue.section_id, cue.fingerprint_payload()) for cue in self.cues)),
        )


def _freeze(values: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(dict(values))


def _motion_for(entrance: str, order: int) -> tuple[str, int, int, str, str, dict[str, str]]:
    table = {
        "reveal-rise": ("rise-fade", 900, 0, "cubic-bezier(.22,1,.36,1)", "reveal", {"distance": "32px", "stagger": "80"}),
        "editorial-drift": ("drift-fade", 760, 40, "cubic-bezier(.16,1,.3,1)", "reveal", {"distance": "24px", "axis": "inline"}),
        "stagger-grid": ("stagger-cards", 680, 80, "cubic-bezier(.22,1,.36,1)", "reveal", {"stagger": "110", "distance": "22px"}),
        "focus-console": ("focus-expand", 720, 60, "cubic-bezier(.22,1,.36,1)", "reveal", {"scale_from": ".975", "glow": "true"}),
        "closing-expand": ("expand-fade", 820, 20, "cubic-bezier(.16,1,.3,1)", "reveal", {"scale_from": ".96", "distance": "18px"}),
    }
    try:
        effect, duration, delay, easing, reduced, attrs = table[entrance]
    except KeyError as exc:
        raise MotionCompositionError(f"Unsupported pattern entrance '{entrance}'") from exc
    return effect, duration, delay + (order - 1) * 15, easing, reduced, attrs


def compose_motion(patterns: PatternPlan, components: ComponentPlan) -> MotionPlan:
    if len(patterns.sections) != len(components.components):
        raise MotionCompositionError("Motion composition requires aligned pattern and component plans")

    cues: list[MotionCue] = []
    for order, pattern in enumerate(patterns.sections, start=1):
        component = components.for_section(pattern.section_id)
        effect, duration, delay, easing, reduced, attrs = _motion_for(pattern.entrance, order)
        target = ".ruos-items > *" if effect == "stagger-cards" else ".ruos-section__content"
        cues.append(
            MotionCue(
                section_id=pattern.section_id,
                order=order,
                trigger="intersection",
                target=target,
                effect=effect,
                duration_ms=duration,
                delay_ms=delay,
                easing=easing,
                once=True,
                reduced_effect=reduced,
                attributes=_freeze({**attrs, "component_variant": component.variant}),
            )
        )

    if not cues or cues[0].section_id != patterns.sections[0].section_id:
        raise MotionCompositionError("Motion timeline must begin with the first page section")
    if tuple(cue.order for cue in cues) != tuple(range(1, len(cues) + 1)):
        raise MotionCompositionError("Motion cue ordering is not contiguous")

    return MotionPlan(
        page_slug=patterns.page_slug,
        strategy="chapter-aware-progressive-motion",
        reduced_motion_policy="replace-transform-with-instant-reveal",
        cues=tuple(cues),
    )
