#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import ssl
import sys
import time
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE = "https://chatreghermez.com"
OUT_DIR = Path("11-projects/red-umbrella/registries")
CSV_OUT = OUT_DIR / "chatreghermez-live-url-audit-v1.csv"
JSON_OUT = OUT_DIR / "chatreghermez-live-url-audit-v1.json"
MD_OUT = OUT_DIR / "chatreghermez-live-url-audit-v1.md"

PATHS = [
    "/",
    "/environmental-advertising",
    "/environmental-advertising/",
    "/municipality-investment",
    "/municipality-investment/",
    "/investment/",
    "/billboard-rental-isfahan",
    "/billboard-rental-isfahan/",
    "/billboard-mobarakeh",
    "/billboard-mobarakeh/",
    "/cities/mobarakeh/",
    "/advertising-foladshahr",
    "/advertising-foladshahr/",
    "/cities/foladshahr/",
    "/billboard-types",
    "/billboard-types/",
    "/structures/",
    "/services",
    "/services/",
    "/web-design-isfahan",
    "/web-design-isfahan/",
    "/web-design/",
    "/graphic-design",
    "/graphic-design/",
    "/printing",
    "/printing/",
    "/video-marketing-isfahan",
    "/video-marketing-isfahan/",
    "/advertising-video-production/",
    "/product-photography",
    "/product-photography/",
    "/social-media-management",
    "/social-media-management/",
    "/consulting",
    "/consulting/",
    "/portfolio",
    "/portfolio/",
    "/about",
    "/about/",
    "/about-us",
    "/about-us/",
    "/contact",
    "/contact/",
    "/contact-us",
    "/contact-us/",
    "/credentials",
    "/credentials/",
    "/blog",
    "/blog/",
    "/robots.txt",
    "/sitemap.xml",
    "/sitemap_index.xml",
]

USER_AGENT = "Mozilla/5.0 (compatible; RedUmbrellaArchitectureAudit/1.0; +https://chatreghermez.com/)"
TIMEOUT = 20
MAX_REDIRECTS = 8


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HeadParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts: List[str] = []
        self.h1_parts: List[str] = []
        self.in_title = False
        self.in_h1 = False
        self.canonical = ""
        self.meta_robots: List[str] = []
        self.meta_description = ""
        self.visible_text: List[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs_dict = {str(k).lower(): (v or "") for k, v in attrs}
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.in_h1 = True
        if tag == "link" and attrs_dict.get("rel", "").lower() == "canonical":
            self.canonical = attrs_dict.get("href", "").strip()
        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            content = attrs_dict.get("content", "").strip()
            if name in {"robots", "googlebot"} and content:
                self.meta_robots.append(content)
            if name == "description" and content and not self.meta_description:
                self.meta_description = content

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_h1 = False
        if tag in {"script", "style", "noscript", "svg"} and self.skip_depth > 0:
            self.skip_depth -= 1

    def handle_data(self, data):
        txt = " ".join(data.split())
        if not txt:
            return
        if self.in_title:
            self.title_parts.append(txt)
        if self.in_h1:
            self.h1_parts.append(txt)
        if self.skip_depth == 0:
            self.visible_text.append(txt)


@dataclass
class AuditRow:
    requested_url: str
    initial_status: str = ""
    final_status: str = ""
    final_url: str = ""
    redirect_hops: int = 0
    redirect_chain: str = ""
    content_type: str = ""
    title: str = ""
    h1: str = ""
    canonical: str = ""
    meta_robots: str = ""
    x_robots_tag: str = ""
    indexable_guess: str = ""
    meta_description: str = ""
    text_sample: str = ""
    content_bytes: int = 0
    content_sha256: str = ""
    error: str = ""


def clean_text(value: str, limit: int = 500) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def fetch_once(url: str) -> Tuple[int, Dict[str, str], bytes]:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.5",
            "Connection": "close",
        },
        method="GET",
    )
    opener = build_opener(NoRedirect())
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            return int(resp.getcode()), dict(resp.headers.items()), resp.read()
    except HTTPError as exc:
        body = b""
        try:
            body = exc.read()
        except Exception:
            pass
        return int(exc.code), dict(exc.headers.items()), body


