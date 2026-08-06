from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .creative_selection import CreativeSelectionPlan
from .inspiration_intelligence import InspirationIntelligence
from .models import PageSpec
from .pattern_resolver import PatternPlan
from .visual_dna import VisualDNA


class ArtDirectorError(ValueError):
    """Raised when a production art direction cannot be resolved."""


@dataclass(frozen=True)
class ArtDirectionDecision:
    page_slug: str
    concept: str
    composition: str
    hierarchy: tuple[str, ...]
    grid_system: str
    whitespace_rhythm: str
    typography_scale: tuple[str, ...]
    color_logic: tuple[str, ...]
    image_direction: tuple[str, ...]
    scroll_composition: tuple[str, ...]
    responsive_translation: tuple[str, ...]
    constraints: tuple[str, ...]
    inspiration_sha256: str
    selection_sha256: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "concept": self.concept,
            "composition": self.composition,
            "hierarchy": list(self.hierarchy),
            "grid_system": self.grid_system,
            "whitespace_rhythm": self.whitespace_rhythm,
            "typography_scale": list(self.typography_scale),
            "color_logic": list(self.color_logic),
            "image_direction": list(self.image_direction),
            "scroll_composition": list(self.scroll_composition),
            "responsive_translation": list(self.responsive_translation),
            "constraints": list(self.constraints),
            "inspiration_sha256": self.inspiration_sha256,
            "selection_sha256": self.selection_sha256,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def direct_art(
    page: PageSpec,
    dna: VisualDNA,
    patterns: PatternPlan,
    selection: CreativeSelectionPlan,
    inspiration: InspirationIntelligence,
) -> ArtDirectionDecision:
    if len({page.slug, patterns.page_slug, selection.page_slug, inspiration.page_slug}) != 1:
        raise ArtDirectorError("Art direction inputs do not belong to the same page")
    if inspiration.evidence_status != "ready":
        raise ArtDirectorError("Art Director requires approved inspiration evidence")
    selected = {decision.category: decision.candidate_id for decision in selection.decisions}
    required = {"hero", "layout", "typography", "motion", "interaction", "story"}
    missing = sorted(required - set(selected))
    if missing:
        raise ArtDirectorError("Art direction is missing creative selections: " + ", ".join(missing))
    return ArtDirectionDecision(
        page_slug=page.slug,
        concept="Infrastructure becomes a navigable visual system: scale first, understanding second, decision last.",
        composition="chaptered-industrial-canvas with alternating monumental, editorial and interactive spatial states",
        hierarchy=(
            "monumental proposition and structural silhouette",
            "single narrative bridge explaining why structure choice matters",
            "spatial catalogue with progressive technical reveal",
            "guided commercial decision console",
            "high-contrast closing stage",
        ),
        grid_system="12-column fluid desktop grid; asymmetric 7/5 and 8/4 compositions; single-axis snap narrative on mobile",
        whitespace_rhythm="large cinematic pauses around claims; compressed evidence bands; expanded decision moments",
        typography_scale=(
            "display: clamp(3.5rem, 9vw, 9rem)",
            "feature: clamp(2.25rem, 5vw, 5rem)",
            "section: clamp(1.75rem, 3vw, 3rem)",
            "body: clamp(1rem, 1.3vw, 1.25rem) with Persian reading measure",
            "data: tabular numerals with strong contrast",
        ),
        color_logic=(
            f"use Visual DNA profile {dna.id} as the only brand palette authority",
            "reserve accent for navigation state, structural focus and conversion",
            "use dark fields for scale and light fields for explanation",
            "avoid decorative gradients that do not communicate depth or state",
        ),
        image_direction=(
            "low-angle structural photography or renders showing scale",
            "exploded technical views for foundation, lighting and faces",
            "context frames showing location, traffic and sightline",
            "no generic stock-office imagery",
        ),
        scroll_composition=(
            "hero establishes scale through depth rather than a static banner",
            "sticky narrative bridge creates a deliberate reading pause",
            "catalogue reveals structure attributes progressively",
            "horizontal or pinned comparison is used only where it improves choice",
            "conversion follows proof and never interrupts the opening story",
        ),
        responsive_translation=(
            "preserve the hero as the first visual state on mobile",
            "translate asymmetric compositions into ordered full-width chapters",
            "use scroll-snap for comparisons without hiding content",
            "preserve bottom navigation and touch targets",
            "replace depth motion with opacity and position changes under reduced motion",
        ),
        constraints=(
            "no repetitive generic card wall",
            "no copied composition from approved references",
            "no motion without narrative or state purpose",
            "no typography that sacrifices Persian readability",
            "no desktop-only creative device without a mobile equivalent",
            f"selected-hero:{selected['hero']}",
            f"selected-layout:{selected['layout']}",
            f"selected-type:{selected['typography']}",
        ),
        inspiration_sha256=inspiration.sha256,
        selection_sha256=selection.sha256,
    )
