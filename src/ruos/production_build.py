from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from .build_research_gate import require_verified_live_research
from .compiler import BuildRejected, compile_page
from .discovery_snapshot import load_discovery
from .discovery_verifier import VerifiedSearchDiscovery, verify_discovery
from .models import BuildContext, BuildResult, PageSpec
from .research_snapshot import load_snapshot
from .research_verifier import VerifiedResearchEvidence


class ProductionBuildError(BuildRejected):
    pass


def _primary_query(page: PageSpec) -> str:
    query = page.metadata.get("query")
    if isinstance(query, dict):
        value = str(query.get("primary", "")).strip()
        if value:
            return value
    value = str(page.metadata.get("primary_query", "")).strip()
    if not value:
        raise ProductionBuildError("Production build requires a primary query")
    return value


def verify_production_research(
    page: PageSpec,
    context: BuildContext,
    *,
    max_age_days: int = 14,
) -> VerifiedResearchEvidence:
    if not context.require_live_research:
        raise ProductionBuildError("Production build requires live research")
    if context.research_snapshot_root is None:
        raise ProductionBuildError("Production build requires a snapshot root")
    snapshot_path = Path(context.research_snapshot_root) / f"{page.slug}.json"
    return require_verified_live_research(page, snapshot_path, max_age_days=max_age_days)


def verify_production_discovery(
    page: PageSpec,
    context: BuildContext,
    *,
    max_age_days: int = 7,
    minimum_results: int = 5,
) -> VerifiedSearchDiscovery:
    if not context.require_search_discovery:
        raise ProductionBuildError("Production build requires search discovery")
    if context.discovery_snapshot_root is None:
        raise ProductionBuildError("Production build requires a discovery snapshot root")
    snapshot_path = Path(context.discovery_snapshot_root) / f"{page.slug}.json"
    discovery = load_discovery(snapshot_path)
    market = str(page.metadata.get("market", "ir")).strip().lower()
    if market == "iran":
        market = "ir"
    return verify_discovery(
        discovery,
        expected_query=_primary_query(page),
        expected_market=market,
        expected_language=page.lang,
        max_age=timedelta(days=max_age_days),
        minimum_results=minimum_results,
    )


def _page_with_verified_inputs(
    page: PageSpec,
    context: BuildContext,
    verified_research: VerifiedResearchEvidence,
    verified_discovery: VerifiedSearchDiscovery | None,
) -> PageSpec:
    if context.research_snapshot_root is None:
        raise ProductionBuildError("Production build requires a snapshot root")
    snapshot_path = Path(context.research_snapshot_root) / f"{page.slug}.json"
    snapshot = load_snapshot(snapshot_path)
    if snapshot.sha256 != verified_research.snapshot_sha256:
        raise ProductionBuildError("Verified research snapshot changed before compilation")

    research_provenance: dict[str, object] = {
        **verified_research.payload(),
        "evidence": [item.payload() for item in snapshot.evidence],
    }
    metadata = dict(page.metadata)

    if verified_discovery is not None:
        if context.discovery_snapshot_root is None:
            raise ProductionBuildError("Production build requires a discovery snapshot root")
        discovery_path = Path(context.discovery_snapshot_root) / f"{page.slug}.json"
        discovery = load_discovery(discovery_path)
        if discovery.sha256 != verified_discovery.sha256:
            raise ProductionBuildError("Verified search discovery changed before compilation")
        discovery_provenance = {
            **verified_discovery.payload(),
            "results": [item.payload() for item in discovery.results],
        }
        metadata["verified_search_discovery"] = discovery_provenance
        research_provenance["search_discovery"] = discovery_provenance
        research_provenance["status"] = "verified-live-with-search-discovery"

    metadata["verified_live_research"] = research_provenance
    return replace(page, metadata=metadata)


def compile_production_page(
    page: PageSpec,
    context: BuildContext,
    *,
    max_age_days: int = 14,
    discovery_max_age_days: int = 7,
    discovery_minimum_results: int = 5,
) -> tuple[BuildResult, VerifiedResearchEvidence, VerifiedSearchDiscovery | None]:
    verified_research = verify_production_research(page, context, max_age_days=max_age_days)
    verified_discovery = None
    if context.require_search_discovery:
        verified_discovery = verify_production_discovery(
            page,
            context,
            max_age_days=discovery_max_age_days,
            minimum_results=discovery_minimum_results,
        )
    production_page = _page_with_verified_inputs(page, context, verified_research, verified_discovery)
    result = compile_page(
        production_page,
        replace(context, strict=True, require_live_research=True),
    )
    return result, verified_research, verified_discovery
