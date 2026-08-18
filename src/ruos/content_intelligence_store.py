"""Optional PostgreSQL/Supabase storage adapter for Content Intelligence.

The module imports psycopg lazily. Core RUOS remains dependency-free; projects that
want persistent Content Intelligence data can install the optional ``content-intel``
extra and provide CI_DATABASE_URL at runtime.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from typing import Any, Iterator, Mapping


class ContentIntelligenceStoreError(RuntimeError):
    pass


def database_url_from_env() -> str:
    value = os.getenv("CI_DATABASE_URL")
    if not value:
        raise ContentIntelligenceStoreError("CI_DATABASE_URL is not configured")
    return value


def _psycopg():
    try:
        import psycopg  # type: ignore
    except ImportError as exc:
        raise ContentIntelligenceStoreError(
            "psycopg is required for database persistence; install ruos-engine[content-intel]"
        ) from exc
    return psycopg


class PostgresContentIntelligenceStore:
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or database_url_from_env()

    @contextmanager
    def connection(self) -> Iterator[Any]:
        psycopg = _psycopg()
        with psycopg.connect(self.database_url) as conn:
            yield conn

    def upsert_project(
        self,
        project_id: str,
        name: str,
        *,
        language: str = "fa",
        geography: Mapping[str, Any] | None = None,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into ci_projects (id, name, language, geography, config)
                values (%s, %s, %s, %s::jsonb, %s::jsonb)
                on conflict (id) do update set
                  name = excluded.name,
                  language = excluded.language,
                  geography = excluded.geography,
                  config = excluded.config,
                  updated_at = now()
                """,
                (
                    project_id,
                    name,
                    language,
                    json.dumps(dict(geography or {})),
                    json.dumps(dict(config or {})),
                ),
            )

    def ensure_source(
        self,
        project_id: str,
        *,
        source_type: str,
        source_key: str,
        data_class: str,
        access_mode: str,
        weight: float = 1.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> int:
        if data_class not in {"owned", "competitive", "public", "first_party"}:
            raise ValueError(f"invalid data_class: {data_class}")
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select id from ci_sources
                where project_id = %s and source_type = %s and source_key = %s
                order by id asc limit 1
                """,
                (project_id, source_type, source_key),
            )
            row = cur.fetchone()
            if row:
                return int(row[0])
            cur.execute(
                """
                insert into ci_sources
                  (project_id, source_type, source_key, data_class, access_mode, weight, metadata)
                values (%s, %s, %s, %s, %s, %s, %s::jsonb)
                returning id
                """,
                (
                    project_id,
                    source_type,
                    source_key,
                    data_class,
                    access_mode,
                    weight,
                    json.dumps(dict(metadata or {})),
                ),
            )
            return int(cur.fetchone()[0])

    def upsert_content_item(
        self,
        *,
        project_id: str,
        source_id: int,
        external_id: str,
        platform: str,
        canonical_url: str | None = None,
        content_type: str | None = None,
        published_at: str | None = None,
        caption: str | None = None,
        public_metrics: Mapping[str, Any] | None = None,
        analysis: Mapping[str, Any] | None = None,
    ) -> int:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into ci_content_items
                  (project_id, source_id, external_id, platform, canonical_url, content_type,
                   published_at, caption, public_metrics, analysis)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
                on conflict (project_id, platform, external_id) do update set
                  source_id = excluded.source_id,
                  canonical_url = excluded.canonical_url,
                  content_type = excluded.content_type,
                  published_at = excluded.published_at,
                  caption = excluded.caption,
                  public_metrics = excluded.public_metrics,
                  analysis = ci_content_items.analysis || excluded.analysis
                returning id
                """,
                (
                    project_id,
                    source_id,
                    external_id,
                    platform,
                    canonical_url,
                    content_type,
                    published_at,
                    caption,
                    json.dumps(dict(public_metrics or {})),
                    json.dumps(dict(analysis or {})),
                ),
            )
            return int(cur.fetchone()[0])

    def completed_snapshot_targets(self, content_item_id: int) -> list[int]:
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select distinct age_hours
                from ci_metric_snapshots
                where content_item_id = %s and age_hours is not null
                order by age_hours asc
                """,
                (content_item_id,),
            )
            return [int(row[0]) for row in cur.fetchall()]

    def insert_metric_snapshot(
        self,
        *,
        content_item_id: int,
        age_hours: int,
        metrics: Mapping[str, Any],
        derived: Mapping[str, Any] | None = None,
    ) -> int:
        """Insert a target snapshot once; repeated runners are idempotent per target."""

        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                select id from ci_metric_snapshots
                where content_item_id = %s and age_hours = %s
                order by id asc limit 1
                """,
                (content_item_id, age_hours),
            )
            existing = cur.fetchone()
            if existing:
                return int(existing[0])
            cur.execute(
                """
                insert into ci_metric_snapshots (content_item_id, age_hours, metrics, derived)
                values (%s, %s, %s::jsonb, %s::jsonb)
                returning id
                """,
                (
                    content_item_id,
                    age_hours,
                    json.dumps(dict(metrics)),
                    json.dumps(dict(derived or {})),
                ),
            )
            return int(cur.fetchone()[0])

    def recent_metric_values(
        self,
        *,
        project_id: str,
        metric: str,
        age_hours: int,
        limit: int = 20,
        exclude_content_item_id: int | None = None,
    ) -> list[float]:
        """Return baseline values from the same target age across recent content.

        A 6-hour Reel must be compared with other 6-hour snapshots, not with their
        7-day or 30-day totals. Matching checkpoint age is therefore mandatory.
        """

        if limit < 1:
            raise ValueError("limit must be >= 1")
        if age_hours < 0:
            raise ValueError("age_hours cannot be negative")

        exclusion_sql = ""
        params: list[Any] = [metric, age_hours, metric, project_id]
        if exclude_content_item_id is not None:
            exclusion_sql = "and ci.id <> %s"
            params.append(exclude_content_item_id)
        params.append(limit)

        with self.connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"""
                select jsonb_extract_path_text(ms.metrics, %s)::numeric
                from ci_content_items ci
                join lateral (
                    select metrics
                    from ci_metric_snapshots
                    where content_item_id = ci.id
                      and age_hours = %s
                      and jsonb_extract_path_text(metrics, %s) is not null
                    order by captured_at desc
                    limit 1
                ) ms on true
                where ci.project_id = %s
                  and ci.platform = 'instagram'
                  {exclusion_sql}
                order by ci.published_at desc nulls last
                limit %s
                """,
                params,
            )
            return [float(row[0]) for row in cur.fetchall() if row[0] is not None]
