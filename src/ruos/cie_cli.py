from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cie_build import compile_page_with_cie, generate_cie_blueprint
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
    build.add_argument("--media-bindings", help="JSON object keyed by asset_id with uri, poster_uri, provenance and semantic metadata")
    build.add_argument("--produce-media", action="store_true", help="Generate real image/SVG derivatives and use ffmpeg/gltf-transform adapters when available")
    build.add_argument("--media-output-subdir", default="assets/generated-media", help="Build-relative directory for generated media derivatives")
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

        if args.produce_media and not args.require_publish_media:
            raise BuildRejected("--produce-media requires --require-publish-media so source integrity and rights are validated before derivative production")
        context = BuildContext(
            project_root=root,
            output_root=root / args.output,
            strict=not args.no_strict,
            require_publish_media=bool(args.require_publish_media),
            media_bindings_path=Path(args.media_bindings) if args.media_bindings else None,
            produce_media_derivatives=bool(args.produce_media),
            media_output_subdir=str(args.media_output_subdir),
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
