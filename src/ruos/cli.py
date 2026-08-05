from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .compiler import BuildRejected, compile_page
from .models import BuildContext
from .spec_loader import SpecError, load_page_spec


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ruos")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Compile one page specification")
    build.add_argument("page", help="Page slug, for example: structures")
    build.add_argument("--spec-root", default="pages", help="Directory containing page JSON specs")
    build.add_argument("--output", default="dist", help="Build output directory")
    build.add_argument("--no-strict", action="store_true", help="Write output even when a gate fails")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    project_root = Path.cwd()
    spec_path = project_root / args.spec_root / f"{args.page}.json"

    try:
        page = load_page_spec(spec_path)
        result = compile_page(
            page,
            BuildContext(
                project_root=project_root,
                output_root=project_root / args.output,
                strict=not args.no_strict,
            ),
        )
    except (SpecError, BuildRejected) as exc:
        print(f"RUOS BUILD REJECTED: {exc}", file=sys.stderr)
        return 2

    print(f"RUOS BUILD PASSED: {result.output_dir}")
    for path in result.files:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
