from __future__ import annotations

import json
from pathlib import Path

from .cie_gate import build_creative_blueprint
from .compiler import BuildRejected, compile_page
from .component_resolver import resolve_components
from .content_composer import compose_content
from .creative_intelligence import build_creative_intelligence
from .models import BuildContext, BuildResult, PageSpec
from .motion_composer import compose_motion
from .pattern_resolver import resolve_patterns


def generate_cie_blueprint(page: PageSpec) -> dict[str, object]:
    """Generate the deterministic pre-build Creative Blueprint for a page."""
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    components = resolve_components(page)
    patterns = resolve_patterns(page, components)
    motion = compose_motion(patterns, components)
    return build_creative_blueprint(page, content, intelligence, patterns, motion)


def write_cie_blueprint(page: PageSpec, output_root: Path) -> Path:
    blueprint = generate_cie_blueprint(page)
    output = output_root / page.slug / "creative-blueprint.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return output


def compile_page_with_cie(page: PageSpec, context: BuildContext) -> BuildResult:
    """Run the CIE blocking gate before entering the existing RUOS compiler."""
    blueprint = generate_cie_blueprint(page)
    gate = blueprint["gate"]
    status = str(gate.get("status", "blocked"))
    if status == "blocked":
        failed = ", ".join(str(item) for item in gate.get("failed_rules", [])) or "unknown CIE gate failure"
        report = blueprint.get("gate_report", {})
        remediation = "; ".join(str(item) for item in report.get("remediation_actions", []))
        detail = f"CIE pre-build gate blocked: {failed}"
        if remediation:
            detail += f"; remediation: {remediation}"
        raise BuildRejected(detail)

    result = compile_page(page, context)
    blueprint_path = result.output_dir / "creative-blueprint.json"
    blueprint_path.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return BuildResult(
        page=result.page,
        output_dir=result.output_dir,
        files=result.files + (blueprint_path,),
        gates=result.gates,
    )
