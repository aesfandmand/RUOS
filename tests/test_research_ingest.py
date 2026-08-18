from ruos.research_collectors import ResearchEvidence
from ruos.research_ingest import bulk_ingest, validate_evidence


class FakeStore:
    def __init__(self):
        self.fingerprints = set()

    def upsert_research_evidence(self, **kwargs):
        fp = kwargs["fingerprint"]
        if fp in self.fingerprints:
            return False
        self.fingerprints.add(fp)
        return True


def test_bulk_ingest_deduplicates_and_is_idempotent():
    store = FakeStore()
    a = ResearchEvidence(
        project_id="red-umbrella",
        source="google_search",
        source_class="search",
        topic="تبلیغات محیطی",
        confidence=0.8,
        canonical_url="https://example.com/x?utm_source=test",
        title="A",
    )
    b = ResearchEvidence(
        project_id="red-umbrella",
        source="google_search",
        source_class="search",
        topic="تبلیغات محیطی",
        confidence=0.8,
        canonical_url="https://example.com/x",
        title="A",
    )
    first = bulk_ingest(store, [a, b])
    assert first.received == 2
    assert first.deduplicated == 1
    assert first.inserted == 1
    assert first.skipped_existing == 0

    second = bulk_ingest(store, [a])
    assert second.inserted == 0
    assert second.skipped_existing == 1


def test_validate_allows_null_published_at_and_no_outlier():
    item = ResearchEvidence(
        project_id="red-umbrella",
        source="reddit",
        source_class="community",
        topic="ad budget waste",
        confidence=0.7,
        published_at=None,
        outlier_ratio=None,
        corroboration_status="hypothesis_only",
    )
    assert validate_evidence(item) is item
