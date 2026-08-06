from __future__ import annotations

from dataclasses import dataclass

from .live_research import LiveEvidence, LiveResearchAdapter, LiveResearchError
from .search_discovery import SearchDiscovery


@dataclass(frozen=True)
class CompetitorPageResearch:
    discovery_sha256: str
    evidence: tuple[LiveEvidence, ...]

    def payload(self) -> dict[str, object]:
        return {
            "discovery_sha256": self.discovery_sha256,
            "evidence": [item.payload() for item in self.evidence],
        }


def fetch_competitor_pages(
    discovery: SearchDiscovery,
    adapter: LiveResearchAdapter,
    *,
    limit: int = 5,
    minimum_success: int = 3,
) -> CompetitorPageResearch:
    if limit < 1 or limit > 20:
        raise LiveResearchError("Competitor page research limit must be between 1 and 20")
    if minimum_success < 1 or minimum_success > limit:
        raise LiveResearchError("Competitor page research minimum_success must be between 1 and limit")

    evidence: list[LiveEvidence] = []
    failures: list[str] = []
    for result in discovery.results[:limit]:
        source_id = f"competitor-page:{result.rank}"
        try:
            evidence.append(
                adapter.fetch_source(
                    source_id,
                    result.url,
                    observations=(
                        f"Observed search rank {result.rank} for query: {discovery.query}",
                        f"Observed search title: {result.title}",
                    ),
                    manual_claims=(
                        f"Search snippet: {result.snippet}",
                    ) if result.snippet else (),
                )
            )
        except LiveResearchError as exc:
            failures.append(f"rank {result.rank}: {exc}")

    if len(evidence) < minimum_success:
        detail = "; ".join(failures) or "no usable pages"
        raise LiveResearchError(
            f"Competitor page research fetched {len(evidence)} pages; minimum is {minimum_success}: {detail}"
        )
    evidence.sort(key=lambda item: int(item.source_id.rsplit(":", 1)[-1]))
    return CompetitorPageResearch(discovery.sha256, tuple(evidence))
