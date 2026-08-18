"""Platform-specific research adapters for RUOS Content Intelligence.

The module separates *discovery* from *evidence*. Public competitor research never
pretends to have private analytics. YouTube can use the official Data API when a
key is configured; Instagram competitive, TikTok Creative Center/TikTok One, and
LinkedIn competitive research are normalized from public/authorized observations.
"""
from __future__ import annotations

import json
import os
from typing import Any, Iterable, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .research_collectors import ResearchEvidence


class SocialCollectorConfigError(ValueError):
    pass


class YouTubeDataAPICollector:
    """Official YouTube Data API discovery + public statistics collector."""

    SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(self, api_key: str | None = None, timeout_seconds: float = 20.0):
        self.api_key = api_key or os.getenv("CI_YOUTUBE_API_KEY")
        if not self.api_key:
            raise SocialCollectorConfigError("CI_YOUTUBE_API_KEY is not configured")
        self.timeout_seconds = timeout_seconds

    def _get(self, endpoint: str, params: Mapping[str, Any]) -> dict[str, Any]:
        query = dict(params)
        query["key"] = self.api_key
        req = Request(
            f"{endpoint}?{urlencode(query)}",
            headers={"Accept": "application/json", "User-Agent": "RUOS-Content-Intelligence/0.3"},
        )
        with urlopen(req, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def search(self, query: str, *, max_results: int = 25, language: str | None = None, region: str | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max(1, min(50, max_results)),
            "order": "relevance",
        }
        if language:
            params["relevanceLanguage"] = language
        if region:
            params["regionCode"] = region
        payload = self._get(self.SEARCH_ENDPOINT, params)
        return [item for item in payload.get("items", []) if isinstance(item, dict)]

    def video_statistics(self, video_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
        ids = [x for x in dict.fromkeys(video_ids) if x][:50]
        if not ids:
            return {}
        payload = self._get(self.VIDEOS_ENDPOINT, {"part": "snippet,statistics,contentDetails", "id": ",".join(ids)})
        return {item["id"]: item for item in payload.get("items", []) if isinstance(item, dict) and item.get("id")}

    def collect(self, *, project_id: str, query: str, max_results: int = 25, language: str | None = None, region: str | None = None) -> list[ResearchEvidence]:
        search_items = self.search(query, max_results=max_results, language=language, region=region)
        ids = [item.get("id", {}).get("videoId") for item in search_items]
        details = self.video_statistics([x for x in ids if x])
        evidence: list[ResearchEvidence] = []
        for item in search_items:
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            detail = details.get(video_id, {})
            snippet = detail.get("snippet") or item.get("snippet") or {}
            stats = detail.get("statistics") or {}
            metrics: dict[str, int | float | None] = {}
            for src, dst in (("viewCount", "views"), ("likeCount", "likes"), ("commentCount", "comments")):
                value = stats.get(src)
                if isinstance(value, str) and value.isdigit():
                    metrics[dst] = int(value)
            evidence.append(
                ResearchEvidence(
                    project_id=project_id,
                    source="youtube",
                    source_class="competitive",
                    topic=query,
                    query=query,
                    title=snippet.get("title"),
                    canonical_url=f"https://www.youtube.com/watch?v={video_id}",
                    source_identifier=video_id,
                    published_at=snippet.get("publishedAt"),
                    language=language,
                    visible_metrics=metrics,
                    evidence_summary=snippet.get("description"),
                    confidence=0.8,
                    corroboration_status="single_source",
                )
            )
        return evidence


class InstagramCompetitiveAdapter:
    """Normalize public competitor observations without inventing private insights."""

    source = "instagram_competitive"
    source_class = "competitive"

    @staticmethod
    def from_public_post(*, project_id: str, topic: str, url: str, account: str, caption_summary: str, format: str | None = None, hook: str | None = None, visible_likes: int | None = None, visible_comments: int | None = None, published_at: str | None = None, confidence: float = 0.65) -> ResearchEvidence:
        metrics: dict[str, int | float | None] = {}
        if visible_likes is not None:
            metrics["likes"] = visible_likes
        if visible_comments is not None:
            metrics["comments"] = visible_comments
        return ResearchEvidence(
            project_id=project_id,
            source=InstagramCompetitiveAdapter.source,
            source_class=InstagramCompetitiveAdapter.source_class,
            topic=topic,
            canonical_url=url,
            source_identifier=account,
            title=account,
            published_at=published_at,
            format=format,
            hook=hook,
            visible_metrics=metrics,
            evidence_summary=caption_summary,
            confidence=confidence,
            corroboration_status="single_source",
        )


class TikTokCreativeAdapter:
    """Normalize TikTok Creative Center / TikTok One observations."""

    source = "tiktok_creative_center"
    source_class = "competitive"

    @staticmethod
    def from_creative(*, project_id: str, topic: str, url: str, title: str, summary: str, hook: str | None = None, format: str | None = "short_video", visible_metrics: Mapping[str, int | float | None] | None = None, confidence: float = 0.7) -> ResearchEvidence:
        # Metrics may include only values actually displayed by TikTok, e.g. likes,
        # reach/CTR rank or view-rate fields when explicitly available.
        return ResearchEvidence(
            project_id=project_id,
            source=TikTokCreativeAdapter.source,
            source_class=TikTokCreativeAdapter.source_class,
            topic=topic,
            canonical_url=url,
            title=title,
            hook=hook,
            format=format,
            visible_metrics=dict(visible_metrics or {}),
            evidence_summary=summary,
            confidence=confidence,
            corroboration_status="single_source",
        )


class LinkedInCompetitiveAdapter:
    """Normalize public LinkedIn B2B observations.

    This adapter intentionally does not claim unrestricted LinkedIn API search.
    Owned organization data can later use an authorized LinkedIn app separately.
    """

    source = "linkedin"
    source_class = "competitive"

    @staticmethod
    def from_public_post(*, project_id: str, topic: str, url: str, author: str, summary: str, hook: str | None = None, format: str | None = None, visible_reactions: int | None = None, visible_comments: int | None = None, published_at: str | None = None, confidence: float = 0.65) -> ResearchEvidence:
        metrics: dict[str, int | float | None] = {}
        if visible_reactions is not None:
            metrics["reactions"] = visible_reactions
        if visible_comments is not None:
            metrics["comments"] = visible_comments
        return ResearchEvidence(
            project_id=project_id,
            source=LinkedInCompetitiveAdapter.source,
            source_class=LinkedInCompetitiveAdapter.source_class,
            topic=topic,
            canonical_url=url,
            source_identifier=author,
            title=author,
            published_at=published_at,
            hook=hook,
            format=format,
            visible_metrics=metrics,
            evidence_summary=summary,
            confidence=confidence,
            corroboration_status="single_source",
        )
