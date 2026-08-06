from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ruos.live_research import (
    FetchPolicy,
    LiveResearchAdapter,
    LiveResearchError,
    TransportResponse,
)


class FakeTransport:
    def __init__(self, response: TransportResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, FetchPolicy]] = []

    def fetch(self, url: str, policy: FetchPolicy) -> TransportResponse:
        self.calls.append((url, policy))
        return self.response


def _adapter(body: bytes, *, status: int = 200, content_type: str = "text/html; charset=utf-8") -> LiveResearchAdapter:
    transport = FakeTransport(
        TransportResponse(
            requested_url="https://example.com/source",
            final_url="https://example.com/source",
            status=status,
            headers={"content-type": content_type},
            body=body,
        )
    )
    return LiveResearchAdapter(
        transport=transport,
        clock=lambda: datetime(2026, 8, 6, 4, 0, tzinfo=timezone.utc),
    )


def test_live_adapter_records_verifiable_provenance() -> None:
    adapter = _adapter(
        "<html><head><title>Reference page</title></head><body><main>Observed source content for comparison.</main></body></html>".encode()
    )
    evidence = adapter.fetch_source(
        "reference-1",
        "https://example.com/source",
        observations=("The page contains a comparison section.",),
        inferences=("The structure may support commercial investigation intent.",),
        manual_claims=("The client considers this reference visually strong.",),
    )

    assert evidence.origin == "live-web"
    assert evidence.fetched_at == "2026-08-06T04:00:00Z"
    assert evidence.status == 200
    assert evidence.title == "Reference page"
    assert "Observed source content" in evidence.excerpt
    assert len(evidence.content_sha256) == 64
    assert evidence.observations == ("The page contains a comparison section.",)
    assert evidence.inferences == ("The structure may support commercial investigation intent.",)
    assert evidence.manual_claims == ("The client considers this reference visually strong.",)


def test_live_evidence_is_deterministic_for_same_snapshot_and_clock() -> None:
    body = b'{"query":"structures","market":"iran"}'
    first = _adapter(body, content_type="application/json").fetch_source("query-data", "https://example.com/source")
    second = _adapter(body, content_type="application/json").fetch_source("query-data", "https://example.com/source")

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256


def test_adapter_rejects_non_success_response() -> None:
    adapter = _adapter(b"not found", status=404, content_type="text/plain")
    with pytest.raises(LiveResearchError, match="non-success status 404"):
        adapter.fetch_source("missing", "https://example.com/source")


def test_adapter_rejects_empty_extractable_evidence() -> None:
    adapter = _adapter(b"<html><script>only script</script></html>")
    with pytest.raises(LiveResearchError, match="did not yield extractable evidence"):
        adapter.fetch_source("empty", "https://example.com/source")


def test_adapter_requires_source_id() -> None:
    adapter = _adapter(b"useful text", content_type="text/plain")
    with pytest.raises(LiveResearchError, match="requires a source id"):
        adapter.fetch_source("  ", "https://example.com/source")
