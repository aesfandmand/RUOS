from __future__ import annotations

from typing import Any, Mapping

from .component_resolver import ComponentPlan
from .models import PageSpec

_REQUIRED_SECTION_FIELDS = {"section_id","component","dom","css","interaction_hooks","motion_hooks","responsive","assets","qa_assertions","experience_pattern","scene_orchestration","visual_scene_composition"}


def _component_contract(component: Any) -> dict[str, Any]:
    return {"id":component.id,"family":component.family,"variant":component.variant,"density":component.density,"emphasis":component.emphasis,"capabilities":list(component.capabilities),"attributes":dict(component.attributes)}


def _dom_contract(decision: Mapping[str, Any]) -> dict[str, Any]:
    heading=str(decision.get("heading","")).strip(); cta=decision.get("cta",{}) if isinstance(decision.get("cta"),Mapping) else {}
    return {"root":"section","id":str(decision.get("section_id","")),"required_landmarks":["heading","content"],"heading":{"text":heading,"semantic_level":"h1" if int(decision.get("chapter",0) or 0)==1 else "h2"},"content_order":["eyebrow","heading","body","evidence","entities","cta"],"cta":{"required":bool(cta.get("href")),"label":cta.get("label"),"href":cta.get("href")},"semantic_parity_required":True}


def _css_contract(component: Any, decision: Mapping[str, Any]) -> dict[str, Any]:
    return {"layout":component.attributes.get("layout","flow"),"surface":component.attributes.get("surface","default"),"heading_scale":component.attributes.get("heading_scale","feature"),"visual_treatment":str(decision.get("visual_treatment","")),"responsive_strategy":"single-codebase-fluid-layout","container_queries_allowed":True,"no_desktop_only_content":True}


def _responsive_contract(decision: Mapping[str, Any]) -> dict[str, Any]:
    return {"desktop":"execute the full section decision without hiding semantic content","tablet":"preserve hierarchy and interaction purpose while reducing spatial complexity","mobile":str(decision.get("mobile_translation","touch-first vertical semantic sequence")),"reduced_motion":str(decision.get("fallback","static semantic layout")),"touch_targets_min_px":44,"hover_only_forbidden":True,"content_parity_required":True}


def _asset_contract(component: Any, decision: Mapping[str, Any]) -> list[dict[str, Any]]:
    assets=[]; capabilities=set(component.capabilities)
    if "ambient-art" in capabilities: assets.append({"slot":"hero-art","type":"image-or-webgl","required":False,"fallback":"responsive-image-or-svg","alt_required":True})
    if "visual-pause" in capabilities: assets.append({"slot":"editorial-visual","type":"image-or-video","required":False,"fallback":"image","alt_required":True})
    if "indexed-cards" in capabilities: assets.append({"slot":"item-media","type":"image-or-diagram","required":False,"fallback":"text-and-svg","alt_required":True})
    if decision.get("content_role")=="tool": assets.append({"slot":"interaction-state-art","type":"svg-or-canvas","required":False,"fallback":"semantic-html-state","alt_required":False})
    return assets


def _qa_contract(decision: Mapping[str, Any], component: Any) -> list[dict[str, Any]]:
    section_id=str(decision.get("section_id","")); checks=[
        {"id":f"{section_id}:semantic-heading","assert":"section has exactly one expected heading and remains readable without JavaScript"},
        {"id":f"{section_id}:responsive-parity","assert":"desktop and mobile expose equivalent content, evidence, entities and CTA"},
        {"id":f"{section_id}:touch-keyboard","assert":"all interactive controls are keyboard reachable and touch targets are at least 44px"},
        {"id":f"{section_id}:reduced-motion","assert":"prefers-reduced-motion preserves information and action state"},
        {"id":f"{section_id}:anti-copy","assert":"implementation does not reproduce approved reference geometry, copy, assets or signature sequences verbatim"},
        {"id":f"{section_id}:experience-fallback","assert":"selected experience pattern preserves content and action when advanced enhancement is unavailable"},
        {"id":f"{section_id}:scene-order","assert":"scene states are ordered, deterministic and preserve semantic meaning without continuous animation"},
        {"id":f"{section_id}:visual-composition","assert":"camera, depth, layers and transitions preserve semantic content on mobile and reduced motion"},
    ]
    if "primary-cta" in component.capabilities: checks.append({"id":f"{section_id}:cta","assert":"CTA label and destination are visible, actionable and semantically correct"})
    return checks


