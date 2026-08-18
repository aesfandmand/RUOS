"""Executable owned-data sync for RUOS Content Intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from typing import Any

from .content_intelligence import classify_outlier, outlier_ratio
from .content_intelligence_instagram import InstagramConfig, InstagramOwnedInsightsClient
from .content_intelligence_snapshots import (
    derive_instagram_rates,
    due_snapshot_target,
    media_age_hours,
    view_velocity,
)
from .content_intelligence_store import PostgresContentIntelligenceStore


@dataclass(frozen=True)
class SyncSummary:
    media_seen: int = 0
    content_upserted: int = 0
    snapshots_written: int = 0
    snapshots_not_due: int = 0
    media_without_timestamp: int = 0
    insight_metric_errors: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "media_seen": self.media_seen,
            "content_upserted": self.content_upserted,
            "snapshots_written": self.snapshots_written,
            "snapshots_not_due": self.snapshots_not_due,
            "media_without_timestamp": self.media_without_timestamp,
            "insight_metric_errors": self.insight_metric_errors,
        }


def _parse_instagram_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def sync_owned_instagram(
    *,
    project_id: str,
    project_name: str,
    account_key: str,
    client: Any,
    store: Any,
    now: datetime | None = None,
    max_items: int = 200,
    baseline_window: int = 20,
) -> SyncSummary:
    """Synchronize owned Instagram media and write only due target snapshots."""

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    store.upsert_project(project_id, project_name)
    source_id = store.ensure_source(
        project_id,
        source_type="instagram_owned",
        source_key=account_key,
        data_class="owned",
        access_mode="official_api",
        weight=1.0,
        metadata={"separation_rule": "owned_insights_never_competitive"},
    )

    media_items = client.list_media(max_items=max_items)
    counts = {
        "media_seen": len(media_items),
        "content_upserted": 0,
        "snapshots_written": 0,
        "snapshots_not_due": 0,
        "media_without_timestamp": 0,
        "insight_metric_errors": 0,
    }

    for media in media_items:
        external_id = str(media.get("id") or "").strip()
        if not external_id:
            continue

        public_metrics = {
            key: media[key]
            for key in ("like_count", "comments_count")
            if isinstance(media.get(key), (int, float))
        }
        timestamp_value = media.get("timestamp")
        content_item_id = store.upsert_content_item(
            project_id=project_id,
            source_id=source_id,
            external_id=external_id,
            platform="instagram",
            canonical_url=media.get("permalink"),
            content_type=media.get("media_product_type") or media.get("media_type"),
            published_at=timestamp_value,
            caption=media.get("caption"),
            public_metrics=public_metrics,
            analysis={"data_class": "owned"},
        )
        counts["content_upserted"] += 1

        if not isinstance(timestamp_value, str) or not timestamp_value:
            counts["media_without_timestamp"] += 1
            continue

        published_at = _parse_instagram_timestamp(timestamp_value)
        actual_age_hours = media_age_hours(published_at, now)
        completed = store.completed_snapshot_targets(content_item_id)
        target = due_snapshot_target(actual_age_hours, completed)
        if target is None:
            counts["snapshots_not_due"] += 1
            continue

        metrics, metric_errors = client.fetch_media_insights_resilient(external_id)
        counts["insight_metric_errors"] += len(metric_errors)
        derived: dict[str, Any] = derive_instagram_rates(metrics)
        derived["actual_age_hours"] = round(actual_age_hours, 4)
        if metric_errors:
            derived["metric_errors"] = metric_errors

        views = metrics.get("views")
        if isinstance(views, (int, float)):
            if actual_age_hours > 0:
                derived["view_velocity"] = view_velocity(views, actual_age_hours)
            baseline = store.recent_metric_values(
                project_id=project_id,
                metric="views",
                age_hours=target,
                limit=baseline_window,
                exclude_content_item_id=content_item_id,
            )
            if baseline:
                ratio = outlier_ratio(float(views), baseline)
                derived["outlier_ratio"] = ratio
                derived["outlier_class"] = classify_outlier(ratio)
                derived["baseline_window"] = len(baseline)
                derived["baseline_age_hours"] = target

        store.insert_metric_snapshot(
            content_item_id=content_item_id,
            age_hours=target,
            metrics=metrics,
            derived=derived,
        )
        counts["snapshots_written"] += 1

    return SyncSummary(**counts)


def main() -> int:
    """Run one sync iteration from environment configuration."""

    project_id = os.getenv("CI_PROJECT_ID", "red-umbrella")
    project_name = os.getenv("CI_PROJECT_NAME", "Red Umbrella Advertising Agency")
    account_key = os.getenv("CI_INSTAGRAM_ACCOUNT_KEY", project_id)
    max_items = int(os.getenv("CI_INSTAGRAM_MAX_ITEMS", "200"))

    client = InstagramOwnedInsightsClient(InstagramConfig.from_env())
    store = PostgresContentIntelligenceStore()
    summary = sync_owned_instagram(
        project_id=project_id,
        project_name=project_name,
        account_key=account_key,
        client=client,
        store=store,
        max_items=max_items,
    )
    print(json.dumps(summary.as_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
