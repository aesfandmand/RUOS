from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .live_research import LiveResearchError


@dataclass(frozen=True)
class SearchResult:
    rank: int
    title: str
    url: str
    snippet: str

    def payload(self) -> dict[str, object]:
        return {"rank": self.rank, "title": self.title, "url": self.url, "snippet": self.snippet}


@dataclass(frozen=True)
class SearchDiscovery:
    provider: str
    query: str
    market: str
    language: str
    fetched_at: str
    results: tuple[SearchResult, ...]

    def payload(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "query": self.query,
            "market": self.market,
            "language": self.language,
            "fetched_at": self.fetched_at,
            "results": [item.payload() for item in self.results],
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class SearchProvider(Protocol):
    name: str

    def search(self, query: str, *, market: str, language: str, count: int) -> tuple[SearchResult, ...]: ...


def _request_json(url: str, headers: Mapping[str, str], timeout_seconds: float = 15.0) -> Mapping[str, object]:
    request = Request(url, headers=dict(headers), method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            if int(getattr(response, "status", 200)) != 200:
                raise LiveResearchError(f"Search provider returned HTTP {getattr(response, 'status', 'unknown')}")
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                raise LiveResearchError("Search provider response exceeds 2000000 bytes")
            raw = json.loads(body.decode("utf-8"))
    except HTTPError as exc:
        raise LiveResearchError(f"Search provider returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise LiveResearchError(f"Search provider request failed: {exc.reason}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveResearchError("Search provider returned invalid JSON") from exc
    if not isinstance(raw, Mapping):
        raise LiveResearchError("Search provider response root must be an object")
    return raw


class BraveSearchProvider:
    name = "brave"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key or os.getenv("BRAVE_SEARCH_API_KEY", "")).strip()
        if not self.api_key:
            raise LiveResearchError("BRAVE_SEARCH_API_KEY is required for Brave search discovery")

    def search(self, query: str, *, market: str, language: str, count: int) -> tuple[SearchResult, ...]:
        params = urlencode({"q": query, "count": max(1, min(count, 20)), "country": market, "search_lang": language})
        raw = _request_json(
            f"https://api.search.brave.com/res/v1/web/search?{params}",
            {"Accept": "application/json", "X-Subscription-Token": self.api_key, "User-Agent": "RUOS-SearchDiscovery/1.0"},
        )
        web = raw.get("web", {})
        rows = web.get("results", []) if isinstance(web, Mapping) else []
        if not isinstance(rows, list):
            raise LiveResearchError("Brave search response has invalid results")
        results: list[SearchResult] = []
        for index, item in enumerate(rows[:count], start=1):
            if not isinstance(item, Mapping):
                continue
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            if not url or not title:
                continue
            results.append(SearchResult(index, title, url, str(item.get("description", "")).strip()))
        if not results:
            raise LiveResearchError("Brave search returned no usable results")
        return tuple(results)


class SerperSearchProvider:
    name = "serper"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key or os.getenv("SERPER_API_KEY", "")).strip()
        if not self.api_key:
            raise LiveResearchError("SERPER_API_KEY is required for Serper search discovery")

    def search(self, query: str, *, market: str, language: str, count: int) -> tuple[SearchResult, ...]:
        params = urlencode({"q": query, "gl": market, "hl": language, "num": max(1, min(count, 20))})
        raw = _request_json(
            f"https://google.serper.dev/search?{params}",
            {"Accept": "application/json", "X-API-KEY": self.api_key, "User-Agent": "RUOS-SearchDiscovery/1.0"},
        )
        rows = raw.get("organic", [])
        if not isinstance(rows, list):
            raise LiveResearchError("Serper response has invalid organic results")
        results: list[SearchResult] = []
        for index, item in enumerate(rows[:count], start=1):
            if not isinstance(item, Mapping):
                continue
            url = str(item.get("link", "")).strip()
            title = str(item.get("title", "")).strip()
            if not url or not title:
                continue
            results.append(SearchResult(index, title, url, str(item.get("snippet", "")).strip()))
        if not results:
            raise LiveResearchError("Serper returned no usable results")
        return tuple(results)


def discover_search(
    provider: SearchProvider,
    query: str,
    *,
    market: str = "ir",
    language: str = "fa",
    count: int = 10,
    clock: Callable[[], datetime] | None = None,
) -> SearchDiscovery:
    clean_query = query.strip()
    if not clean_query:
        raise LiveResearchError("Search discovery requires a query")
    results = provider.search(clean_query, market=market, language=language, count=count)
    fetched_at = (clock or (lambda: datetime.now(timezone.utc)))().astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return SearchDiscovery(provider.name, clean_query, market, language, fetched_at, results)


def create_provider(name: str) -> SearchProvider:
    normalized = name.strip().lower()
    if normalized == "brave":
        return BraveSearchProvider()
    if normalized == "serper":
        return SerperSearchProvider()
    raise LiveResearchError(f"Unsupported search provider: {name}")
