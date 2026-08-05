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
from .models import BuildContext, BuildResult, PageSpec
from .motion_composer import MotionPlan, compose_motion
from .pattern_resolver import PatternPlan, resolve_patterns
from .qa import evaluate
from .render import render_css, render_document, render_runtime
from .visual_dna import VisualDNA, resolve_visual_dna


ENGINE_NAME = "ruos-engine"
ENGINE_VERSION = "0.6.0"


class BuildRejected(RuntimeError):
    pass


class BuildFailure(RuntimeError):
    pass


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def _digest(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _component_payload(plan: ComponentPlan) -> list[dict[str, object]]:
    return [
        {
            "id": component.id,
            "section_id": component.section_id,
            "family": component.family,
            "variant": component.variant,
            "density": component.density,
            "emphasis": component.emphasis,
            "capabilities": list(component.capabilities),
            "attributes": dict(component.attributes),
        }
        for component in plan.components
    ]


def _pattern_payload(plan: PatternPlan) -> dict[str, object]:
    return {
        "page_slug": plan.page_slug,
        "narrative_arc": plan.narrative_arc,
        "global_motif": plan.global_motif,
        "scroll_model": plan.scroll_model,
        "sections": [
            {
                "section_id": pattern.section_id,
                "chapter": pattern.chapter,
                "entrance": pattern.entrance,
                "transition": pattern.transition,
                "alignment": pattern.alignment,
                "pacing": pattern.pacing,
                "motif": pattern.motif,
                "attributes": dict(pattern.attributes),
            }
            for pattern in plan.sections
        ],
    }


def _motion_payload(plan: MotionPlan) -> dict[str, object]:
    return {
        "page_slug": plan.page_slug,
        "strategy": plan.strategy,
        "reduced_motion_policy": plan.reduced_motion_policy,
        "cues": [
            {
                "section_id": cue.section_id,
                "order": cue.order,
                "trigger": cue.trigger,
                "target": cue.target,
                "effect": cue.effect,
                "duration_ms": cue.duration_ms,
                "delay_ms": cue.delay_ms,
                "easing": cue.easing,
                "once": cue.once,
                "reduced_effect": cue.reduced_effect,
                "attributes": dict(cue.attributes),
            }
            for cue in plan.cues
        ],
    }


def _motion_runtime(plan: MotionPlan) -> str:
    payload = json.dumps(_motion_payload(plan), ensure_ascii=False, separators=(",", ":"))
    return f'''\nconst RUOS_MOTION={payload};
const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const motionEffects={{
  'rise-fade':{{opacity:['0','1'],transform:['translateY(32px)','none']}},
  'drift-fade':{{opacity:['0','1'],transform:['translateX(24px)','none']}},
  'stagger-cards':{{opacity:['0','1'],transform:['translateY(22px)','none']}},
  'focus-expand':{{opacity:['0','1'],transform:['scale(.975)','none']}},
  'expand-fade':{{opacity:['0','1'],transform:['scale(.96) translateY(18px)','none']}}
}};
for(const cue of RUOS_MOTION.cues){{
  const section=document.getElementById(cue.section_id);if(!section)continue;
  const targets=[...section.querySelectorAll(cue.target)];if(!targets.length)continue;
  if(reduceMotion){{for(const target of targets){{target.style.opacity='1';target.style.transform='none';}}continue;}}
  const motionObserver=new IntersectionObserver(entries=>{{for(const entry of entries){{if(!entry.isIntersecting)continue;targets.forEach((target,index)=>target.animate(motionEffects[cue.effect],{{duration:cue.duration_ms,delay:cue.delay_ms+index*Number(cue.attributes.stagger||0),easing:cue.easing,fill:'both'}}));if(cue.once)motionObserver.disconnect();}}}},{{threshold:.2}});
  motionObserver.observe(section);
}}
'''.strip()


def _canonical_payload(
    page: PageSpec,
    dna: VisualDNA,
    components: ComponentPlan,
    patterns: PatternPlan,
    motion: MotionPlan,
    html: str,
    css: str,
    runtime: str,
) -> dict[str, object]:
    visual_payload = dict(dna.fingerprint_payload())
    component_payload = _component_payload(components)
    pattern_payload = _pattern_payload(patterns)
    motion_payload = _motion_payload(motion)
    canonical_components = json.dumps(component_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    canonical_patterns = json.dumps(pattern_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    canonical_motion = json.dumps(motion_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "page": page.slug,
        "visual_profile": dna.id,
        "visual_dna": visual_payload,
        "visual_dna_sha256": hashlib.sha256(json.dumps(visual_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
        "component_plan": component_payload,
        "component_plan_sha256": hashlib.sha256(canonical_components.encode("utf-8")).hexdigest(),
        "pattern_plan": pattern_payload,
        "pattern_plan_sha256": hashlib.sha256(canonical_patterns.encode("utf-8")).hexdigest(),
        "motion_plan": motion_payload,
        "motion_plan_sha256": hashlib.sha256(canonical_motion.encode("utf-8")).hexdigest(),
        "spec": asdict(page),
        "artifacts": {
            "index.html": _digest(html),
            "assets/styles.css": _digest(css),
            "assets/runtime.js": _digest(runtime),
            "assets/motion-manifest.json": _digest(json.dumps(motion_payload, ensure_ascii=False, indent=2, sort_keys=True)),
        },
    }


def _atomic_publish(staging_dir: Path, output_dir: Path) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = output_dir.with_name(f".{output_dir.name}.previous")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    if output_dir.exists():
        output_dir.replace(backup_dir)
    try:
        staging_dir.replace(output_dir)
    except OSError as exc:
        if backup_dir.exists() and not output_dir.exists():
            backup_dir.replace(output_dir)
        raise BuildFailure(f"Unable to publish build for {output_dir.name}: {exc}") from exc
    else:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)


def compile_page(page: PageSpec, context: BuildContext) -> BuildResult:
    output_dir = context.output_root / page.slug
    context.output_root.mkdir(parents=True, exist_ok=True)

    dna = resolve_visual_dna(page.visual_profile)
    components = resolve_components(page)
    patterns = resolve_patterns(page, components)
    motion = compose_motion(patterns, components)
    html = render_document(page, components)
    css = render_css(dna)
    runtime = render_runtime() + "\n" + _motion_runtime(motion)
    gates = evaluate(page, html, css, runtime)

    rejected = [gate for gate in gates if not gate.passed]
    if context.strict and rejected:
        summary = "; ".join(f"{gate.gate}: {', '.join(gate.failures)}" for gate in rejected)
        raise BuildRejected(summary)

    payload = _canonical_payload(page, dna, components, patterns, motion, html, css, runtime)
    build_id = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]

    staging_root = Path(tempfile.mkdtemp(prefix=f".ruos-{page.slug}-", dir=str(context.output_root)))
    try:
        assets_dir = staging_root / "assets"
        motion_json = json.dumps(_motion_payload(motion), ensure_ascii=False, indent=2, sort_keys=True)
        files = (
            _write(staging_root / "index.html", html),
            _write(assets_dir / "styles.css", css),
            _write(assets_dir / "runtime.js", runtime),
            _write(assets_dir / "motion-manifest.json", motion_json),
        )
        manifest = {
            **payload,
            "build_id": build_id,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "strict": context.strict,
            "passed": all(gate.passed for gate in gates),
            "files": [str(path.relative_to(staging_root)) for path in files],
            "sha256": {str(path.relative_to(staging_root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
            "gates": [asdict(gate) for gate in gates],
        }
        manifest_path = _write(staging_root / "build-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        qa_path = _write(staging_root / "qa-report.json", json.dumps([asdict(gate) for gate in gates], ensure_ascii=False, indent=2))
        _write(staging_root / ".ruos-build", f"{build_id}\n")
        _atomic_publish(staging_root, output_dir)
    except Exception:
        if staging_root.exists():
            shutil.rmtree(staging_root, ignore_errors=True)
        raise

    published_files = tuple(output_dir / path.relative_to(staging_root) for path in files)
    published_manifest = output_dir / manifest_path.relative_to(staging_root)
    published_qa = output_dir / qa_path.relative_to(staging_root)

    os.utime(output_dir, None)
    return BuildResult(page=page, output_dir=output_dir, files=published_files + (published_manifest, published_qa), gates=gates)
