from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .competitor_page_research import CompetitorPageResearch
from .live_research import LiveEvidence, LiveResearchError


@dataclass(frozen=True)
class CompetitorEvidenceSnapshot:
    page_slug: str
    discovery_sha256: str
    evidence: tuple[LiveEvidence, ...]

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "discovery_sha256": self.discovery_sha256,
            "evidence": [item.payload() for item in self.evidence],
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def envelope(self) -> dict[str, object]:
        return {**self.payload(), "sha256": self.sha256}


def build_competitor_snapshot(page_slug: str, research: CompetitorPageResearch) -> CompetitorEvidenceSnapshot:
    slug = page_slug.strip()
    if not slug:
        raise LiveResearchError("Competitor evidence snapshot requires a page slug")
    if len(research.discovery_sha256) != 64:
        raise LiveResearchError("Competitor evidence snapshot requires a discovery SHA-256")
    if not research.evidence:
        raise LiveResearchError("Competitor evidence snapshot requires fetched page evidence")
    ranks: list[int] = []
    for item in research.evidence:
        if item.origin != "live-web":
            raise LiveResearchError("Competitor evidence snapshot accepts only live-web evidence")
        try:
            ranks.append(int(item.source_id.rsplit(":", 1)[-1]))
        except ValueError as exc:
            raise LiveResearchError("Competitor evidence source id must end with its search rank") from exc
    if ranks != sorted(ranks) or len(ranks) != len(set(ranks)):
        raise LiveResearchError("Competitor evidence ranks must be unique and ordered")
    return CompetitorEvidenceSnapshot(slug, research.discovery_sha256, research.evidence)


def write_competitor_snapshot(snapshot: CompetitorEvidenceSnapshot, path: Path) -> None:
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


def load_competitor_snapshot(path: Path) -> CompetitorEvidenceSnapshot:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LiveResearchError(f"Unable to read competitor evidence snapshot: {path}") from exc
    if not isinstance(raw, dict):
        raise LiveResearchError("Competitor evidence snapshot root must be an object")
    rows = raw.get("evidence")
    if not isinstance(rows, list) or not rows:
        raise LiveResearchError("Competitor evidence snapshot requires evidence")
    evidence: list[LiveEvidence] = []
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            raise LiveResearchError(f"Competitor evidence #{index} must be an object")
        try:
            evidence.append(LiveEvidence(
                source_id=str(item["source_id"]), requested_url=str(item["requested_url"]),
                final_url=str(item["final_url"]), origin=str(item["origin"]),
                fetched_at=str(item["fetched_at"]), status=int(item["status"]),
                content_type=str(item["content_type"]), content_sha256=str(item["content_sha256"]),
                byte_length=int(item["byte_length"]), title=str(item.get("title", "")),
                excerpt=str(item["excerpt"]), observations=tuple(str(v) for v in item.get("observations", [])),
                inferences=tuple(str(v) for v in item.get("inferences", [])),
                manual_claims=tuple(str(v) for v in item.get("manual_claims", [])),
            ))
        except (KeyError, TypeError, ValueError) as exc:
            raise LiveResearchError(f"Competitor evidence #{index} is invalid") from exc
    research = CompetitorPageResearch(str(raw.get("discovery_sha256", "")), tuple(evidence))
    snapshot = build_competitor_snapshot(str(raw.get("page_slug", "")), research)
    if str(raw.get("sha256", "")) != snapshot.sha256:
        raise LiveResearchError("Competitor evidence snapshot checksum does not match its contents")
    return snapshot
