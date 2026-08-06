from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .component_resolver import ComponentPlan, resolve_components
from .content_composer import ContentPlan, compose_content
from .creative_intelligence import CreativeIntelligencePlan, build_creative_intelligence
from .models import BuildContext, BuildResult, PageSpec
from .motion_composer import MotionPlan, compose_motion
from .page_choreographer import choreograph_page
from .pattern_resolver import PatternPlan, resolve_patterns
from .qa import evaluate
from .quality_score import AgencyQualityScore, calculate_agency_quality
from .render import render_css, render_document, render_runtime
from .semantic_enhancer import enhance_semantics
from .studio_artifacts import StudioArtifactBundle, build_studio_artifacts
from .visual_dna import VisualDNA, resolve_visual_dna

ENGINE_NAME = "ruos-engine"
ENGINE_VERSION = "1.1.0"

class BuildRejected(RuntimeError): pass
class BuildFailure(RuntimeError): pass

def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content, encoding="utf-8", newline="\n"); return path

def _digest(content: str) -> str: return hashlib.sha256(content.encode("utf-8")).hexdigest()
def _hash_payload(value: object) -> str: return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
def _component_payload(plan: ComponentPlan) -> list[dict[str, object]]: return [{"id": c.id, "section_id": c.section_id, "family": c.family, "variant": c.variant, "density": c.density, "emphasis": c.emphasis, "capabilities": list(c.capabilities), "attributes": dict(c.attributes)} for c in plan.components]
def _pattern_payload(plan: PatternPlan) -> dict[str, object]: return {"page_slug": plan.page_slug, "narrative_arc": plan.narrative_arc, "global_motif": plan.global_motif, "scroll_model": plan.scroll_model, "sections": [{"section_id": p.section_id, "chapter": p.chapter, "entrance": p.entrance, "transition": p.transition, "alignment": p.alignment, "pacing": p.pacing, "motif": p.motif, "attributes": dict(p.attributes)} for p in plan.sections]}
def _motion_payload(plan: MotionPlan) -> dict[str, object]: return {"page_slug": plan.page_slug, "strategy": plan.strategy, "reduced_motion_policy": plan.reduced_motion_policy, "cues": [{"section_id": c.section_id, "order": c.order, "trigger": c.trigger, "target": c.target, "effect": c.effect, "duration_ms": c.duration_ms, "delay_ms": c.delay_ms, "easing": c.easing, "once": c.once, "reduced_effect": c.reduced_effect, "attributes": dict(c.attributes)} for c in plan.cues]}
def _content_payload(plan: ContentPlan) -> dict[str, object]: return {"page_slug": plan.page_slug, "language": plan.language, "direction": plan.direction, "primary_intent": plan.primary_intent, "blocks": [{"section_id": b.section_id, "role": b.role, "heading_level": b.heading_level, "intent": b.intent, "title": b.title, "body": b.body, "cta_label": b.cta_label, "cta_href": b.cta_href, "entities": list(b.entities), "attributes": dict(b.attributes)} for b in plan.blocks]}
def _intelligence_payload(plan: CreativeIntelligencePlan) -> dict[str, object]: return {"page_slug": plan.page_slug, "query": {"primary_query": plan.query.primary_query, "supporting_queries": list(plan.query.supporting_queries), "search_intent": plan.query.search_intent, "journey_stage": plan.query.journey_stage}, "sales": {"conversion_goal": plan.sales.conversion_goal, "value_proposition": plan.sales.value_proposition, "friction_policy": plan.sales.friction_policy, "proof_requirements": list(plan.sales.proof_requirements), "cta_sequence": list(plan.sales.cta_sequence)}, "semantic": {"primary_entity": plan.semantic.primary_entity, "entities": list(plan.semantic.entities), "schema_types": list(plan.semantic.schema_types), "answer_targets": list(plan.semantic.answer_targets), "ai_summary": plan.semantic.ai_summary}, "creative": {"emotional_curve": list(plan.creative.emotional_curve), "narrative_model": plan.creative.narrative_model, "persuasion_principles": list(plan.creative.persuasion_principles), "visual_direction": plan.creative.visual_direction, "attributes": dict(plan.creative.attributes)}}
def _quality_payload(score: AgencyQualityScore) -> dict[str, object]: return {"total": score.total, "grade": score.grade, "publishable": score.publishable, "threshold": 88, "dimensions": [{"name": item.name, "score": item.score, "weight": item.weight} for item in score.dimensions], "blockers": list(score.blockers)}
def _studio_payload(bundle: StudioArtifactBundle) -> dict[str, object]: return {"manifest": bundle.manifest(), "artifacts": {artifact.name: {"owner": artifact.owner, "dependencies": list(artifact.dependencies), "payload": dict(artifact.payload), "sha256": artifact.sha256} for artifact in bundle.artifacts}}

