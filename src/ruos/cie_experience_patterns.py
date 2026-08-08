from __future__ import annotations

from typing import Any, Mapping

from .models import PageSpec


PATTERNS: dict[str, dict[str, Any]] = {
    "cinematic-scroll-stage": {"purpose": "establish narrative context with scroll-linked depth and staged reveal", "desktop": "sticky or pinned visual stage with progressive content reveal", "mobile": "vertical cinematic sequence with no required pinning", "enhancement": "webgl-or-layered-transform", "fallback": "static responsive hero with ordered semantic content"},
    "pinned-storytelling": {"purpose": "hold visual context while explanatory steps advance", "desktop": "sticky visual anchor with sequential text states", "mobile": "stacked story states with persistent progress indicator", "enhancement": "intersection-observer-state-machine", "fallback": "linear semantic section sequence"},
    "structure-anatomy-explorer": {"purpose": "explain physical structure, foundation, lighting and placement as inspectable layers", "desktop": "anatomy stage with hotspots and layer state", "mobile": "touch-first accordion/hotspot hybrid with same evidence", "enhancement": "svg-canvas-or-webgl-anatomy", "fallback": "semantic diagram plus labeled detail list"},
    "hotspot-decision-explorer": {"purpose": "let users inspect options and expose decision criteria without losing context", "desktop": "interactive hotspot/choice surface with live detail panel", "mobile": "large touch controls with linear result panel", "enhancement": "stateful-progressive-enhancement", "fallback": "radio-like semantic controls and visible result text"},
    "horizontal-journey": {"purpose": "express a finite ordered sequence while preserving chapter continuity", "desktop": "scroll-linked horizontal stage with explicit progress", "mobile": "vertical sequence or controlled horizontal snap cards", "enhancement": "scroll-progress-transform", "fallback": "ordered vertical list"},
    "cinematic-transition": {"purpose": "create a deliberate visual pause before a new decision or conversion state", "desktop": "full-bleed transition stage with restrained depth/motion", "mobile": "short visual pause with content-first transition", "enhancement": "layered-transform-or-video", "fallback": "static editorial transition"},
    "editorial-reveal": {"purpose": "present content with strong hierarchy and progressive reveal", "desktop": "editorial composition with measured reveal", "mobile": "single-column reading flow", "enhancement": "intersection-observer-reveal", "fallback": "static semantic layout"},
}


def _select_pattern(page: PageSpec, section_id: str, section_kind: str, component: Mapping[str, Any], evidence: set[str]) -> str:
    family = str(component.get("family", "")); variant = str(component.get("variant", "")); slug = page.slug.lower()
    if section_id == "hero" or family == "hero": return "cinematic-scroll-stage"
    if section_kind == "interaction" or family == "interactive" or "decision" in variant: return "hotspot-decision-explorer"
    if slug in {"structures", "structure", "catalog"} and (section_kind == "knowledge" or "industrial-product-provider-required" in evidence): return "structure-anatomy-explorer"
    if section_kind in {"process", "journey", "sequence", "timeline"}: return "horizontal-journey"
    if section_kind in {"proof", "story", "case-study"}: return "pinned-storytelling"
    if section_kind in {"transition", "conversion", "closing"}: return "cinematic-transition"
    return "editorial-reveal"


def build_experience_pattern_plan(page: PageSpec, creative_director: Mapping[str, Any]) -> dict[str, Any]:
    decisions = creative_director.get("sections", [])
    if creative_director.get("status") != "ready" or not isinstance(decisions, list): return {"version": "1.0", "status": "blocked", "page_id": page.slug, "sections": [], "blockers": ["creative director plan is not ready"]}
    sections: list[dict[str, Any]] = []; blockers: list[str] = []; seen: set[str] = set()
    for decision in decisions:
        if not isinstance(decision, Mapping): blockers.append("experience decisions must be objects"); continue
        section_id = str(decision.get("section_id", "")).strip()
        if not section_id or section_id in seen: blockers.append("experience decisions require unique section ids"); continue
        seen.add(section_id); component = decision.get("component", {}) if isinstance(decision.get("component"), Mapping) else {}; evidence = {str(item) for item in decision.get("evidence", [])}; section = next((item for item in page.sections if item.id == section_id), None)
        if section is None: blockers.append(f"unknown page section: {section_id}"); continue
        pattern_id = _select_pattern(page, section_id, section.kind, component, evidence); pattern = PATTERNS[pattern_id]
        sections.append({"section_id": section_id, "pattern": pattern_id, "purpose": pattern["purpose"], "desktop_behavior": pattern["desktop"], "mobile_behavior": pattern["mobile"], "enhancement": pattern["enhancement"], "fallback": pattern["fallback"], "semantic_parity_required": True, "reduced_motion_required": True, "anti_copy_required": True})
    if len(sections) != len(page.sections): blockers.append("experience pattern plan requires exactly one pattern per page section")
    return {"version": "1.0", "status": "ready" if sections and not blockers else "blocked", "page_id": page.slug, "available_patterns": sorted(PATTERNS), "sections": sections, "blockers": blockers}
