from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cie_build import compile_page_with_cie, generate_cie_blueprint
from .cli import _run_3d_evidence
from .compiler import BuildRejected
from .models import BuildContext
from .spec_loader import SpecError, load_page_spec


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ruos-cie", description="Creative Intelligence Engine pre-build runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    blueprint = sub.add_parser("blueprint", help="Generate and inspect the Creative Blueprint without building")
    blueprint.add_argument("page")
    blueprint.add_argument("--spec-root", default="pages")
    blueprint.add_argument("--output", default=".ruos/cie")

    build = sub.add_parser("build", help="Run CIE blocking gate and compile only when the gate allows build")
    build.add_argument("page")
    build.add_argument("--spec-root", default="pages")
    build.add_argument("--output", default="dist")
    build.add_argument("--no-strict", action="store_true")
    build.add_argument("--require-publish-media", action="store_true", help="Resolve real media and block publish when integrity/provenance/license/semantics/posters are incomplete")
    build.add_argument("--media-bindings", help="JSON object keyed by section_id:asset_id (or asset_id when unique) with source and publish metadata")
    build.add_argument("--produce-media", action="store_true", help="Generate real image/SVG derivatives and use ffmpeg/gltf-transform adapters when available")
    build.add_argument("--media-output-subdir", default="assets/generated-media", help="Build-relative directory for generated media derivatives")
    build.add_argument("--require-3d-lod-qa", action="store_true", help="Block runtime 3D delivery unless source/high/medium LOD QA passes")
    build.add_argument("--3d-source-map", dest="three_d_source_map", help="JSON map of section_id to authored .blend source")
    build.add_argument("--3d-visual-approvals", dest="three_d_visual_approvals", help="JSON visual QA approvals keyed by section_id")

    evidence = sub.add_parser("capture-3d-evidence", help="Render deterministic source/high/medium comparisons and create a human-review template")
    evidence.add_argument("page")
    evidence.add_argument("--spec-root", default="pages")
    evidence.add_argument("--3d-source-map", dest="three_d_source_map", required=True)
    evidence.add_argument("--output-root", default=".ruos/3d-evidence")
    evidence.add_argument("--blender-script", default="scripts/cie_blender_visual_evidence.py")
    evidence.add_argument("--blender-executable", default="blender")
    evidence.add_argument("--timeout", type=int, default=300)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path.cwd()
    try:
        page = load_page_spec(root / args.spec_root / f"{args.page}.json")
        if args.command == "blueprint":
            result = generate_cie_blueprint(page)
            output = root / args.output / f"{page.slug}.creative-blueprint.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
            gate = result["gate"]
            print(f"RUOS CIE BLUEPRINT: {output}")
            print(f"RUOS CIE STATUS: {gate['status']}")
            report = result.get("gate_report", {})
            print(f"RUOS CIE SCORE: {report.get('score', 0)}")
            if gate["status"] == "blocked":
                print("RUOS CIE BUILD BLOCKED", file=sys.stderr)
                return 2
            return 0

        if args.command == "capture-3d-evidence":
            return _run_3d_evidence(page, args, root)

        if args.produce_media and not args.require_publish_media:
            raise BuildRejected("--produce-media requires --require-publish-media so source integrity and rights are validated before derivative production")
        if args.require_publish_media and not args.media_bindings:
            raise BuildRejected("--require-publish-media requires --media-bindings")
        if args.require_3d_lod_qa and not args.produce_media:
            raise BuildRejected("--require-3d-lod-qa requires --produce-media")
        if args.require_3d_lod_qa and (not args.three_d_source_map or not args.three_d_visual_approvals):
            raise BuildRejected("--require-3d-lod-qa requires --3d-source-map and --3d-visual-approvals")
        context = BuildContext(
            project_root=root,
            output_root=root / args.output,
            strict=not args.no_strict,
            require_publish_media=bool(args.require_publish_media),
            media_bindings_path=Path(args.media_bindings) if args.media_bindings else None,
            produce_media_derivatives=bool(args.produce_media),
            media_output_subdir=str(args.media_output_subdir),
            require_3d_lod_qa=bool(args.require_3d_lod_qa),
            three_d_source_map_path=Path(args.three_d_source_map) if args.three_d_source_map else None,
            three_d_visual_approvals_path=Path(args.three_d_visual_approvals) if args.three_d_visual_approvals else None,
        )
        result = compile_page_with_cie(page, context)
        print(f"RUOS CIE BUILD PASSED: {result.output_dir}")
        for path in result.files:
            print(path)
        return 0
    except (SpecError, BuildRejected, ValueError) as exc:
        print(f"RUOS CIE BUILD REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
