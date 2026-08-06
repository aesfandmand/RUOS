from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from ruos.build_research_gate import require_verified_live_research
from ruos.live_research import LiveEvidence, LiveResearchError
from ruos.research_snapshot import build_snapshot, write_snapshot
from ruos.spec_loader import load_page_spec


def _evidence(source: dict[str, object], fetched_at: str) -> LiveEvidence:
    return LiveEvidence(
        source_id=str(source["id"]),
        requested_url=str(source["url"]),
        final_url=str(source["url"]),
        origin="live-web",
        fetched_at=fetched_at,
        status=200,
        content_type="text/html; charset=utf-8",
        content_sha256="a" * 64,
        byte_length=256,
        title=str(source["title"]),
        excerpt="Verified live source content.",
        observations=("Observed content",),
        inferences=(),
        manual_claims=(),
    )


def test_live_research_gate_rejects_missing_snapshot(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    with pytest.raises(LiveResearchError, match="Run 'ruos research structures' first"):
        require_verified_live_research(page, tmp_path / "structures.json")


def test_live_research_gate_accepts_complete_fresh_snapshot(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    sources = page.metadata["research"]["sources"]
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    snapshot = build_snapshot(page.slug, (_evidence(source, fetched_at) for source in sources))
    path = tmp_path / "structures.json"
    write_snapshot(snapshot, path)

    verified = require_verified_live_research(page, path)

    assert verified.page_slug == "structures"
    assert verified.source_count == len(sources)
    assert verified.snapshot_sha256 == snapshot.sha256
    assert verified.payload()["status"] == "verified-live"


def test_live_research_gate_rejects_invalid_max_age(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    with pytest.raises(LiveResearchError, match="at least one day"):
        require_verified_live_research(page, tmp_path / "structures.json", max_age_days=0)
