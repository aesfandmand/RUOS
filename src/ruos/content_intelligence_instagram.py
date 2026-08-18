"""Instagram Owned Insights connector for RUOS Content Intelligence.

This module deliberately uses only the Python standard library. It does not own
OAuth credentials and never persists access tokens. Runtime credentials are read
from environment variables or passed explicitly by the caller.

The connector targets Instagram professional accounts (Business/Creator) using
Meta's official Instagram Platform. API version is required at runtime instead of
being hard-coded so RUOS does not silently depend on an expired Graph API version.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_MEDIA_FIELDS = (
    "id",
    "caption",
    "media_type",
    "media_product_type",
    "permalink",
    "timestamp",
    "like_count",
    "comments_count",
)

# Keep this set intentionally conservative. Some metrics are media-type specific;
# fetch_media_insights_resilient() records unsupported metrics instead of failing
# the whole snapshot.
DEFAULT_MEDIA_INSIGHT_METRICS = (
    "views",
    "reach",
    "likes",
    "comments",
    "saved",
    "shares",
    "total_interactions",
)

REQUIRED_INSTAGRAM_LOGIN_PERMISSIONS = (
    "instagram_business_basic",
    "instagram_business_manage_insights",
)


class InstagramConfigError(ValueError):
    """Raised when required runtime configuration is missing."""


class InstagramAPIError(RuntimeError):
    """Normalized Instagram Platform error."""

    def __init__(self, message: str, *, status: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status = status
        self.payload = payload


@dataclass(frozen=True)
class InstagramConfig:
    access_token: str
    user_id: str
    api_version: str
    base_url: str = "https://graph.instagram.com"
    timeout_seconds: float = 20.0

    @classmethod
    def from_env(cls) -> "InstagramConfig":
        required = {
            "access_token": os.getenv("CI_INSTAGRAM_ACCESS_TOKEN"),
            "user_id": os.getenv("CI_INSTAGRAM_USER_ID"),
            "api_version": os.getenv("CI_META_GRAPH_API_VERSION"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise InstagramConfigError(
                "Missing Instagram runtime configuration: " + ", ".join(missing)
            )
        return cls(**required)  # type: ignore[arg-type]

    def endpoint(self, object_path: str) -> str:
        version = self.api_version.strip("/")
        path = object_path.strip("/")
        return f"{self.base_url.rstrip('/')}/{version}/{path}"


class InstagramOwnedInsightsClient:
    """Small read-only client for owned Instagram media and insights."""

    def __init__(self, config: InstagramConfig):
        self.config = config

    def _request_json(
        self,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if params:
            clean = {key: value for key, value in params.items() if value is not None}
            url = f"{url}?{urlencode(clean, doseq=True)}"

        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {self.config.access_token}",
                "Accept": "application/json",
                "User-Agent": "RUOS-Content-Intelligence/0.2",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw)
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                payload: Any = json.loads(raw)
            except json.JSONDecodeError:
                payload = raw
            message = _extract_error_message(payload) or f"Instagram API HTTP {exc.code}"
            raise InstagramAPIError(message, status=exc.code, payload=payload) from exc
        except URLError as exc:
            raise InstagramAPIError(f"Instagram API network error: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise InstagramAPIError("Instagram API returned invalid JSON") from exc

    def list_media(
        self,
        *,
        fields: Iterable[str] = DEFAULT_MEDIA_FIELDS,
        page_limit: int = 100,
        max_items: int = 500,
    ) -> list[dict[str, Any]]:
        if page_limit < 1 or max_items < 1:
            raise ValueError("page_limit and max_items must be >= 1")

        url = self.config.endpoint(f"{self.config.user_id}/media")
        params: Mapping[str, Any] | None = {
            "fields": ",".join(fields),
            "limit": min(page_limit, max_items),
        }
        items: list[dict[str, Any]] = []

        while url and len(items) < max_items:
            payload = self._request_json(url, params=params)
            data = payload.get("data", [])
            if not isinstance(data, list):
                raise InstagramAPIError("Instagram media response has invalid data shape")
            items.extend(item for item in data if isinstance(item, dict))
            next_url = payload.get("paging", {}).get("next")
            url = next_url if isinstance(next_url, str) and next_url else ""
            params = None  # paging.next already contains its own query parameters

        return items[:max_items]

    def fetch_media_insights(
        self,
        media_id: str,
        metrics: Iterable[str] = DEFAULT_MEDIA_INSIGHT_METRICS,
    ) -> dict[str, float | int]:
        metric_list = tuple(dict.fromkeys(metric.strip() for metric in metrics if metric.strip()))
        if not metric_list:
            raise ValueError("metrics cannot be empty")
        payload = self._request_json(
            self.config.endpoint(f"{media_id}/insights"),
            params={"metric": ",".join(metric_list)},
        )
        return normalize_insights_payload(payload)

    def fetch_media_insights_resilient(
        self,
        media_id: str,
        metrics: Iterable[str] = DEFAULT_MEDIA_INSIGHT_METRICS,
    ) -> tuple[dict[str, float | int], dict[str, str]]:
        """Read metrics individually so one unsupported metric does not lose a snapshot."""

        values: dict[str, float | int] = {}
        errors: dict[str, str] = {}
        for metric in dict.fromkeys(metric.strip() for metric in metrics if metric.strip()):
            try:
                values.update(self.fetch_media_insights(media_id, (metric,)))
            except InstagramAPIError as exc:
                errors[metric] = str(exc)
        return values, errors


def normalize_insights_payload(payload: Mapping[str, Any]) -> dict[str, float | int]:
    """Normalize the Graph response to a flat metric dictionary.

    Meta has used both ``values[0].value`` and ``total_value.value`` shapes across
    Insights surfaces. Supporting both keeps the storage layer independent from
    response-shape differences.
    """

    data = payload.get("data", [])
    if not isinstance(data, list):
        raise InstagramAPIError("Instagram insights response has invalid data shape")

    normalized: dict[str, float | int] = {}
    for item in data:
        if not isinstance(item, Mapping):
            continue
        name = item.get("name")
        if not isinstance(name, str) or not name:
            continue

        value: Any = None
        total_value = item.get("total_value")
        if isinstance(total_value, Mapping):
            value = total_value.get("value")

        if value is None:
            values = item.get("values")
            if isinstance(values, list) and values and isinstance(values[0], Mapping):
                value = values[0].get("value")

        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, (int, float)):
            normalized[name] = value

    return normalized


def _extract_error_message(payload: Any) -> str | None:
    if not isinstance(payload, Mapping):
        return None
    error = payload.get("error")
    if isinstance(error, Mapping):
        message = error.get("message")
        if isinstance(message, str):
            return message
    return None
