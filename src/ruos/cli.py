from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping

from .compiler import BuildRejected, compile_page
from .discovery_snapshot import write_discovery
from .live_research import LiveResearchAdapter, LiveResearchError
from .models import BuildContext
from .production_build import compile_production_page
from .research_snapshot import build_snapshot, write_snapshot
from .search_discovery import create_provider, discover_search
from .spec_loader import SpecError, load_page_spec


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ruos")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Compile one page specification")
    build.add_argument("page")
    build.add_argument("--spec-root", default="pages")
    build.add_argument("--output", default="dist")
    build.add_argument("--no-strict", action="store_true")
    build.add_argument("--require-live-research", action="store_true")
    build.add_argument("--snapshot-root", default=".ruos/research")
    build.add_argument("--research-max-age-days", type=int, default=14)
    build.add_argument("--require-search-discovery", action="store_true")
    build.add_argument("--discovery-root", default=".ruos/discovery")
    build.add_argument("--discovery-max-age-days", type=int, default=7)
    build.add_argument("--discovery-minimum-results", type=int, default=5)

    research = sub.add_parser("research", help="Fetch configured live sources")
    research.add_argument("page")
    research.add_argument("--spec-root", default="pages")
    research.add_argument("--snapshot-root", default=".ruos/research")

    discover = sub.add_parser("discover", help="Run live search discovery for a page query")
    discover.add_argument("page")
    discover.add_argument("--spec-root", default="pages")
    discover.add_argument("--provider", choices=("brave", "serper"), default="brave")
    discover.add_argument("--query", default="")
    discover.add_argument("--market", default="ir")
    discover.add_argument("--language", default="fa")
    discover.add_argument("--count", type=int, default=10)
    discover.add_argument("--output-root", default=".ruos/discovery")
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


def _primary_query(page) -> str:
    query = page.metadata.get("query")
    if isinstance(query, Mapping):
        value = str(query.get("primary", "")).strip()
        if value:
            return value
    value = str(page.metadata.get("primary_query", "")).strip()
    if value:
        return value
    raise LiveResearchError("Page metadata must define a primary query or pass --query")


def _run_research(page, snapshot_path: Path) -> int:
    adapter = LiveResearchAdapter()
    evidence = []
    for source in _research_sources(page):
        source_id = str(source.get("id", "")).strip()
        url = str(source.get("url", "")).strip()
        notes = str(source.get("notes", "")).strip()
        print(f"RUOS RESEARCH FETCH: {source_id} {url}")
        evidence.append(adapter.fetch_source(source_id, url, manual_claims=(notes,) if notes else ()))
    snapshot = build_snapshot(page.slug, evidence)
    write_snapshot(snapshot, snapshot_path)
    print(f"RUOS RESEARCH SNAPSHOT: {snapshot_path}")
    print(f"RUOS RESEARCH SHA256: {snapshot.sha256}")
    return 0


def _run_discovery(page, args, project_root: Path) -> int:
    query = args.query.strip() or _primary_query(page)
    discovery = discover_search(
        create_provider(args.provider), query, market=args.market, language=args.language, count=args.count
    )
    output = project_root / args.output_root / f"{page.slug}.json"
    write_discovery(discovery, output)
    print(f"RUOS SEARCH DISCOVERY: {output}")
    print(f"RUOS SEARCH SHA256: {discovery.sha256}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    project_root = Path.cwd()
    spec_path = project_root / args.spec_root / f"{args.page}.json"
    try:
        page = load_page_spec(spec_path)
        if args.command == "research":
            return _run_research(page, project_root / args.snapshot_root / f"{page.slug}.json")
        if args.command == "discover":
            return _run_discovery(page, args, project_root)

        if args.require_search_discovery and not args.require_live_research:
            raise BuildRejected("Search discovery requires --require-live-research")
        context = BuildContext(
            project_root=project_root,
            output_root=project_root / args.output,
            strict=not args.no_strict,
            require_live_research=args.require_live_research,
            research_snapshot_root=project_root / args.snapshot_root,
            require_search_discovery=args.require_search_discovery,
            discovery_snapshot_root=project_root / args.discovery_root,
        )
        if args.require_live_research:
            result, verified, discovery = compile_production_page(
                page,
                context,
                max_age_days=args.research_max_age_days,
                discovery_max_age_days=args.discovery_max_age_days,
                discovery_minimum_results=args.discovery_minimum_results,
            )
            print(f"RUOS LIVE RESEARCH VERIFIED: {verified.source_count} sources snapshot={verified.snapshot_sha256}")
            if discovery is not None:
                print(f"RUOS SEARCH DISCOVERY VERIFIED: {discovery.result_count} results snapshot={discovery.sha256}")
        else:
            result = compile_page(page, context)
    except (SpecError, BuildRejected, LiveResearchError) as exc:
        label = "RESEARCH FAILED" if args.command in {"research", "discover"} else "BUILD REJECTED"
        print(f"RUOS {label}: {exc}", file=sys.stderr)
        return 2

    print(f"RUOS BUILD PASSED: {result.output_dir}")
    for path in result.files:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
