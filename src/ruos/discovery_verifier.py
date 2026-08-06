from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .live_research import LiveResearchError
from .search_discovery import SearchDiscovery


@dataclass(frozen=True)
class VerifiedSearchDiscovery:
    provider: str
    query: str
    market: str
    language: str
    fetched_at: str
    result_count: int
    freshness_hours: int
    sha256: str

    def payload(self) -> dict[str, object]:
        return {
            "status": "verified-search-discovery",
            "provider": self.provider,
            "query": self.query,
            "market": self.market,
            "language": self.language,
            "fetched_at": self.fetched_at,
            "result_count": self.result_count,
            "freshness_hours": self.freshness_hours,
            "sha256": self.sha256,
        }


def verify_discovery(
    discovery: SearchDiscovery,
    *,
    expected_query: str,
    expected_market: str,
    expected_language: str,
    now: datetime | None = None,
    max_age: timedelta = timedelta(days=7),
    minimum_results: int = 5,
) -> VerifiedSearchDiscovery:
    if discovery.query.strip() != expected_query.strip():
        raise LiveResearchError("Search discovery query does not match the page query")
    if discovery.market.lower() != expected_market.lower():
        raise LiveResearchError("Search discovery market does not match the requested market")
    if discovery.language.lower() != expected_language.lower():
        raise LiveResearchError("Search discovery language does not match the requested language")
    if len(discovery.results) < minimum_results:
        raise LiveResearchError(
            f"Search discovery has {len(discovery.results)} results; minimum is {minimum_results}"
        )
    urls = [item.url for item in discovery.results]
    if len(urls) != len(set(urls)):
        raise LiveResearchError("Search discovery contains duplicate result URLs")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    try:
        fetched = datetime.fromisoformat(discovery.fetched_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError as exc:
        raise LiveResearchError("Search discovery timestamp is invalid") from exc
    age = current - fetched
    if age < timedelta(0):
        raise LiveResearchError("Search discovery timestamp is in the future")
    if age > max_age:
        raise LiveResearchError("Search discovery snapshot is stale")
    return VerifiedSearchDiscovery(
        provider=discovery.provider,
        query=discovery.query,
        market=discovery.market,
        language=discovery.language,
        fetched_at=discovery.fetched_at,
        result_count=len(discovery.results),
        freshness_hours=int(age.total_seconds() // 3600),
        sha256=discovery.sha256,
    )
