from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .live_research import LiveEvidence, LiveResearchError


@dataclass(frozen=True)
class ResearchSnapshot:
    page_slug: str
    created_at: str
    evidence: tuple[LiveEvidence, ...]

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "created_at": self.created_at,
            "evidence": [item.payload() for item in self.evidence],
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def envelope(self) -> dict[str, object]:
        return {**self.payload(), "sha256": self.sha256}


def build_snapshot(page_slug: str, evidence: Iterable[LiveEvidence]) -> ResearchSnapshot:
    items = tuple(sorted(evidence, key=lambda item: item.source_id))
    if not page_slug.strip():
        raise LiveResearchError("Research snapshot requires a page slug")
    if not items:
        raise LiveResearchError("Research snapshot requires at least one evidence item")
    source_ids = [item.source_id for item in items]
    if len(source_ids) != len(set(source_ids)):
        raise LiveResearchError("Research snapshot contains duplicate source ids")
    if any(item.origin != "live-web" for item in items):
        raise LiveResearchError("Research snapshot accepts only live-web evidence")
    newest = max(datetime.fromisoformat(item.fetched_at.replace("Z", "+00:00")) for item in items)
    created_at = newest.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return ResearchSnapshot(page_slug=page_slug.strip(), created_at=created_at, evidence=items)


def write_snapshot(snapshot: ResearchSnapshot, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(snapshot.envelope(), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
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


def load_snapshot(path: Path) -> ResearchSnapshot:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveResearchError(f"Unable to read research snapshot: {path}") from exc
    if not isinstance(raw, dict):
        raise LiveResearchError("Research snapshot root must be an object")
    evidence: list[LiveEvidence] = []
    for index, item in enumerate(raw.get("evidence", []), start=1):
        if not isinstance(item, dict):
            raise LiveResearchError(f"Research evidence #{index} must be an object")
        try:
            evidence.append(
                LiveEvidence(
                    source_id=str(item["source_id"]),
                    requested_url=str(item["requested_url"]),
                    final_url=str(item["final_url"]),
                    origin=str(item["origin"]),
                    fetched_at=str(item["fetched_at"]),
                    status=int(item["status"]),
                    content_type=str(item["content_type"]),
                    content_sha256=str(item["content_sha256"]),
                    byte_length=int(item["byte_length"]),
                    title=str(item.get("title", "")),
                    excerpt=str(item["excerpt"]),
                    observations=tuple(str(value) for value in item.get("observations", [])),
                    inferences=tuple(str(value) for value in item.get("inferences", [])),
                    manual_claims=tuple(str(value) for value in item.get("manual_claims", [])),
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveResearchError(f"Research evidence #{index} is invalid") from exc
    snapshot = build_snapshot(str(raw.get("page_slug", "")), evidence)
    expected_sha = str(raw.get("sha256", ""))
    if expected_sha != snapshot.sha256:
        raise LiveResearchError("Research snapshot checksum does not match its contents")
    if str(raw.get("created_at", "")) != snapshot.created_at:
        raise LiveResearchError("Research snapshot creation time is inconsistent with evidence")
    return snapshot
