from pathlib import Path

import pytest

from ruos.discovery_snapshot import load_discovery, write_discovery
from ruos.live_research import LiveResearchError
from ruos.search_discovery import SearchDiscovery, SearchResult


def _discovery() -> SearchDiscovery:
    return SearchDiscovery(
        provider="fake",
        query="سازه‌های تبلیغاتی",
        market="ir",
        language="fa",
        fetched_at="2026-08-06T05:00:00Z",
        results=(
            SearchResult(1, "نتیجه اول", "https://example.com/one", "شرح اول"),
            SearchResult(2, "نتیجه دوم", "https://example.com/two", "شرح دوم"),
        ),
    )


def test_discovery_snapshot_round_trips_and_preserves_checksum(tmp_path: Path) -> None:
    path = tmp_path / "structures.json"
    discovery = _discovery()
    write_discovery(discovery, path)
    loaded = load_discovery(path)

    assert loaded.payload() == discovery.payload()
    assert loaded.sha256 == discovery.sha256


def test_discovery_snapshot_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "structures.json"
    write_discovery(_discovery(), path)
    path.write_text(path.read_text(encoding="utf-8").replace("نتیجه اول", "نتیجه تغییرکرده"), encoding="utf-8")

    with pytest.raises(LiveResearchError, match="checksum"):
        load_discovery(path)


def test_discovery_snapshot_rejects_non_contiguous_ranks(tmp_path: Path) -> None:
    path = tmp_path / "structures.json"
    write_discovery(_discovery(), path)
    path.write_text(path.read_text(encoding="utf-8").replace('"rank": 2', '"rank": 3'), encoding="utf-8")

    with pytest.raises(LiveResearchError, match="contiguous"):
        load_discovery(path)
