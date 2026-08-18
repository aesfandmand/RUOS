"""Validation and persistence for Content Intelligence research evidence."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Iterable, Mapping

from .research_collectors import ResearchEvidence, deduplicate

ALLOWED_SOURCE_CLASSES = {"owned", "competitive", "search", "community", "first_party"}
ALLOWED_CORROBORATION = {
    "single_source",
    "corroborated",
    "first_party_confirmed",
    "hypothesis_only",
    "locally_corroborated",
}


class ResearchEvidenceValidationError(ValueError):
    pass


@dataclass(frozen=True)
class IngestSummary:
    received: int
    deduplicated: int
    inserted: int
    skipped_existing: int


def _require_iso_datetime(value: str, field: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ResearchEvidenceValidationError(f"{field} must be ISO-8601 datetime") from exc


def validate_evidence(item: ResearchEvidence) -> ResearchEvidence:
    item.normalize()
    if not item.project_id.strip():
        raise ResearchEvidenceValidationError("project_id is required")
    if not item.source.strip():
        raise ResearchEvidenceValidationError("source is required")
    if item.source_class not in ALLOWED_SOURCE_CLASSES:
        raise ResearchEvidenceValidationError(f"invalid source_class: {item.source_class}")
    if not item.topic.strip():
        raise ResearchEvidenceValidationError("topic is required")
    if not 0 <= item.confidence <= 1:
        raise ResearchEvidenceValidationError("confidence must be between 0 and 1")
    if item.commercial_relevance is not None and not 0 <= item.commercial_relevance <= 10:
        raise ResearchEvidenceValidationError("commercial_relevance must be between 0 and 10")
    if item.corroboration_status not in ALLOWED_CORROBORATION:
        raise ResearchEvidenceValidationError(
            f"invalid corroboration_status: {item.corroboration_status}"
        )
    _require_iso_datetime(item.observed_at, "observed_at")
    if item.published_at is not None:
        _require_iso_datetime(item.published_at, "published_at")
    if item.outlier_ratio is not None and item.outlier_ratio < 0:
        raise ResearchEvidenceValidationError("outlier_ratio cannot be negative")
    return item


def evidence_metadata(item: ResearchEvidence) -> dict[str, Any]:
    payload = item.to_dict()
    payload["fingerprint"] = item.fingerprint
    return payload


def bulk_ingest(store: Any, items: Iterable[ResearchEvidence]) -> IngestSummary:
    received_items = list(items)
    unique_items = deduplicate(received_items)
    inserted = 0
    skipped = 0
    for item in unique_items:
        validate_evidence(item)
        created = store.upsert_research_evidence(
            project_id=item.project_id,
            fingerprint=item.fingerprint,
            source_type=item.source,
            source_class=item.source_class,
            topic=item.topic,
            title=item.title,
            query=item.query,
            excerpt=item.evidence_summary,
            url=item.canonical_url,
            observed_at=item.observed_at,
            published_at=item.published_at,
            confidence=item.confidence,
            commercial_relevance=item.commercial_relevance,
            corroboration_status=item.corroboration_status,
            tags=[value for value in (item.intent, item.funnel_stage, item.format, item.angle) if value],
            metadata=evidence_metadata(item),
        )
        if created:
            inserted += 1
        else:
            skipped += 1
    return IngestSummary(
        received=len(received_items),
        deduplicated=len(unique_items),
        inserted=inserted,
        skipped_existing=skipped,
    )
