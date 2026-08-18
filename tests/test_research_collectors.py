from ruos.research_collectors import ResearchEvidence, canonicalize_url, deduplicate


def test_canonicalize_url_removes_tracking_and_fragment():
    url = "https://Example.com/a/?utm_source=x&b=2#part"
    assert canonicalize_url(url) == "https://example.com/a?b=2"


def test_deduplicate_same_evidence():
    a = ResearchEvidence(project_id="red-umbrella", source="reddit", source_class="community", topic="billboard roi", title="Are billboards worth it?", canonical_url="https://reddit.com/x?utm_source=a", confidence=0.7)
    b = ResearchEvidence(project_id="red-umbrella", source="reddit", source_class="community", topic="billboard roi", title="Are billboards worth it?", canonical_url="https://reddit.com/x", confidence=0.7)
    assert len(deduplicate([a, b])) == 1


def test_no_outlier_is_invented():
    item = ResearchEvidence(project_id="red-umbrella", source="youtube", source_class="competitive", topic="OOH", confidence=0.6)
    assert item.outlier_ratio is None
