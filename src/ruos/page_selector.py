"""Decide which page the engine should build next.

Reads the materialized architecture registries (``architecture_registry``)
and ranks every page that is commercially active, indexable, and has a
*concrete* URL — never inventing one. A candidate is skipped, with a
stated reason, rather than guessed into existence:

- no concrete URL yet (still "PENDING" pending owner/audit decision)
- a URL template (``{slug}``) with no locked sub-registry to expand it
- the page has already been generated (output exists under the build
  output directory) — a page with an authored content spec but no
  output yet is still a candidate, and ranks just as high; an authored
  spec means it is ready to compose, not that it is done

Within the surviving candidates, pages already covered by a
``url_status`` the owner has locked (``KEEP``, ``KEEP_PATTERN``,
``CANONICAL_PATTERN``) outrank ones still waiting on URL audit
(``PENDING_AUDIT``) — an unconfirmed URL is still buildable, just lower
confidence than one the owner has already fixed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .architecture_registry import DEFAULT_REGISTRY_ROOT, EntityRecord, StructureRecord, load_entities, load_structures

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[2]

_LOCKED_URL_STATUSES = frozenset({"KEEP", "KEEP_PATTERN", "CANONICAL_PATTERN"})
_AUDIT_PENDING_URL_STATUSES = frozenset({"PENDING_AUDIT"})

_PAGE_LEVEL_RANK = {
    "ROOT": 0,
    "PILLAR/HUB": 1,
    "HUB": 1,
    "PILLAR": 2,
    "PILLAR/LANDING": 2,
    "LANDING": 3,
    "LANDING/RESOLVER": 3,
    "LANDING/ENTITY": 3,
    "ENTITY": 4,
    "SECTION/ENTITY": 5,
    "PAGE": 6,
}


@dataclass(frozen=True)
class PageCandidate:
    slug: str
    url: str
    source_id: str
    source_kind: str  # "entity" | "structure"
    page_type: str | None
    page_level: str | None
    priority_rank: tuple[int, int]
    reason: str


@dataclass(frozen=True)
class SkippedEntity:
    source_id: str
    name: str | None
    reason: str


def _slug_from_url(url: str) -> str:
    trimmed = url.strip("/")
    if not trimmed:
        return "home"
    return trimmed.rsplit("/", 1)[-1]


def _already_generated(project_root: Path, output_root: str, slug: str) -> bool:
    return (project_root / output_root / slug / "index.html").is_file()


def _is_eligible(entity: EntityRecord) -> str | None:
    """Return a skip reason, or None if the entity clears the commercial/indexing gate."""
    if entity.commercial_status != "ACTIVE":
        return f"commercial_status is '{entity.commercial_status}', not ACTIVE"
    if entity.publication_status != "INDEX":
        return f"publication_status is '{entity.publication_status}', not INDEX"
    if entity.indexability != "index":
        return f"indexability is '{entity.indexability}', not a plain index"
    return None


def _url_status_rank(url_status: str | None) -> int:
    if url_status in _LOCKED_URL_STATUSES:
        return 0
    if url_status in _AUDIT_PENDING_URL_STATUSES:
        return 1
    return 2


def _expand_structure_template(entity: EntityRecord, structures: tuple[StructureRecord, ...]) -> list[PageCandidate]:
    candidates = []
    for structure in structures:
        candidates.append(PageCandidate(
            slug=_slug_from_url(structure.url),
            url=structure.url,
            source_id=structure.id,
            source_kind="structure",
            page_type=entity.page_type,
            page_level="SECTION/ENTITY",
            priority_rank=(0, _PAGE_LEVEL_RANK.get("SECTION/ENTITY", 9)),
            reason=f"locked structure registry record ({structure.id}); expands entity template {entity.id}",
        ))
    return candidates


def select_candidates(
    project_root: Path | None = None,
    registry_root: Path | None = None,
    output_root: str = "dist",
) -> tuple[tuple[PageCandidate, ...], tuple[SkippedEntity, ...]]:
    """Rank every buildable page, best-first, and report why the rest were skipped."""
    project_root = project_root or DEFAULT_PROJECT_ROOT
    registry_root = registry_root or DEFAULT_REGISTRY_ROOT

    entities = load_entities(registry_root)
    structures = load_structures(registry_root)

    candidates: list[PageCandidate] = []
    skipped: list[SkippedEntity] = []

    for entity in entities:
        gate_reason = _is_eligible(entity)
        if gate_reason is not None:
            skipped.append(SkippedEntity(entity.id, entity.name_en or entity.name_fa, gate_reason))
            continue

        url = entity.url_candidate
        if not url or not url.startswith("/"):
            skipped.append(SkippedEntity(
                entity.id, entity.name_en or entity.name_fa,
                "no concrete URL yet — url_candidate is still 'PENDING' or unset",
            ))
            continue

        if "{" in url:
            if "structure-slug" in url:
                expanded = _expand_structure_template(entity, structures)
                candidates.extend(expanded)
            else:
                skipped.append(SkippedEntity(
                    entity.id, entity.name_en or entity.name_fa,
                    f"URL is a template ({url}) with no locked sub-registry to expand it yet",
                ))
            continue

        candidates.append(PageCandidate(
            slug=_slug_from_url(url),
            url=url,
            source_id=entity.id,
            source_kind="entity",
            page_type=entity.page_type,
            page_level=entity.page_level,
            priority_rank=(_url_status_rank(entity.url_status), _PAGE_LEVEL_RANK.get(entity.page_level, 9)),
            reason=f"entity registry record ({entity.id}), url_status={entity.url_status}",
        ))

    already_built = [c for c in candidates if _already_generated(project_root, output_root, c.slug)]
    for built in already_built:
        skipped.append(SkippedEntity(
            built.source_id, built.slug,
            f"already generated at {output_root}/{built.slug}/index.html",
        ))
    buildable = [c for c in candidates if not _already_generated(project_root, output_root, c.slug)]

    buildable.sort(key=lambda c: (c.priority_rank, c.source_id))
    return tuple(buildable), tuple(skipped)


def select_next(
    project_root: Path | None = None,
    registry_root: Path | None = None,
    output_root: str = "dist",
) -> PageCandidate | None:
    candidates, _ = select_candidates(project_root, registry_root, output_root)
    return candidates[0] if candidates else None