def _index(plan: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if not isinstance(plan,Mapping): return {}
    raw=plan.get("sections",[])
    if not isinstance(raw,list): return {}
    return {str(item.get("section_id")):item for item in raw if isinstance(item,Mapping) and item.get("section_id")}


def build_ui_implementation_contract(page: PageSpec, components: ComponentPlan, creative_director: Mapping[str, Any], experience_patterns: Mapping[str, Any] | None=None, scene_orchestration: Mapping[str, Any] | None=None, visual_scene_composition: Mapping[str, Any] | None=None) -> dict[str, Any]:
    if creative_director.get("status")!="ready": return {"version":"1.2","status":"blocked","page_id":page.slug,"sections":[],"blockers":["creative director plan is not ready"]}
    decisions=creative_director.get("sections",[])
    if not isinstance(decisions,list): return {"version":"1.2","status":"blocked","page_id":page.slug,"sections":[],"blockers":["creative director sections must be a list"]}
    experience_index=_index(experience_patterns); scene_index=_index(scene_orchestration); visual_index=_index(visual_scene_composition)
    contracts=[]; blockers=[]
    for decision in decisions:
        if not isinstance(decision,Mapping): blockers.append("all creative director section decisions must be objects"); continue
        section_id=str(decision.get("section_id","")).strip()
        if not section_id: blockers.append("section decision missing section_id"); continue
        component=components.for_section(section_id); motion=decision.get("motion") if isinstance(decision.get("motion"),Mapping) else None; interaction=str(decision.get("interaction","")).strip(); experience=experience_index.get(section_id); scene=scene_index.get(section_id); visual=visual_index.get(section_id)
        if experience_patterns is not None and experience is None: blockers.append(f"{section_id} missing experience pattern")
        if scene_orchestration is not None and scene is None: blockers.append(f"{section_id} missing scene orchestration")
        if visual_scene_composition is not None and visual is None: blockers.append(f"{section_id} missing visual scene composition")
        contract={
            "section_id":section_id,
            "component":_component_contract(component),
            "experience_pattern":dict(experience) if experience else {"section_id":section_id,"pattern":"editorial-reveal","fallback":"static semantic layout"},
            "scene_orchestration":dict(scene) if scene else {"section_id":section_id,"driver":"static","scenes":[{"id":"static","range":[0,1],"state":"static","actions":["preserve-content"]}]},
            "visual_scene_composition":dict(visual) if visual else {"section_id":section_id,"pattern":"editorial-reveal","scenes":[]},
            "dom":_dom_contract(decision),"css":_css_contract(component,decision),
            "interaction_hooks":{"mode":interaction or "none","data_attributes":[f"data-ruos-section={section_id}",f"data-ruos-variant={component.variant}"],"keyboard_required":"keyboard-ready" in component.capabilities or component.family=="interactive","touch_required":True},
            "motion_hooks":{"enabled":motion is not None,"trigger":motion.get("trigger") if motion else None,"target":motion.get("target") if motion else None,"effect":motion.get("effect") if motion else None,"duration_ms":motion.get("duration_ms") if motion else None,"easing":motion.get("easing") if motion else None,"reduced_motion_fallback":str(decision.get("fallback","static semantic layout"))},
            "responsive":_responsive_contract(decision),"assets":_asset_contract(component,decision),"qa_assertions":_qa_contract(decision,component),"entity_mapping":list(decision.get("entity_mapping",[])),"schema_mapping":list(decision.get("schema_mapping",[])),"evidence":list(decision.get("evidence",[])),
        }
        missing=sorted(_REQUIRED_SECTION_FIELDS-set(contract))
        if missing: blockers.append(f"{section_id} missing implementation fields: {', '.join(missing)}")
        contracts.append(contract)
    if len(contracts)!=len(components.components): blockers.append("implementation contract requires exactly one section contract per resolved component")
    status="ready" if contracts and not blockers else "blocked"
    return {"version":"1.2","status":status,"page_id":page.slug,"execution_model":"single-codebase-progressive-enhancement","global_contract":{"semantic_html_first":True,"css_layout_before_scripted_positioning":True,"javascript_progressive_enhancement":True,"mobile_touch_first":True,"keyboard_access_required":True,"reduced_motion_required":True,"asset_fallback_required":True,"anti_copy_required":True,"experience_pattern_engine_required":True,"scene_orchestration_required":True,"visual_scene_composition_required":True},"sections":contracts,"blockers":blockers}
