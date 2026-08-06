from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping

from .build_research_gate import require_verified_live_research
from .compiler import BuildRejected, compile_page
from .live_research import LiveResearchAdapter, LiveResearchError
from .models import BuildContext
from .research_snapshot import build_snapshot, write_snapshot
from .spec_loader import SpecError, load_page_spec


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ruos")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Compile one page specification")
    build.add_argument("page", help="Page slug, for example: structures")
    build.add_argument("--spec-root", default="pages", help="Directory containing page JSON specs")
    build.add_argument("--output", default="dist", help="Build output directory")
    build.add_argument("--no-strict", action="store_true", help="Write output even when a gate fails")
    build.add_argument(
        "--require-live-research",
        action="store_true",
        help="Reject the build unless a complete, fresh, verified live research snapshot exists",
    )
    build.add_argument(
        "--snapshot-root",
        default=".ruos/research",
        help="Directory containing verified live research snapshots",
    )
    build.add_argument(
        "--research-max-age-days",
        type=int,
        default=14,
        help="Maximum accepted live research snapshot age in days",
    )

    research = sub.add_parser("research", help="Fetch live sources and write a verified evidence snapshot")
    research.add_argument("page", help="Page slug, for example: structures")
    research.add_argument("--spec-root", default="pages", help="Directory containing page JSON specs")
    research.add_argument(
        "--snapshot-root",
        default=".ruos/research",
        help="Directory for deterministic live research snapshots",
    )
    return parser


def _research_sources(page) -> tuple[Mapping[str, object], ...]:
    research = page.metadata.get("research")
    if not isinstance(research, Mapping):
        raise LiveResearchError("Page metadata must include a research object")
    raw_sources = research.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise LiveResearchError("Page research must include at least one source")
    sources: list[Mapping[str, object]] = []
    for index, source in enumerate(raw_sources, start=1):
        if not isinstance(source, Mapping):
            raise LiveResearchError(f"Research source #{index} must be an object")
        sources.append(source)
    return tuple(sources)


def _run_research(page, snapshot_path: Path) -> int:
    adapter = LiveResearchAdapter()
    evidence = []
    for source in _research_sources(page):
        source_id = str(source.get("id", "")).strip()
        url = str(source.get("url", "")).strip()
        notes = str(source.get("notes", "")).strip()
        print(f"RUOS RESEARCH FETCH: {source_id} {url}")
        evidence.append(
            adapter.fetch_source(
                source_id,
                url,
                manual_claims=(notes,) if notes else (),
            )
        )
    snapshot = build_snapshot(page.slug, evidence)
    write_snapshot(snapshot, snapshot_path)
    print(f"RUOS RESEARCH SNAPSHOT: {snapshot_path}")
    print(f"RUOS RESEARCH SHA256: {snapshot.sha256}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    project_root = Path.cwd()
    spec_path = project_root / args.spec_root / f"{args.page}.json"

    try:
        page = load_page_spec(spec_path)
        if args.command == "research":
            snapshot_path = project_root / args.snapshot_root / f"{page.slug}.json"
            return _run_research(page, snapshot_path)

        snapshot_root = project_root / args.snapshot_root
        if args.require_live_research:
            verified = require_verified_live_research(
                page,
                snapshot_root / f"{page.slug}.json",
                max_age_days=args.research_max_age_days,
            )
            print(
                f"RUOS LIVE RESEARCH VERIFIED: {verified.source_count} sources "
                f"snapshot={verified.snapshot_sha256}"
            )

        result = compile_page(
            page,
            BuildContext(
                project_root=project_root,
                output_root=project_root / args.output,
                strict=not args.no_strict,
                require_live_research=args.require_live_research,
                research_snapshot_root=snapshot_root,
            ),
        )
    except (SpecError, BuildRejected, LiveResearchError) as exc:
        label = "RESEARCH FAILED" if args.command == "research" else "BUILD REJECTED"
        print(f"RUOS {label}: {exc}", file=sys.stderr)
        return 2

    print(f"RUOS BUILD PASSED: {result.output_dir}")
    for path in result.files:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
