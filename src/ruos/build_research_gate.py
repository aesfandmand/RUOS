from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Mapping

from .live_research import LiveResearchError
from .models import PageSpec
from .research_snapshot import load_snapshot
from .research_studio import ResearchSource
from .research_verifier import VerifiedResearchEvidence, verify_snapshot


def _configured_sources(page: PageSpec) -> tuple[ResearchSource, ...]:
    research = page.metadata.get("research")
    if not isinstance(research, Mapping):
        raise LiveResearchError("Page metadata must include a research object")
    raw_sources = research.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise LiveResearchError("Page research must include configured sources")

    sources: list[ResearchSource] = []
    for index, item in enumerate(raw_sources, start=1):
        if not isinstance(item, Mapping):
            raise LiveResearchError(f"Research source #{index} must be an object")
        try:
            sources.append(
                ResearchSource(
                    id=str(item["id"]).strip(),
                    kind=str(item["kind"]).strip(),
                    title=str(item["title"]).strip(),
                    url=str(item["url"]).strip(),
                    market=str(item["market"]).strip(),
                    language=str(item["language"]).strip(),
                    notes=str(item["notes"]).strip(),
                )
            )
        except KeyError as exc:
            raise LiveResearchError(f"Research source #{index} is incomplete") from exc
    return tuple(sources)


def require_verified_live_research(
    page: PageSpec,
    snapshot_path: Path,
    *,
    max_age_days: int = 14,
) -> VerifiedResearchEvidence:
    if max_age_days < 1:
        raise LiveResearchError("Live research maximum age must be at least one day")
    if not snapshot_path.is_file():
        raise LiveResearchError(
            f"Required live research snapshot is missing: {snapshot_path}. Run 'ruos research {page.slug}' first."
        )
    snapshot = load_snapshot(snapshot_path)
    return verify_snapshot(
        page.slug,
        _configured_sources(page),
        snapshot,
        max_age=timedelta(days=max_age_days),
    )
