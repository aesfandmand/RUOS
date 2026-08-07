from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from .build_research_gate import require_verified_live_research
from .compiler import BuildRejected, compile_page
from .competitor_snapshot import load_competitor_snapshot
from .competitor_verifier import VerifiedCompetitorEvidence, verify_competitor_evidence
from .discovery_snapshot import load_discovery
from .discovery_verifier import VerifiedSearchDiscovery, verify_discovery
from .models import BuildContext, BuildResult, PageSpec
from .prebuild_intelligence import PrebuildIntelligenceError, enforce_prebuild_dossier
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


def _require_prebuild_intelligence(page: PageSpec) -> None:
    dossier = page.metadata.get("prebuild_intelligence")
    if not isinstance(dossier, dict):
        raise ProductionBuildError("Production build requires metadata.prebuild_intelligence")
    enriched = dict(dossier)
    enriched.setdefault("target_market", page.metadata.get("market", "ir"))
    enriched.setdefault("target_language", page.lang)
    try:
        enforce_prebuild_dossier(enriched)
    except PrebuildIntelligenceError as exc:
        raise ProductionBuildError(str(exc)) from exc


def verify_production_research(page: PageSpec, context: BuildContext, *, max_age_days: int = 14) -> VerifiedResearchEvidence:
    if not context.require_live_research:
        raise ProductionBuildError("Production build requires live research")
    if context.research_snapshot_root is None:
        raise ProductionBuildError("Production build requires a snapshot root")
    return require_verified_live_research(page, Path(context.research_snapshot_root) / f"{page.slug}.json", max_age_days=max_age_days)


def verify_production_discovery(page: PageSpec, context: BuildContext, *, max_age_days: int = 7, minimum_results: int = 5) -> VerifiedSearchDiscovery:
    if not context.require_search_discovery:
        raise ProductionBuildError("Production build requires search discovery")
    if context.discovery_snapshot_root is None:
        raise ProductionBuildError("Production build requires a discovery snapshot root")
    discovery = load_discovery(Path(context.discovery_snapshot_root) / f"{page.slug}.json")
    market = str(page.metadata.get("market", "ir")).strip().lower()
    if market == "iran": market = "ir"
    return verify_discovery(discovery, expected_query=_primary_query(page), expected_market=market, expected_language=page.lang, max_age=timedelta(days=max_age_days), minimum_results=minimum_results)


def verify_production_competitors(page: PageSpec, context: BuildContext, *, max_age_days: int = 7, minimum_pages: int = 3) -> VerifiedCompetitorEvidence:
    if not context.require_competitor_evidence:
        raise ProductionBuildError("Production build requires competitor page evidence")
    if context.competitor_snapshot_root is None or context.discovery_snapshot_root is None:
        raise ProductionBuildError("Production build requires competitor and discovery snapshot roots")
    discovery = load_discovery(Path(context.discovery_snapshot_root) / f"{page.slug}.json")
    snapshot = load_competitor_snapshot(Path(context.competitor_snapshot_root) / f"{page.slug}.json")
    return verify_competitor_evidence(snapshot, discovery, expected_page_slug=page.slug, max_age=timedelta(days=max_age_days), minimum_pages=minimum_pages)


def _page_with_verified_inputs(page: PageSpec, context: BuildContext, verified_research: VerifiedResearchEvidence, verified_discovery: VerifiedSearchDiscovery | None, verified_competitors: VerifiedCompetitorEvidence | None) -> PageSpec:
    if context.research_snapshot_root is None:
        raise ProductionBuildError("Production build requires a snapshot root")
    snapshot = load_snapshot(Path(context.research_snapshot_root) / f"{page.slug}.json")
    if snapshot.sha256 != verified_research.snapshot_sha256:
        raise ProductionBuildError("Verified research snapshot changed before compilation")
    research_provenance: dict[str, object] = {**verified_research.payload(), "evidence": [item.payload() for item in snapshot.evidence]}
    metadata = dict(page.metadata)
    if verified_discovery is not None:
        if context.discovery_snapshot_root is None: raise ProductionBuildError("Production build requires a discovery snapshot root")
        discovery = load_discovery(Path(context.discovery_snapshot_root) / f"{page.slug}.json")
        if discovery.sha256 != verified_discovery.sha256: raise ProductionBuildError("Verified search discovery changed before compilation")
        discovery_provenance = {**verified_discovery.payload(), "results": [item.payload() for item in discovery.results]}
        metadata["verified_search_discovery"] = discovery_provenance; research_provenance["search_discovery"] = discovery_provenance; research_provenance["status"] = "verified-live-with-search-discovery"
    if verified_competitors is not None:
        if context.competitor_snapshot_root is None: raise ProductionBuildError("Production build requires a competitor snapshot root")
        competitor_snapshot = load_competitor_snapshot(Path(context.competitor_snapshot_root) / f"{page.slug}.json")
        if competitor_snapshot.sha256 != verified_competitors.snapshot_sha256: raise ProductionBuildError("Verified competitor evidence changed before compilation")
        competitor_provenance = {**verified_competitors.payload(), "evidence": [item.payload() for item in competitor_snapshot.evidence]}
        metadata["verified_competitor_evidence"] = competitor_provenance; research_provenance["competitor_page_evidence"] = competitor_provenance["evidence"]; research_provenance["competitor_evidence"] = competitor_provenance; research_provenance["status"] = "verified-live-with-search-and-competitors"
    metadata["verified_live_research"] = research_provenance
    return replace(page, metadata=metadata)


def compile_production_page(page: PageSpec, context: BuildContext, *, max_age_days: int = 14, discovery_max_age_days: int = 7, discovery_minimum_results: int = 5, competitor_max_age_days: int = 7, competitor_minimum_pages: int = 3) -> tuple[BuildResult, VerifiedResearchEvidence, VerifiedSearchDiscovery | None]:
    _require_prebuild_intelligence(page)
    if context.require_competitor_evidence and not context.require_search_discovery:
        raise ProductionBuildError("Competitor page evidence requires search discovery")
    verified_research = verify_production_research(page, context, max_age_days=max_age_days)
    verified_discovery = verify_production_discovery(page, context, max_age_days=discovery_max_age_days, minimum_results=discovery_minimum_results) if context.require_search_discovery else None
    verified_competitors = verify_production_competitors(page, context, max_age_days=competitor_max_age_days, minimum_pages=competitor_minimum_pages) if context.require_competitor_evidence else None
    production_page = _page_with_verified_inputs(page, context, verified_research, verified_discovery, verified_competitors)
    result = compile_page(production_page, replace(context, strict=True, require_live_research=True))
    return result, verified_research, verified_discovery