def audit_url(url: str) -> AuditRow:
    row = AuditRow(requested_url=url)
    current = url
    chain: List[str] = []
    try:
        for hop in range(MAX_REDIRECTS + 1):
            status, headers, body = fetch_once(current)
            if hop == 0:
                row.initial_status = str(status)
            location = headers.get("Location") or headers.get("location")
            if status in {301, 302, 303, 307, 308} and location:
                nxt = urljoin(current, location)
                chain.append(f"{status} {current} -> {nxt}")
                current = nxt
                time.sleep(0.1)
                continue

            row.final_status = str(status)
            row.final_url = current
            row.redirect_hops = len(chain)
            row.redirect_chain = " || ".join(chain)
            row.content_type = headers.get("Content-Type", headers.get("content-type", ""))
            row.x_robots_tag = headers.get("X-Robots-Tag", headers.get("x-robots-tag", ""))
            row.content_bytes = len(body)
            row.content_sha256 = hashlib.sha256(body).hexdigest() if body else ""

            if body and ("text/html" in row.content_type.lower() or body[:100].lower().find(b"<html") >= 0):
                text = body.decode("utf-8", errors="replace")
                parser = HeadParser()
                try:
                    parser.feed(text)
                except Exception:
                    pass
                row.title = clean_text(" ".join(parser.title_parts), 250)
                row.h1 = clean_text(" | ".join(parser.h1_parts), 350)
                row.canonical = clean_text(parser.canonical, 500)
                row.meta_robots = clean_text(", ".join(parser.meta_robots), 250)
                row.meta_description = clean_text(parser.meta_description, 400)
                row.text_sample = clean_text(" ".join(parser.visible_text), 800)

            noindex_tokens = (row.meta_robots + " " + row.x_robots_tag).lower()
            if status == 200 and "noindex" not in noindex_tokens:
                row.indexable_guess = "YES"
            elif status == 200:
                row.indexable_guess = "NO_NOINDEX"
            else:
                row.indexable_guess = "NO_STATUS"
            return row

        row.error = f"redirect_limit_exceeded:{MAX_REDIRECTS}"
        row.final_url = current
        row.redirect_hops = len(chain)
        row.redirect_chain = " || ".join(chain)
        return row
    except (URLError, TimeoutError, ssl.SSLError, OSError) as exc:
        row.error = f"{type(exc).__name__}: {exc}"
        row.final_url = current
        row.redirect_hops = len(chain)
        row.redirect_chain = " || ".join(chain)
        return row
    except Exception as exc:
        row.error = f"{type(exc).__name__}: {exc}"
        row.final_url = current
        row.redirect_hops = len(chain)
        row.redirect_chain = " || ".join(chain)
        return row


def write_outputs(rows: List[AuditRow]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(asdict(rows[0]).keys()) if rows else list(AuditRow("").__dict__.keys())
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    JSON_OUT.write_text(json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2), encoding="utf-8")

    counts: Dict[str, int] = {}
    for r in rows:
        key = r.final_status or "ERROR"
        counts[key] = counts.get(key, 0) + 1

    lines = [
        "# Red Umbrella — Live URL Audit v1",
        "",
        "**Execution:** GitHub Actions live HTTP audit",
        f"**Base:** {BASE}",
        f"**URLs tested:** {len(rows)}",
        "",
        "## Status summary",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(["", "## URLs with errors or non-200 final status", ""])
    problem_rows = [r for r in rows if r.error or r.final_status != "200"]
    if not problem_rows:
        lines.append("- None")
    else:
        for r in problem_rows:
            lines.append(f"- `{r.requested_url}` → `{r.final_status or 'ERROR'}` → `{r.final_url}` — {clean_text(r.error, 250)}")

    lines.extend(["", "## Canonical / redirect observations", ""])
    for r in rows:
        if r.redirect_hops or r.canonical:
            lines.append(
                f"- `{r.requested_url}` | final `{r.final_status}` `{r.final_url}` | hops `{r.redirect_hops}` | canonical `{r.canonical or '-'}' | title: {r.title or '-'}"
            )

    lines.extend([
        "",
        "## Truth note",
        "",
        "This file records HTTP evidence observed during this workflow run. `indexable_guess` is a mechanical check based on final HTTP 200 plus absence of an explicit `noindex`; it is not a Search Console indexed-state claim.",
        "",
    ])
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows: List[AuditRow] = []
    for i, path in enumerate(PATHS, start=1):
        url = urljoin(BASE, path)
        print(f"[{i}/{len(PATHS)}] {url}", flush=True)
        row = audit_url(url)
        rows.append(row)
        print(f"  initial={row.initial_status or '-'} final={row.final_status or '-'} url={row.final_url} error={row.error or '-'}", flush=True)
        time.sleep(0.15)
    write_outputs(rows)
    success = sum(1 for r in rows if r.final_status)
    print(f"Completed with HTTP evidence for {success}/{len(rows)} URLs")
    return 0 if success > 0 else 2


if __name__ == "__main__":
    sys.exit(main())
