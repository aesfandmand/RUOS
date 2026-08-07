from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


class PrebuildIntelligenceError(RuntimeError):
    pass


_REQUIRED_FIELDS = (
    "iranian_query_set",
    "serp_landscape",
    "search_intent_map",
    "funnel_role",
    "conversion_goal",
    "pillar",
    "cluster",
    "title_strategy",
    "h1",
    "heading_architecture",
    "discover_hook",
    "faq_and_paa_plan",
    "entity_graph",
    "schema_plan",
    "capability_evidence_plan",
    "internal_linking_plan",
    "related_blog_and_video_plan",
    "writer_profile",
    "iranian_editor_profile",
    "voice_constraints",
    "live_library_research_report",
    "selected_technology_stack",
    "aspirational_reference_translation",
    "motion_direction",
    "conversion_instrumentation_plan",
)


@dataclass(frozen=True)
class PrebuildGateReport:
    passed: bool
    missing: tuple[str, ...]
    invalid: tuple[str, ...]


def _nonempty(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return bool(value)
    return True


def validate_prebuild_dossier(dossier: Mapping[str, object]) -> PrebuildGateReport:
    missing = tuple(field for field in _REQUIRED_FIELDS if field not in dossier)
    invalid = tuple(field for field in _REQUIRED_FIELDS if field in dossier and not _nonempty(dossier[field]))

    market = str(dossier.get("target_market", "ir")).lower().strip()
    language = str(dossier.get("target_language", "fa")).lower().strip()
    if market != "ir":
        invalid += ("target_market",)
    if language != "fa":
        invalid += ("target_language",)

    queries = dossier.get("iranian_query_set")
    if isinstance(queries, Sequence) and not isinstance(queries, (str, bytes, bytearray)):
        if not any(any("\u0600" <= char <= "\u06ff" for char in str(item)) for item in queries):
            invalid += ("iranian_query_set:requires_persian_query",)

    return PrebuildGateReport(not missing and not invalid, missing, invalid)


def enforce_prebuild_dossier(dossier: Mapping[str, object]) -> None:
    report = validate_prebuild_dossier(dossier)
    if not report.passed:
        reasons = []
        if report.missing:
            reasons.append("missing=" + ",".join(report.missing))
        if report.invalid:
            reasons.append("invalid=" + ",".join(report.invalid))
        raise PrebuildIntelligenceError("Pre-build intelligence gate failed: " + "; ".join(reasons))
