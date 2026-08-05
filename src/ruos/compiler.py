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
from .pattern_resolver import PatternPlan, resolve_patterns
from .qa import evaluate
from .render import render_css, render_document, render_runtime
from .visual_dna import VisualDNA, resolve_visual_dna


ENGINE_NAME = "ruos-engine"
ENGINE_VERSION = "0.5.0"


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


def _canonical_payload(
    page: PageSpec,
    dna: VisualDNA,
    components: ComponentPlan,
    patterns: PatternPlan,
    html: str,
    css: str,
    runtime: str,
) -> dict[str, object]:
    visual_payload = dict(dna.fingerprint_payload())
    component_payload = _component_payload(components)
    pattern_payload = _pattern_payload(patterns)
    canonical_components = json.dumps(
        component_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    canonical_patterns = json.dumps(
        pattern_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "page": page.slug,
        "visual_profile": dna.id,
        "visual_dna": visual_payload,
        "visual_dna_sha256": hashlib.sha256(
            json.dumps(visual_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "component_plan": component_payload,
        "component_plan_sha256": hashlib.sha256(canonical_components.encode("utf-8")).hexdigest(),
        "pattern_plan": pattern_payload,
        "pattern_plan_sha256": hashlib.sha256(canonical_patterns.encode("utf-8")).hexdigest(),
        "spec": asdict(page),
        "artifacts": {
            "index.html": _digest(html),
            "assets/styles.css": _digest(css),
            "assets/runtime.js": _digest(runtime),
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
    html = render_document(page, components)
    css = render_css(dna)
    runtime = render_runtime()
    gates = evaluate(page, html, css, runtime)

    rejected = [gate for gate in gates if not gate.passed]
    if context.strict and rejected:
        summary = "; ".join(f"{gate.gate}: {', '.join(gate.failures)}" for gate in rejected)
        raise BuildRejected(summary)

    payload = _canonical_payload(page, dna, components, patterns, html, css, runtime)
    build_id = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]

    staging_root = Path(tempfile.mkdtemp(prefix=f".ruos-{page.slug}-", dir=str(context.output_root)))
    try:
        assets_dir = staging_root / "assets"
        files = (
            _write(staging_root / "index.html", html),
            _write(assets_dir / "styles.css", css),
            _write(assets_dir / "runtime.js", runtime),
        )
        manifest = {
            **payload,
            "build_id": build_id,
            "built_at": datetime.now(timezone.utc).isoformat(),
            "strict": context.strict,
            "passed": all(gate.passed for gate in gates),
            "files": [str(path.relative_to(staging_root)) for path in files],
            "sha256": {
                str(path.relative_to(staging_root)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in files
            },
            "gates": [asdict(gate) for gate in gates],
        }
        manifest_path = _write(
            staging_root / "build-manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        )
        qa_path = _write(
            staging_root / "qa-report.json",
            json.dumps([asdict(gate) for gate in gates], ensure_ascii=False, indent=2),
        )
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
    return BuildResult(
        page=page,
        output_dir=output_dir,
        files=published_files + (published_manifest, published_qa),
        gates=gates,
    )
