from pathlib import Path

import pytest

from ruos.component_resolver import resolve_components
from ruos.motion_composer import MotionCompositionError, compose_motion
from ruos.pattern_resolver import PatternPlan, SectionPattern, resolve_patterns
from ruos.spec_loader import load_page_spec


def _plans():
    page = load_page_spec(Path("pages/structures.json"))
    components = resolve_components(page)
    patterns = resolve_patterns(page, components)
    return components, patterns


def test_motion_plan_is_deterministic_and_contiguous() -> None:
    components, patterns = _plans()
    first = compose_motion(patterns, components)
    second = compose_motion(patterns, components)

    assert first.fingerprint_payload() == second.fingerprint_payload()
    assert [cue.order for cue in first.cues] == [1, 2, 3, 4, 5]
    assert [cue.section_id for cue in first.cues] == [pattern.section_id for pattern in patterns.sections]
    assert all(cue.duration_ms > 0 for cue in first.cues)
    assert all(cue.reduced_effect == "reveal" for cue in first.cues)
    assert all(cue.once for cue in first.cues)


def test_motion_plan_maps_semantic_effects() -> None:
    components, patterns = _plans()
    plan = compose_motion(patterns, components)

    effects = {cue.section_id: cue.effect for cue in plan.cues}
    assert effects == {
        "hero": "rise-fade",
        "story": "drift-fade",
        "knowledge": "stagger-cards",
        "interaction": "focus-expand",
        "conversion": "expand-fade",
    }
    assert plan.cues[2].target == ".ruos-items > *"
    assert plan.reduced_motion_policy == "replace-transform-with-instant-reveal"


def test_unknown_entrance_is_rejected() -> None:
    components, patterns = _plans()
    broken = SectionPattern(
        section_id=patterns.sections[0].section_id,
        chapter=1,
        entrance="unknown-motion",
        transition=patterns.sections[0].transition,
        alignment=patterns.sections[0].alignment,
        pacing=patterns.sections[0].pacing,
        motif=patterns.sections[0].motif,
        attributes=patterns.sections[0].attributes,
    )
    invalid = PatternPlan(
        page_slug=patterns.page_slug,
        narrative_arc=patterns.narrative_arc,
        global_motif=patterns.global_motif,
        scroll_model=patterns.scroll_model,
        sections=(broken,) + patterns.sections[1:],
    )

    with pytest.raises(MotionCompositionError, match="Unsupported pattern entrance"):
        compose_motion(invalid, components)
