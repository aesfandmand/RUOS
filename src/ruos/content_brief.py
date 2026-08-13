"""Real search + fetch, per structure, for the content drafting pipeline.

This is orchestration only — every piece of actual research (search
results, page fetches, provenance hashing, freshness checking) is the
existing, working machinery in ``search_discovery.py`` and
``live_research.py``; nothing here talks to the network directly. What this
module adds is: turning a real structure's registry data into real search
queries (never an invented one), fetching real page bodies long enough to
actually draft from (not just a short snippet — see
``live_research.LiveEvidence.full_text``), and writing the result as a
verified ``ResearchSnapshot`` plus a plain-language digest (``brief.md``)
that the drafting step — an assistant, same authorship model as
straboard.json — reads from.

Two search passes run by default: one against Iranian sources (market
``ir``, language ``fa``), one against international OOH-industry sources
(market ``us``, language ``en``) — both derived from the structure's own
real ``family``/``name_fa``, never a fabricated topic.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

from .architecture_registry import StructureRecord
from .live_research import LiveEvidence, LiveResearchAdapter, LiveResearchError
from .research_snapshot import ResearchSnapshot, build_snapshot, write_snapshot
from .research_studio import ResearchSource
from .research_verifier import VerifiedResearchEvidence, verify_snapshot
from .search_discovery import SearchDiscovery, SearchProvider, discover_search

# Query construction only — never presented on a page as a translation or a
# fact about the structure. A family with no entry here still gets a query,
# just using the Persian family name as-is for the international pass too.
_FAMILY_EN: dict[str, str] = {
    "بیلبورد": "billboard",
    "استرابورد": "strabord frame advertising structure",
    "لایت‌باکس": "outdoor light box advertising sign",
    "لایت‌برد": "light board advertising sign",
    "برایت‌بورد": "backlit advertising sign",
    "سازه سازمانی": "corporate banner stand",
    "لایت‌باکس ایندور": "indoor light box sign",
    "عرشه پل": "pedestrian bridge advertising panel",
}

_IRAN_LABEL = "iran"
_INTL_LABEL = "international"


@dataclass(frozen=True)
class QuerySpec:
    label: str
    query: str
    market: str
    language: str


def default_queries(structure: StructureRecord) -> tuple[QuerySpec, ...]:
    family_en = _FAMILY_EN.get(structure.family, structure.family)
    return (
        QuerySpec(_IRAN_LABEL, f"{structure.name_fa} تبلیغات محیطی مزایا و کاربرد", "ir", "fa"),
        QuerySpec(_INTL_LABEL, f"{family_en} outdoor advertising structure benefits", "us", "en"),
    )


@dataclass(frozen=True)
class ContentBrief:
    structure_id: str
    slug: str
    queries: tuple[QuerySpec, ...]
    discoveries: tuple[SearchDiscovery, ...]
    sources: tuple[ResearchSource, ...]
    snapshot: ResearchSnapshot
    verified: VerifiedResearchEvidence

    def payload(self) -> dict[str, object]:
        return {
            "structure_id": self.structure_id,
            "slug": self.slug,
            "queries": [
                {"label": q.label, "query": q.query, "market": q.market, "language": q.language}
                for q in self.queries
            ],
            "snapshot_sha256": self.snapshot.sha256,
            "verified": self.verified.payload(),
        }


def build_content_brief(
    structure: StructureRecord,
    provider: SearchProvider,
    *,
    queries: Sequence[QuerySpec] | None = None,
    results_per_query: int = 5,
    fetch_per_query: int = 3,
    adapter: LiveResearchAdapter | None = None,
    clock: Callable[[], datetime] | None = None,
    now: datetime | None = None,
) -> ContentBrief:
    """Run real discovery + real fetch for one structure and return a
    verified brief. `provider` and `adapter` are injected (never
    constructed here) so this is fully testable against a fake provider/
    fake transport — see tests/test_content_brief.py — and so the CLI, not
    this function, is the only place that reads an API key from the
    environment."""
    resolved_queries = tuple(queries) if queries else default_queries(structure)
    if not resolved_queries:
        raise LiveResearchError("A content brief needs at least one query")
    adapter = adapter or LiveResearchAdapter(clock=clock)
    slug = structure.url.strip("/").rsplit("/", 1)[-1]

    discoveries: list[SearchDiscovery] = []
    sources: list[ResearchSource] = []
    evidence: list[LiveEvidence] = []

    for spec in resolved_queries:
        discovery = discover_search(
            provider, spec.query, market=spec.market, language=spec.language,
            count=results_per_query, clock=clock,
        )
        discoveries.append(discovery)
        for result in discovery.results[:fetch_per_query]:
            source_id = f"{slug}-{spec.label}-{result.rank}"
            sources.append(ResearchSource(
                id=source_id, kind="web", title=result.title, url=result.url,
                market=spec.market, language=spec.language, notes=result.snippet,
            ))
            evidence.append(adapter.fetch_source(source_id, result.url))

    snapshot = build_snapshot(slug, evidence)
    verified = verify_snapshot(slug, sources, snapshot, now=now)
    return ContentBrief(
        structure_id=structure.id, slug=slug, queries=resolved_queries,
        discoveries=tuple(discoveries), sources=tuple(sources),
        snapshot=snapshot, verified=verified,
    )


def render_brief_markdown(brief: ContentBrief) -> str:
    """The document the drafting step (an assistant, reading this file) works
    from — one section per real fetched source: title, url, market/language,
    fetched-at, and enough of the real body text to actually quote or
    paraphrase with a citation back to `source_id`."""
    lines = [
        f"# محتوای تحقیقی: {brief.slug}",
        "",
        f"وضعیت: {brief.verified.source_count} منبع، تأییدشده در "
        f"{brief.verified.freshness_hours} ساعت پیش (snapshot "
        f"`{brief.snapshot.sha256[:12]}`).",
        "",
        "## کوئری‌های اجراشده",
        "",
    ]
    for spec in brief.queries:
        lines.append(f"- **{spec.label}** ({spec.market}/{spec.language}): {spec.query}")
    lines.append("")
    lines.append("## منابع")
    lines.append("")
    evidence_by_id = {item.source_id: item for item in brief.snapshot.evidence}
    for source in brief.sources:
        item = evidence_by_id[source.id]
        lines.append(f"### `{source.id}` — {source.title or item.title}")
        lines.append("")
        lines.append(f"- URL: {source.url}")
        lines.append(f"- بازار/زبان: {source.market}/{source.language}")
        lines.append(f"- زمان دریافت: {item.fetched_at}")
        lines.append(f"- content_sha256: `{item.content_sha256}`")
        lines.append("")
        lines.append(item.full_text or item.excerpt)
        lines.append("")
    return "\n".join(lines)


def write_content_brief(brief: ContentBrief, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = output_dir / "snapshot.json"
    write_snapshot(brief.snapshot, snapshot_path)
    brief_path = output_dir / "brief.md"
    brief_path.write_text(render_brief_markdown(brief), encoding="utf-8")
    (output_dir / "brief.json").write_text(
        json.dumps(brief.payload(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return snapshot_path, brief_path
