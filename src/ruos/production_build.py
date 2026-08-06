from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .build_research_gate import require_verified_live_research
from .compiler import BuildRejected, compile_page
from .models import BuildContext, BuildResult, PageSpec
from .research_verifier import VerifiedResearchEvidence


class ProductionBuildError(BuildRejected):
    pass


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
    return require_verified_live_research(
        page,
        snapshot_path,
        max_age_days=max_age_days,
    )


def compile_production_page(
    page: PageSpec,
    context: BuildContext,
    *,
    max_age_days: int = 14,
) -> tuple[BuildResult, VerifiedResearchEvidence]:
    verified = verify_production_research(
        page,
        context,
        max_age_days=max_age_days,
    )
    result = compile_page(
        page,
        replace(context, strict=True, require_live_research=True),
    )
    return result, verified
