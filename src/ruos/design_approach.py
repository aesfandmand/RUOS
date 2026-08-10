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

_STRUCTURE_DETAIL_V1 = DesignApproach(
    id="structure-detail-v1",
    name="Structure Detail product page (hero + registry-sourced spec sheet)",
    block_sequence=("structure-hero", "structure-specs", "faq-section-final", "review-gate"),
    source_reference="blocks/structure-hero, blocks/structure-specs, blocks/structure-gallery, "
                      "blocks/structure-related, blocks/structure-services — new blocks built on "
                      "the V16 design tokens (not extracted from a V16 selector), spec/photo/"
                      "cross-reference/cross-sell/FAQ data pulled live from "
                      "structure-page-registry-v2.1.yaml, media/structures/ (real Didanshow "
                      "installation photography), the service registry and the persona registry "
                      "via structure_detail_spec.py",
    note="block_sequence is the fixed spine every Structure Detail page carries: hero, spec "
         "sheet, FAQ, review gate. structure_detail_spec.build_structure_detail_spec also "
         "inserts up to three conditional blocks between the spec sheet and the FAQ — "
         "'structure-gallery' (a 3D-coverflow carousel of the structure's own real installation "
         "photos, when media/structures/<id>/ has at least two after reserving one for the hero "
         "photo), 'structure-related' (other real structures in the same family) and "
         "'structure-services' (real cross-sell services curated per family) — but only when "
         "the registry/media actually has at least two real items for that structure; a "
         "structure with fewer never gets a padded, fabricated version of that section. Only "
         "structures whose registry record has at least three real attributes (family, context, "
         "whose registry record has at least three real attributes (family, context, "
         "orientation, dimensions, face_count, mounting) can build a spec sheet at all; see "
         "structure_detail_spec.StructureDetailSpecError for the ones that can't yet.",
)

# Page Type -> DesignApproach.id. Every Page Type not listed here has no
# owner-approved reference yet and must be reported as NOT_YET_DESIGNED,
# never guessed.
_PAGE_TYPE_APPROACH: dict[str, str] = {
    "INVESTMENT_HUB": _SALES_LANDING_V16.id,
    "STRUCTURE_DETAIL": _STRUCTURE_DETAIL_V1.id,
}

_CATALOG: dict[str, DesignApproach] = {
    _SALES_LANDING_V16.id: _SALES_LANDING_V16,
    _STRUCTURE_DETAIL_V1.id: _STRUCTURE_DETAIL_V1,
}


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
