from dataclasses import replace
from pathlib import Path

from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.research_studio import conduct_research
from ruos.spec_loader import load_page_spec


def test_verified_live_provenance_is_preserved_in_research_payload() -> None:
    page = load_page_spec(Path("pages/structures.json"))
    provenance = {
        "status": "verified-live",
        "snapshot_sha256": "a" * 64,
        "created_at": "2026-08-06T04:00:00Z",
        "source_count": 1,
        "covered_source_ids": ["source-one"],
        "freshness_hours": 2,
        "evidence": [
            {
                "source_id": "source-one",
                "origin": "live-web",
                "fetched_at": "2026-08-06T04:00:00Z",
                "content_sha256": "b" * 64,
                "observations": ["Observed source content"],
                "inferences": ["Explicit inference"],
                "manual_claims": ["Client preference"],
            }
        ],
    }
    metadata = dict(page.metadata)
    metadata["verified_live_research"] = provenance
    production_page = replace(page, metadata=metadata)
    intelligence = build_creative_intelligence(
        production_page,
        compose_content(production_page),
    )

    brief = conduct_research(production_page, intelligence)
    payload = brief.payload()

    assert brief.evidence_status == "verified-live"
    assert payload["provenance"]["snapshot_sha256"] == "a" * 64
    assert payload["provenance"]["evidence"][0]["origin"] == "live-web"
    assert payload["provenance"]["evidence"][0]["observations"] == [
        "Observed source content"
    ]
