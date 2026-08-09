"""Wire page selection, design-approach matching and composition into one call.

``generate_next`` is the one-command entrypoint the engine needs: it walks
the ranked build queue from ``page_selector`` and, for each candidate in
order, tries to take it all the way to a composed page. It stops at the
first candidate that actually composes, or reports every attempt it made
and why each one stopped where it did — never inventing a design or
content it does not have real, owner-approved provenance for.

Three ways a candidate can be blocked, in the order they are checked:

1. ``DESIGN_NOT_YET_DESIGNED`` — no owner-approved block sequence exists
   yet for this Page Type (see ``design_approach``).
2. ``CONTENT_NOT_YET_AUTHORED`` — a design approach matched, but no
   content spec (real slot data — copy, products, proof, images) has been
   authored for this page yet. This module never fabricates that content;
   authoring it is a separate, content-specific step.
3. ``COMPOSE_REJECTED`` — a spec exists and was rendered, but the
   composer rejected the sequence (e.g. the repeated card-grid rule).

Only a candidate that clears all three stages reaches ``GENERATED``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .architecture_registry import DEFAULT_REGISTRY_ROOT
from .block_composer import BlockCompositionError
from .block_library import BlockRenderError
from .block_page import BlockPageError, load_page_spec, render_page
from .block_registry import BlockRegistryError, load_library
from .design_approach import MATCHED, select_design_approach
from .page_selector import DEFAULT_PROJECT_ROOT, PageCandidate, select_candidates

DESIGN_NOT_YET_DESIGNED = "design_not_yet_designed"
CONTENT_NOT_YET_AUTHORED = "content_not_yet_authored"
COMPOSE_REJECTED = "compose_rejected"
GENERATED = "generated"


@dataclass(frozen=True)
class GenerateAttempt:
    candidate: PageCandidate
    stage: str
    reason: str


@dataclass(frozen=True)
class GenerateReport:
    attempts: tuple[GenerateAttempt, ...]
    generated_page: Any | None  # RenderedPage, when stage == GENERATED
    generated_library: Any | None  # BlockLibrary the page was rendered against


def generate_next(
    project_root: Path | None = None,
    registry_root: Path | None = None,
    spec_root: str = "pages/blocks",
    library_root: str = "blocks",
    output_root: str = "dist",
) -> GenerateReport:
    project_root = project_root or DEFAULT_PROJECT_ROOT
    registry_root = registry_root or DEFAULT_REGISTRY_ROOT
    candidates, _ = select_candidates(project_root, registry_root, output_root)

    attempts: list[GenerateAttempt] = []
    library = None

    for candidate in candidates:
        design = select_design_approach(candidate.page_type)
        if design.status != MATCHED:
            attempts.append(GenerateAttempt(candidate, DESIGN_NOT_YET_DESIGNED, design.reason))
            continue

        spec_path = project_root / spec_root / f"{candidate.slug}.json"
        if not spec_path.is_file():
            attempts.append(GenerateAttempt(
                candidate, CONTENT_NOT_YET_AUTHORED,
                f"design approach '{design.approach.id}' matched, but no authored content "
                f"spec exists yet at {spec_path}",
            ))
            continue

        if library is None:
            library = load_library(project_root / library_root)
        spec = load_page_spec(spec_path)
        try:
            page = render_page(spec, library)
        except (BlockCompositionError, BlockRenderError, BlockPageError, BlockRegistryError) as exc:
            attempts.append(GenerateAttempt(candidate, COMPOSE_REJECTED, str(exc)))
            continue

        attempts.append(GenerateAttempt(candidate, GENERATED, f"composed via {design.approach.id}"))
        return GenerateReport(tuple(attempts), page, library)

    return GenerateReport(tuple(attempts), None, None)