def _motion_runtime(plan: MotionPlan) -> str:
    payload = json.dumps(_motion_payload(plan), ensure_ascii=False, separators=(",", ":"))
    return f'''\nconst RUOS_MOTION={payload};
const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const motionEffects={{'rise-fade':{{opacity:['0','1'],transform:['translateY(32px)','none']}},'drift-fade':{{opacity:['0','1'],transform:['translateX(24px)','none']}},'stagger-cards':{{opacity:['0','1'],transform:['translateY(22px)','none']}},'focus-expand':{{opacity:['0','1'],transform:['scale(.975)','none']}},'expand-fade':{{opacity:['0','1'],transform:['scale(.96) translateY(18px)','none']}}}};
for(const cue of RUOS_MOTION.cues){{const section=document.getElementById(cue.section_id);if(!section)continue;const targets=[...section.querySelectorAll(cue.target)];if(!targets.length)continue;if(reduceMotion){{for(const target of targets){{target.style.opacity='1';target.style.transform='none';}}continue;}}const motionObserver=new IntersectionObserver(entries=>{{for(const entry of entries){{if(!entry.isIntersecting)continue;targets.forEach((target,index)=>target.animate(motionEffects[cue.effect],{{duration:cue.duration_ms,delay:cue.delay_ms+index*Number(cue.attributes.stagger||0),easing:cue.easing,fill:'both'}}));if(cue.once)motionObserver.disconnect();}}}},{{threshold:.2}});motionObserver.observe(section);}}
'''.strip()

def _canonical_payload(page: PageSpec, dna: VisualDNA, components: ComponentPlan, patterns: PatternPlan, motion: MotionPlan, content: ContentPlan, intelligence: CreativeIntelligencePlan, quality: AgencyQualityScore, studio: StudioArtifactBundle, html: str, css: str, runtime: str) -> dict[str, object]:
    visual_payload = dict(dna.fingerprint_payload()); component_payload = _component_payload(components); pattern_payload = _pattern_payload(patterns); motion_payload = _motion_payload(motion); content_payload = _content_payload(content); intelligence_payload = _intelligence_payload(intelligence); quality_payload = _quality_payload(quality); studio_payload = _studio_payload(studio)
    motion_json = json.dumps(motion_payload, ensure_ascii=False, indent=2, sort_keys=True); intelligence_json = json.dumps(intelligence_payload, ensure_ascii=False, indent=2, sort_keys=True); quality_json = json.dumps(quality_payload, ensure_ascii=False, indent=2, sort_keys=True); studio_manifest_json = json.dumps(studio.manifest(), ensure_ascii=False, indent=2, sort_keys=True)
    artifacts = {"index.html": _digest(html), "assets/styles.css": _digest(css), "assets/runtime.js": _digest(runtime), "assets/motion-manifest.json": _digest(motion_json), "assets/creative-intelligence.json": _digest(intelligence_json), "agency-quality-report.json": _digest(quality_json), "studio/manifest.json": _digest(studio_manifest_json)}
    for artifact in studio.artifacts: artifacts[f"studio/{artifact.name}"] = _digest(json.dumps(dict(artifact.payload), ensure_ascii=False, indent=2, sort_keys=True))
    return {"engine": ENGINE_NAME, "engine_version": ENGINE_VERSION, "page": page.slug, "visual_profile": dna.id, "visual_dna": visual_payload, "visual_dna_sha256": _hash_payload(visual_payload), "component_plan": component_payload, "component_plan_sha256": _hash_payload(component_payload), "pattern_plan": pattern_payload, "pattern_plan_sha256": _hash_payload(pattern_payload), "motion_plan": motion_payload, "motion_plan_sha256": _hash_payload(motion_payload), "content_plan": content_payload, "content_plan_sha256": _hash_payload(content_payload), "creative_intelligence": intelligence_payload, "creative_intelligence_sha256": _hash_payload(intelligence_payload), "agency_quality": quality_payload, "agency_quality_sha256": _hash_payload(quality_payload), "studio": studio_payload, "studio_sha256": _hash_payload(studio_payload), "spec": asdict(page), "artifacts": artifacts}

