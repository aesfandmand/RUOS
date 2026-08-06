from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from ruos.live_research import LiveEvidence, LiveResearchError
from ruos.research_snapshot import build_snapshot
from ruos.research_studio import ResearchSource
from ruos.research_verifier import verify_snapshot


def _source(source_id: str) -> ResearchSource:
    return ResearchSource(
        id=source_id,
        kind="design-reference",
        title=source_id,
        url=f"https://example.com/{source_id}",
        market="global",
        language="en",
        notes="Traceable source",
    )


def _evidence(source_id: str, fetched_at: str = "2026-08-06T04:00:00Z") -> LiveEvidence:
    return LiveEvidence(
        source_id=source_id,
        requested_url=f"https://example.com/{source_id}",
        final_url=f"https://example.com/{source_id}",
        origin="live-web",
        fetched_at=fetched_at,
        status=200,
        content_type="text/html",
        content_sha256="a" * 64,
        byte_length=100,
        title=source_id,
        excerpt="Observed live source content.",
        observations=(),
        inferences=(),
        manual_claims=(),
    )


def test_verifier_accepts_complete_fresh_snapshot() -> None:
    sources = (_source("a"), _source("b"))
    snapshot = build_snapshot("structures", (_evidence("b"), _evidence("a")))
    verified = verify_snapshot(
        "structures",
        sources,
        snapshot,
        now=datetime(2026, 8, 6, 10, 0, tzinfo=timezone.utc),
    )
    assert verified.covered_source_ids == ("a", "b")
    assert verified.source_count == 2
    assert verified.freshness_hours == 6
    assert verified.payload()["status"] == "verified-live"


def test_verifier_rejects_missing_source() -> None:
    snapshot = build_snapshot("structures", (_evidence("a"),))
    with pytest.raises(LiveResearchError, match="missing configured sources: b"):
        verify_snapshot("structures", (_source("a"), _source("b")), snapshot)


def test_verifier_rejects_changed_url() -> None:
    snapshot = build_snapshot("structures", (_evidence("a"),))
    changed = replace(_source("a"), url="https://example.com/changed")
    with pytest.raises(LiveResearchError, match="URL changed"):
        verify_snapshot("structures", (changed,), snapshot)


def test_verifier_rejects_stale_snapshot() -> None:
    snapshot = build_snapshot("structures", (_evidence("a", "2026-07-01T04:00:00Z"),))
    with pytest.raises(LiveResearchError, match="stale"):
        verify_snapshot(
            "structures",
            (_source("a"),),
            snapshot,
            now=datetime(2026, 8, 6, 4, 0, tzinfo=timezone.utc),
            max_age=timedelta(days=14),
        )
