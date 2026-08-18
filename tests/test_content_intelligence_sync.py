from datetime import datetime, timezone

from ruos.content_intelligence_sync import sync_owned_instagram


class FakeClient:
    def list_media(self, max_items=200):
        return [
            {
                "id": "m1",
                "timestamp": "2026-08-18T00:00:00+00:00",
                "permalink": "https://example.test/m1",
                "media_type": "VIDEO",
                "media_product_type": "REELS",
                "caption": "test",
                "like_count": 20,
                "comments_count": 3,
            }
        ]

    def fetch_media_insights_resilient(self, media_id):
        assert media_id == "m1"
        return (
            {
                "views": 4000,
                "reach": 2000,
                "saved": 100,
                "shares": 40,
                "total_interactions": 300,
                "comments": 20,
                "likes": 200,
            },
            {},
        )


class FakeStore:
    def __init__(self):
        self.snapshot = None

    def upsert_project(self, project_id, project_name):
        self.project = (project_id, project_name)

    def ensure_source(self, *args, **kwargs):
        return 10

    def upsert_content_item(self, **kwargs):
        self.content = kwargs
        return 99

    def completed_snapshot_targets(self, content_item_id):
        assert content_item_id == 99
        return [1]

    def recent_metric_values(self, **kwargs):
        return [900, 1000, 1100, 1200, 1000]

    def insert_metric_snapshot(self, **kwargs):
        self.snapshot = kwargs
        return 123


def test_sync_owned_instagram_writes_due_snapshot_with_outlier_data():
    store = FakeStore()
    summary = sync_owned_instagram(
        project_id="red-umbrella",
        project_name="Red Umbrella",
        account_key="redumbrella",
        client=FakeClient(),
        store=store,
        now=datetime(2026, 8, 18, 6, 30, tzinfo=timezone.utc),
    )

    assert summary.media_seen == 1
    assert summary.snapshots_written == 1
    assert store.snapshot["age_hours"] == 6
    assert store.snapshot["derived"]["save_rate"] == 5.0
    assert store.snapshot["derived"]["outlier_ratio"] == 4.0
    assert store.snapshot["derived"]["outlier_class"] == "strong_outlier"
