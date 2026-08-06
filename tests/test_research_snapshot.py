from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ruos.live_research import LiveEvidence, LiveResearchError
from ruos.research_snapshot import build_snapshot, load_snapshot, write_snapshot


def _evidence(source_id: str, fetched_at: str) -> LiveEvidence:
    return LiveEvidence(
        source_id=source_id,
        requested_url=f"https://example.com/{source_id}",
        final_url=f"https://example.com/{source_id}",
        origin="live-web",
        fetched_at=fetched_at,
        status=200,
        content_type="text/html; charset=utf-8",
        content_sha256="a" * 64,
        byte_length=120,
        title=source_id,
        excerpt="Observed source text.",
        observations=("Observed fact",),
        inferences=("Explicit inference",),
        manual_claims=("Manual client preference",),
    )


def test_snapshot_is_sorted_deterministic_and_round_trips(tmp_path: Path) -> None:
    snapshot = build_snapshot(
        "structures",
        (
            _evidence("source-b", "2026-08-06T04:00:00Z"),
            _evidence("source-a", "2026-08-06T03:00:00Z"),
        ),
    )
    path = tmp_path / "structures.json"
    write_snapshot(snapshot, path)
    loaded = load_snapshot(path)

    assert [item.source_id for item in loaded.evidence] == ["source-a", "source-b"]
    assert loaded.created_at == "2026-08-06T04:00:00Z"
    assert loaded.payload() == snapshot.payload()
    assert loaded.sha256 == snapshot.sha256


def test_snapshot_rejects_duplicate_sources() -> None:
    with pytest.raises(LiveResearchError, match="duplicate source ids"):
        build_snapshot(
            "structures",
            (
                _evidence("same", "2026-08-06T03:00:00Z"),
                _evidence("same", "2026-08-06T04:00:00Z"),
            ),
        )


def test_snapshot_rejects_non_live_evidence() -> None:
    manual = replace(_evidence("manual", "2026-08-06T03:00:00Z"), origin="manual")
    with pytest.raises(LiveResearchError, match="only live-web evidence"):
        build_snapshot("structures", (manual,))


def test_snapshot_detects_tampering(tmp_path: Path) -> None:
    snapshot = build_snapshot("structures", (_evidence("source", "2026-08-06T03:00:00Z"),))
    path = tmp_path / "structures.json"
    write_snapshot(snapshot, path)
    text = path.read_text(encoding="utf-8").replace("Observed source text.", "Tampered source text.")
    path.write_text(text, encoding="utf-8")

    with pytest.raises(LiveResearchError, match="checksum"):
        load_snapshot(path)
