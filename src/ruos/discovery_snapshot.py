from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .live_research import LiveResearchError
from .search_discovery import SearchDiscovery, SearchResult


def write_discovery(discovery: SearchDiscovery, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**discovery.payload(), "sha256": discovery.sha256}
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def load_discovery(path: Path) -> SearchDiscovery:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveResearchError(f"Unable to read search discovery snapshot: {path}") from exc
    if not isinstance(raw, dict):
        raise LiveResearchError("Search discovery snapshot root must be an object")
    rows = raw.get("results", [])
    if not isinstance(rows, list) or not rows:
        raise LiveResearchError("Search discovery snapshot requires results")
    results: list[SearchResult] = []
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            raise LiveResearchError(f"Search result #{index} must be an object")
        try:
            result = SearchResult(
                rank=int(item["rank"]),
                title=str(item["title"]),
                url=str(item["url"]),
                snippet=str(item.get("snippet", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveResearchError(f"Search result #{index} is invalid") from exc
        if result.rank != index:
            raise LiveResearchError("Search discovery ranks must be contiguous and ordered")
        if not result.url.startswith("https://"):
            raise LiveResearchError("Search discovery results must use HTTPS")
        results.append(result)
    discovery = SearchDiscovery(
        provider=str(raw.get("provider", "")),
        query=str(raw.get("query", "")),
        market=str(raw.get("market", "")),
        language=str(raw.get("language", "")),
        fetched_at=str(raw.get("fetched_at", "")),
        results=tuple(results),
    )
    if not discovery.provider or not discovery.query or not discovery.fetched_at:
        raise LiveResearchError("Search discovery metadata is incomplete")
    if str(raw.get("sha256", "")) != discovery.sha256:
        raise LiveResearchError("Search discovery snapshot checksum does not match its contents")
    return discovery
