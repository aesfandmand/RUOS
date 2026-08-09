"""Match a registry Page Type to a proven, owner-approved block sequence.

This is deliberately conservative. The block library currently has exactly
one full-page composition with real provenance: the sequence extracted
losslessly from the owner-approved V16 baseline (see ``blocks/README.md``
and ``LOCKED_BASELINE_V16.md``). Every other Page Type in the architecture
registry has no owner-approved visual reference yet, so this selector
reports that honestly (``not_yet_designed``) instead of reusing V16's
sequence, or inventing a new one, for content it was never designed for.
That would repeat the exact mistake the owner already rejected once:
building from a baseline the owner never approved.

Even the one proven sequence is not unconditionally buildable — its tail
currently repeats the card-grid layout across five sections, which
``block_composer`` correctly rejects (see
``test_reference_page_still_fails_the_shape_rules``). Callers must still
run the sequence through the composer and handle ``BlockCompositionError``;
``status`` here only reflects whether a design *reference* exists, not
whether it currently composes.
"""
from __future__ import annotations

from dataclasses import dataclass

MATCHED = "matched"
NOT_YET_DESIGNED = "not_yet_designed"


@dataclass(frozen=True)
class DesignApproach:
    id: str
    name: str
    block_sequence: tuple[str, ...]
    source_reference: str
    note: str


@dataclass(frozen=True)
class DesignApproachResult:
    page_type: str
    status: str  # MATCHED | NOT_YET_DESIGNED
    approach: DesignApproach | None
    reason: str


_SALES_LANDING_V16 = DesignApproach(
    id="sales-landing-v16",
    name="V16 sales / investment landing (owner-approved baseline)",
    block_sequence=(
        "hero-scroll-scene",
        "opportunity-section",
        "paths-scroll",
        "products-section",
        "contract-section",
        "assessment-section",
        "proof-section-final",
        "process-section-final",
        "media-section-final",
        "audience-section-final",
        "knowledge-section-final",
        "faq-section-final",
        "review-gate",
    ),
    source_reference="pages/blocks/urban-investment.json, extracted from "
                      "red-umbrella-website/services-urban-investment-final-v16.html",
    note="Composes structurally but its own tail repeats the card-grid layout "
         "across five sections (three of them adjacent), which violates the "
         "composer's anti-repetition rule. It needs owner-approved alternative "
         "layouts for contract/proof/media/audience/knowledge before it can "
         "actually compose — see blocks/README.md.",
)

# Page Type -> DesignApproach.id. Every Page Type not listed here has no
# owner-approved reference yet and must be reported as NOT_YET_DESIGNED,
# never guessed.
_PAGE_TYPE_APPROACH: dict[str, str] = {
    "INVESTMENT_HUB": _SALES_LANDING_V16.id,
}

_CATALOG: dict[str, DesignApproach] = {_SALES_LANDING_V16.id: _SALES_LANDING_V16}


def select_design_approach(page_type: str | None) -> DesignApproachResult:
    if not page_type:
        return DesignApproachResult(
            page_type=page_type or "",
            status=NOT_YET_DESIGNED,
            approach=None,
            reason="Registry record has no page_type; cannot select a design approach.",
        )

    approach_id = _PAGE_TYPE_APPROACH.get(page_type)
    if approach_id is None:
        return DesignApproachResult(
            page_type=page_type,
            status=NOT_YET_DESIGNED,
            approach=None,
            reason=f"No owner-approved design approach exists yet for page_type '{page_type}'. "
                   "Do not build until the owner supplies a real visual reference for it.",
        )

    approach = _CATALOG[approach_id]
    return DesignApproachResult(page_type=page_type, status=MATCHED, approach=approach, reason=approach.note)
