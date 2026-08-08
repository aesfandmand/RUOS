from __future__ import annotations

from typing import Any, Mapping

from .models import PageSpec


def _scene_template(pattern: str) -> list[dict[str, Any]]:
    if pattern == "cinematic-scroll-stage":
        return [
            {"id": "establish", "range": [0.0, 0.25], "state": "context", "actions": ["reveal-heading", "hold-primary-context"]},
            {"id": "depth", "range": [0.25, 0.5], "state": "depth", "actions": ["parallax-depth-layer", "advance-progress"]},
            {"id": "focus", "range": [0.5, 0.75], "state": "focus", "actions": ["focus-evidence", "reduce-background-noise"]},
            {"id": "handoff", "range": [0.75, 1.0], "state": "handoff", "actions": ["reveal-cta", "prepare-next-section"]},
        ]
    if pattern == "structure-anatomy-explorer":
        return [
            {"id": "overview", "range": [0.0, 0.25], "state": "overview", "actions": ["show-complete-structure"]},
            {"id": "structure", "range": [0.25, 0.5], "state": "structure", "actions": ["activate-structure-layer", "announce-layer"]},
            {"id": "foundation", "range": [0.5, 0.75], "state": "foundation", "actions": ["activate-foundation-layer", "announce-layer"]},
            {"id": "context", "range": [0.75, 1.0], "state": "placement", "actions": ["activate-placement-layer", "reveal-decision-criteria"]},
        ]
    if pattern == "hotspot-decision-explorer":
        return [
            {"id": "prompt", "range": [0.0, 0.33], "state": "prompt", "actions": ["show-choice-surface"]},
            {"id": "compare", "range": [0.33, 0.66], "state": "compare", "actions": ["keep-selected-choice", "update-live-result"]},
            {"id": "resolve", "range": [0.66, 1.0], "state": "resolve", "actions": ["show-recommendation", "reveal-cta"]},
        ]
    if pattern == "horizontal-journey":
        return [
            {"id": "start", "range": [0.0, 0.34], "state": "start", "actions": ["activate-first-step", "show-progress"]},
            {"id": "progress", "range": [0.34, 0.67], "state": "progress", "actions": ["advance-active-step", "preserve-context"]},
            {"id": "complete", "range": [0.67, 1.0], "state": "complete", "actions": ["activate-final-step", "reveal-next-action"]},
        ]
    if pattern == "pinned-storytelling":
        return [
            {"id": "setup", "range": [0.0, 0.34], "state": "setup", "actions": ["pin-context", "reveal-first-state"]},
            {"id": "develop", "range": [0.34, 0.67], "state": "develop", "actions": ["advance-story-state", "retain-visual-anchor"]},
            {"id": "payoff", "range": [0.67, 1.0], "state": "payoff", "actions": ["resolve-story", "release-pin"]},
        ]
    if pattern == "cinematic-transition":
        return [
            {"id": "enter", "range": [0.0, 0.5], "state": "enter", "actions": ["reduce-density", "focus-message"]},
            {"id": "exit", "range": [0.5, 1.0], "state": "exit", "actions": ["reveal-next-action", "handoff"]},
        ]
    return [
        {"id": "reveal", "range": [0.0, 0.5], "state": "reveal", "actions": ["reveal-content"]},
        {"id": "settle", "range": [0.5, 1.0], "state": "settle", "actions": ["settle-layout", "preserve-readability"]},
    ]


def build_scene_orchestration_plan(page: PageSpec, experience_patterns: Mapping[str, Any]) -> dict[str, Any]:
    raw = experience_patterns.get("sections", []) if isinstance(experience_patterns, Mapping) else []
    if experience_patterns.get("status") != "ready" or not isinstance(raw, list):
        return {"version": "1.0", "status": "blocked", "page_id": page.slug, "sections": [], "blockers": ["experience pattern plan is not ready"]}
    sections: list[dict[str, Any]] = []
    blockers: list[str] = []
    for item in raw:
        if not isinstance(item, Mapping):
            blockers.append("scene orchestration requires object pattern entries"); continue
        section_id = str(item.get("section_id", "")).strip(); pattern = str(item.get("pattern", "")).strip()
        if not section_id or not pattern:
            blockers.append("scene orchestration requires section_id and pattern"); continue
        scenes = _scene_template(pattern)
        sections.append({
            "section_id": section_id,
            "pattern": pattern,
            "driver": "scroll-progress" if pattern not in {"hotspot-decision-explorer"} else "interaction-and-scroll",
            "scenes": scenes,
            "initial_state": scenes[0]["state"],
            "final_state": scenes[-1]["state"],
            "mobile_policy": "preserve state order without mandatory pinning",
            "reduced_motion_policy": "apply state changes without continuous transform animation",
            "semantic_parity_required": True,
        })
    if len(sections) != len(page.sections): blockers.append("scene orchestration requires exactly one scene plan per page section")
    return {"version": "1.0", "status": "ready" if sections and not blockers else "blocked", "page_id": page.slug, "sections": sections, "blockers": blockers}