def _atomic_publish(staging_dir: Path, output_dir: Path) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True); backup_dir = output_dir.with_name(f".{output_dir.name}.previous")
    if backup_dir.exists(): shutil.rmtree(backup_dir)
    if output_dir.exists(): output_dir.replace(backup_dir)
    try: staging_dir.replace(output_dir)
    except OSError as exc:
        if backup_dir.exists() and not output_dir.exists(): backup_dir.replace(output_dir)
        raise BuildFailure(f"Unable to publish build for {output_dir.name}: {exc}") from exc
    else:
        if backup_dir.exists(): shutil.rmtree(backup_dir)

def compile_page(page: PageSpec, context: BuildContext) -> BuildResult:
    output_dir = context.output_root / page.slug; context.output_root.mkdir(parents=True, exist_ok=True)
    dna = resolve_visual_dna(page.visual_profile); content = compose_content(page); intelligence = build_creative_intelligence(page, content); components = resolve_components(page); patterns = resolve_patterns(page, components); motion = compose_motion(patterns, components)
    html = enhance_semantics(page, intelligence, render_document(page, components)).html; css = render_css(dna); runtime = render_runtime() + "\n" + _motion_runtime(motion); html, css, runtime = choreograph_page(page, html, css, runtime)
    gates = evaluate(page, html, css, runtime); quality = calculate_agency_quality(gates); studio = build_studio_artifacts(page, dna, components, patterns, motion, content, intelligence, gates, quality); studio_review = studio.by_name("agency-review.json").payload
    rejected = [gate for gate in gates if not gate.passed]; studio_publishable = bool(studio_review.get("publishable"))
    if context.strict and (rejected or not quality.publishable or not studio_publishable):
        details = [f"{gate.gate}: {', '.join(gate.failures)}" for gate in rejected]; details.extend(str(blocker) for blocker in studio_review.get("blockers", []))
        if not quality.publishable and not quality.blockers: details.append(f"agency-quality: score {quality.total} is below publish threshold 88")
        if not studio_publishable and not studio_review.get("blockers"): details.append("virtual-studio: specialist consensus was not reached")
        raise BuildRejected("; ".join(dict.fromkeys(details)))
    payload = _canonical_payload(page, dna, components, patterns, motion, content, intelligence, quality, studio, html, css, runtime); build_id = _hash_payload(payload)[:16]; staging_root = Path(tempfile.mkdtemp(prefix=f".ruos-{page.slug}-", dir=str(context.output_root)))
    try:
        assets_dir = staging_root / "assets"; studio_dir = staging_root / "studio"; motion_json = json.dumps(_motion_payload(motion), ensure_ascii=False, indent=2, sort_keys=True); intelligence_json = json.dumps(_intelligence_payload(intelligence), ensure_ascii=False, indent=2, sort_keys=True); quality_json = json.dumps(_quality_payload(quality), ensure_ascii=False, indent=2, sort_keys=True)
        files = [_write(staging_root / "index.html", html), _write(assets_dir / "styles.css", css), _write(assets_dir / "runtime.js", runtime), _write(assets_dir / "motion-manifest.json", motion_json), _write(assets_dir / "creative-intelligence.json", intelligence_json), _write(staging_root / "agency-quality-report.json", quality_json), _write(studio_dir / "manifest.json", json.dumps(studio.manifest(), ensure_ascii=False, indent=2, sort_keys=True))]
        for artifact in studio.artifacts: files.append(_write(studio_dir / artifact.name, json.dumps(dict(artifact.payload), ensure_ascii=False, indent=2, sort_keys=True)))
        manifest = {**payload, "build_id": build_id, "built_at": datetime.now(timezone.utc).isoformat(), "strict": context.strict, "passed": quality.publishable and studio_publishable, "files": [str(path.relative_to(staging_root)) for path in files], "sha256": {str(path.relative_to(staging_root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}, "gates": [asdict(gate) for gate in gates]}
        manifest_path = _write(staging_root / "build-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)); qa_path = _write(staging_root / "qa-report.json", json.dumps([asdict(gate) for gate in gates], ensure_ascii=False, indent=2)); _write(staging_root / ".ruos-build", f"{build_id}\n"); _atomic_publish(staging_root, output_dir)
    except Exception:
        if staging_root.exists(): shutil.rmtree(staging_root, ignore_errors=True)
        raise
    published_files = tuple(output_dir / path.relative_to(staging_root) for path in files); published_manifest = output_dir / manifest_path.relative_to(staging_root); published_qa = output_dir / qa_path.relative_to(staging_root); os.utime(output_dir, None)
    return BuildResult(page=page, output_dir=output_dir, files=published_files + (published_manifest, published_qa), gates=gates)
