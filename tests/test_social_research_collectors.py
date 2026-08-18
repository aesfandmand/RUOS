from ruos.social_research_collectors import (
    InstagramCompetitiveAdapter,
    LinkedInCompetitiveAdapter,
    TikTokCreativeAdapter,
)


def test_instagram_public_adapter_keeps_only_visible_metrics():
    item = InstagramCompetitiveAdapter.from_public_post(
        project_id="red-umbrella",
        topic="billboard",
        url="https://instagram.com/p/example/?utm_source=x",
        account="example",
        caption_summary="summary",
        visible_likes=10,
        visible_comments=2,
    )
    data = item.to_dict()
    assert data["visible_metrics"] == {"likes": 10, "comments": 2}
    assert "reach" not in data["visible_metrics"]
    assert "saves" not in data["visible_metrics"]
    assert data["canonical_url"] == "https://instagram.com/p/example"


def test_tiktok_adapter_does_not_invent_metrics():
    item = TikTokCreativeAdapter.from_creative(
        project_id="red-umbrella",
        topic="marketing",
        url="https://ads.tiktok.com/business/creativecenter/topads/example",
        title="Example",
        summary="Observed creative pattern",
    )
    assert item.to_dict()["visible_metrics"] == {}
    assert item.outlier_ratio is None


def test_linkedin_adapter_is_competitive_public_evidence():
    item = LinkedInCompetitiveAdapter.from_public_post(
        project_id="red-umbrella",
        topic="B2B marketing consulting",
        url="https://www.linkedin.com/feed/update/urn:li:activity:123",
        author="Example Author",
        summary="Observed professional discussion",
        visible_reactions=20,
    )
    data = item.to_dict()
    assert data["source"] == "linkedin"
    assert data["source_class"] == "competitive"
    assert data["visible_metrics"] == {"reactions": 20}
