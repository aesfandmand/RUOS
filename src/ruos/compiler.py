from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import BuildContext, BuildResult, PageSpec
from .qa import evaluate
from .render import render_css, render_document, render_runtime


class BuildRejected(RuntimeError):
    pass


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def compile_page(page: PageSpec, context: BuildContext) -> BuildResult:
    output_dir = context.output_root / page.slug
    assets_dir = output_dir / "assets"

    html = render_document(page)
    css = render_css()
    runtime = render_runtime()
    gates = evaluate(page, html, css, runtime)

    rejected = [gate for gate in gates if not gate.passed]
    if context.strict and rejected:
        summary = "; ".join(f"{gate.gate}: {', '.join(gate.failures)}" for gate in rejected)
        raise BuildRejected(summary)

    files = (
        _write(output_dir / "index.html", html),
        _write(assets_dir / "styles.css", css),
        _write(assets_dir / "runtime.js", runtime),
    )

    manifest = {
        "engine": "ruos-engine",
        "engine_version": "0.1.0",
        "page": page.slug,
        "visual_profile": page.visual_profile,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "strict": context.strict,
        "passed": all(gate.passed for gate in gates),
        "files": [str(path.relative_to(output_dir)) for path in files],
        "sha256": {
            str(path.relative_to(output_dir)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
        "gates": [asdict(gate) for gate in gates],
    }
    manifest_path = _write(
        output_dir / "build-manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )
    qa_path = _write(
        output_dir / "qa-report.json",
        json.dumps([asdict(gate) for gate in gates], ensure_ascii=False, indent=2),
    )

    return BuildResult(
        page=page,
        output_dir=output_dir,
        files=files + (manifest_path, qa_path),
        gates=gates,
    )
