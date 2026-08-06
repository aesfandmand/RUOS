from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Callable, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


class LiveResearchError(RuntimeError):
    """Raised when live evidence cannot be fetched or verified safely."""


@dataclass(frozen=True)
class FetchPolicy:
    timeout_seconds: float = 12.0
    max_bytes: int = 2_000_000
    max_redirects: int = 5
    user_agent: str = "RUOS-LiveResearch/1.0 (+https://github.com/aesfandmand/RUOS)"
    allowed_schemes: tuple[str, ...] = ("https",)
    blocked_hosts: tuple[str, ...] = ("localhost",)
    allowed_content_types: tuple[str, ...] = (
        "text/html",
        "application/xhtml+xml",
        "application/json",
        "text/plain",
    )


@dataclass(frozen=True)
class TransportResponse:
    requested_url: str
    final_url: str
    status: int
    headers: Mapping[str, str]
    body: bytes


class ResearchTransport(Protocol):
    def fetch(self, url: str, policy: FetchPolicy) -> TransportResponse: ...


@dataclass(frozen=True)
class LiveEvidence:
    source_id: str
    requested_url: str
    final_url: str
    origin: str
    fetched_at: str
    status: int
    content_type: str
    content_sha256: str
    byte_length: int
    title: str
    excerpt: str
    observations: tuple[str, ...]
    inferences: tuple[str, ...]
    manual_claims: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "origin": self.origin,
            "fetched_at": self.fetched_at,
            "status": self.status,
            "content_type": self.content_type,
            "content_sha256": self.content_sha256,
            "byte_length": self.byte_length,
            "title": self.title,
            "excerpt": self.excerpt,
            "observations": list(self.observations),
            "inferences": list(self.inferences),
            "manual_claims": list(self.manual_claims),
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = True
        if lowered in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "title":
            self._in_title = False
        if lowered in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if not clean:
            return
        if self._in_title:
            self.title_parts.append(clean)
        if not self._ignored_depth:
            self.text_parts.append(clean)


def _is_public_ip(value: str) -> bool:
    address = ipaddress.ip_address(value)
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _validate_public_url(url: str, policy: FetchPolicy) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in policy.allowed_schemes:
        raise LiveResearchError(f"URL scheme is not allowed: {parsed.scheme or '<missing>'}")
    if parsed.username or parsed.password:
        raise LiveResearchError("Credential-bearing URLs are not allowed")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise LiveResearchError("URL must include a hostname")
    if host in policy.blocked_hosts or host.endswith(".localhost"):
        raise LiveResearchError(f"Blocked research host: {host}")
    try:
        addresses = {result[4][0] for result in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM)}
    except socket.gaierror as exc:
        raise LiveResearchError(f"Unable to resolve research host '{host}'") from exc
    if not addresses or any(not _is_public_ip(address) for address in addresses):
        raise LiveResearchError(f"Research host resolves to a non-public address: {host}")


class _SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, policy: FetchPolicy) -> None:
        super().__init__()
        self.policy = policy
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        self.redirect_count += 1
        if self.redirect_count > self.policy.max_redirects:
            raise LiveResearchError(
                f"Research request exceeded {self.policy.max_redirects} redirects"
            )
        resolved = urljoin(req.full_url, newurl)
        _validate_public_url(resolved, self.policy)
        return super().redirect_request(req, fp, code, msg, headers, resolved)


class UrllibResearchTransport:
    def fetch(self, url: str, policy: FetchPolicy) -> TransportResponse:
        _validate_public_url(url, policy)
        request = Request(
            url,
            headers={
                "User-Agent": policy.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/json,text/plain;q=0.9",
                "Accept-Encoding": "identity",
            },
            method="GET",
        )
        opener = build_opener(_SafeRedirectHandler(policy))
        try:
            with opener.open(request, timeout=policy.timeout_seconds) as response:
                final_url = response.geturl()
                _validate_public_url(final_url, policy)
                status = int(getattr(response, "status", 200))
                headers = {key.lower(): value for key, value in response.headers.items()}
                content_type = headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if content_type not in policy.allowed_content_types:
                    raise LiveResearchError(
                        f"Research response content type is not allowed: {content_type or '<missing>'}"
                    )
                body = response.read(policy.max_bytes + 1)
                if len(body) > policy.max_bytes:
                    raise LiveResearchError(f"Research response exceeds {policy.max_bytes} bytes")
                return TransportResponse(url, final_url, status, headers, body)
        except LiveResearchError:
            raise
        except HTTPError as exc:
            raise LiveResearchError(f"Research request failed with HTTP {exc.code}: {url}") from exc
        except URLError as exc:
            raise LiveResearchError(f"Research request failed: {url}: {exc.reason}") from exc


def _decode_body(body: bytes, content_type: str) -> str:
    charset = "utf-8"
    for part in content_type.split(";")[1:]:
        key, _, value = part.strip().partition("=")
        if key.lower() == "charset" and value:
            charset = value.strip('"\'')
            break
    try:
        return body.decode(charset, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def _extract_text(body: bytes, content_type: str) -> tuple[str, str]:
    text = _decode_body(body, content_type)
    if "html" not in content_type.lower():
        compact = " ".join(text.split())
        return "", compact[:700]
    parser = _TextExtractor()
    parser.feed(text)
    title = " ".join(parser.title_parts).strip()[:240]
    excerpt = " ".join(parser.text_parts).strip()[:700]
    return title, excerpt


class LiveResearchAdapter:
    def __init__(
        self,
        transport: ResearchTransport | None = None,
        policy: FetchPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.transport = transport or UrllibResearchTransport()
        self.policy = policy or FetchPolicy()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def fetch_source(
        self,
        source_id: str,
        url: str,
        *,
        observations: tuple[str, ...] = (),
        inferences: tuple[str, ...] = (),
        manual_claims: tuple[str, ...] = (),
    ) -> LiveEvidence:
        source_id = source_id.strip()
        if not source_id:
            raise LiveResearchError("Live evidence requires a source id")
        response = self.transport.fetch(url, self.policy)
        if response.status < 200 or response.status >= 300:
            raise LiveResearchError(f"Research source returned non-success status {response.status}")
        content_type = response.headers.get("content-type", "application/octet-stream")
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type not in self.policy.allowed_content_types:
            raise LiveResearchError(
                f"Research response content type is not allowed: {media_type or '<missing>'}"
            )
        title, excerpt = _extract_text(response.body, content_type)
        if not excerpt:
            raise LiveResearchError("Research source did not yield extractable evidence")
        fetched_at = self.clock().astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return LiveEvidence(
            source_id=source_id,
            requested_url=response.requested_url,
            final_url=response.final_url,
            origin="live-web",
            fetched_at=fetched_at,
            status=response.status,
            content_type=content_type,
            content_sha256=hashlib.sha256(response.body).hexdigest(),
            byte_length=len(response.body),
            title=title,
            excerpt=excerpt,
            observations=tuple(item.strip() for item in observations if item.strip()),
            inferences=tuple(item.strip() for item in inferences if item.strip()),
            manual_claims=tuple(item.strip() for item in manual_claims if item.strip()),
        )
