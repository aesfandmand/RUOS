from datetime import datetime, timezone
from pathlib import Path

import pytest

from ruos.competitor_page_research import CompetitorPageResearch
from ruos.competitor_snapshot import (
    build_competitor_snapshot,
    load_competitor_snapshot,
    write_competitor_snapshot,
)
from ruos.live_research import LiveEvidence, LiveResearchError


def _evidence(rank: int) -> LiveEvidence:
    return LiveEvidence(
        source_id=f"competitor-page:{rank}",
        requested_url=f"https://example{rank}.com/page",
        final_url=f"https://example{rank}.com/page",
        origin="live-web",
        fetched_at=datetime(2026, 8, 6, 6, rank, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
        status=200,
        content_type="text/html; charset=utf-8",
        content_sha256=str(rank) * 64,
        byte_length=1000 + rank,
        title=f"Page {rank}",
        excerpt=f"Observed competitor page {rank}",
        observations=(f"Observed search rank {rank}",),
        inferences=(),
        manual_claims=(),
    )


def test_competitor_snapshot_round_trip_and_checksum(tmp_path: Path) -> None:
    research = CompetitorPageResearch("a" * 64, (_evidence(1), _evidence(2), _evidence(3)))
    snapshot = build_competitor_snapshot("structures", research)
    path = tmp_path / "structures.json"
    write_competitor_snapshot(snapshot, path)
    loaded = load_competitor_snapshot(path)

    assert loaded == snapshot
    assert len(loaded.sha256) == 64
    assert loaded.discovery_sha256 == "a" * 64
    assert [item.source_id for item in loaded.evidence] == [
        "competitor-page:1",
        "competitor-page:2",
        "competitor-page:3",
    ]


def test_competitor_snapshot_rejects_tampering(tmp_path: Path) -> None:
    snapshot = build_competitor_snapshot(
        "structures", CompetitorPageResearch("a" * 64, (_evidence(1),))
    )
    path = tmp_path / "structures.json"
    write_competitor_snapshot(snapshot, path)
    text = path.read_text(encoding="utf-8").replace("Observed competitor page 1", "tampered")
    path.write_text(text, encoding="utf-8")

    with pytest.raises(LiveResearchError, match="checksum"):
        load_competitor_snapshot(path)


def test_competitor_snapshot_rejects_unordered_or_duplicate_ranks() -> None:
    with pytest.raises(LiveResearchError, match="unique and ordered"):
        build_competitor_snapshot(
            "structures",
            CompetitorPageResearch("a" * 64, (_evidence(2), _evidence(1))),
        )
