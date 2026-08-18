"""CLI for validating and ingesting normalized research evidence JSONL."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .content_intelligence_store import PostgresContentIntelligenceStore
from .research_collectors import ResearchEvidence
from .research_ingest import bulk_ingest


def _load_jsonl(path: Path) -> list[ResearchEvidence]:
    items: list[ResearchEvidence] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
            items.append(ResearchEvidence(**payload))
        except Exception as exc:
            raise ValueError(f"invalid evidence at line {line_no}: {exc}") from exc
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest RUOS research evidence JSONL")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    store = PostgresContentIntelligenceStore()
    summary = bulk_ingest(store, _load_jsonl(args.path))
    print(json.dumps(asdict(summary), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
