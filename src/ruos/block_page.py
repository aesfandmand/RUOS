"""Turn a composed block sequence into a complete, self-contained HTML document."""
from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .block_composer import ComposedPage, compose_page
from .block_registry import BlockLibrary, load_library


class BlockPageError(ValueError):
    """Raised when a block page specification cannot be turned into a document."""


@dataclass(frozen=True)
class RenderedPage:
    slug: str
    html: str
    css: str
    script: str
    composed: ComposedPage


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def load_page_spec(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BlockPageError(f"Block page spec not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BlockPageError(f"Invalid JSON in {path}: {exc}") from exc
    for key in ("slug", "title", "description", "blocks"):
        if not raw.get(key):
            raise BlockPageError(f"Block page spec is missing '{key}'")
    return raw


def _schema_graph(spec: Mapping[str, Any], composed: ComposedPage) -> dict[str, Any]:
    """Derive structured data from the blocks that are actually on the page."""
    slug = spec["slug"]
    brand = (spec.get("shell", {}).get("site-header", {}).get("brand", {})).get("name", "")
    graph: list[dict[str, Any]] = [
        {
            "@type": "WebPage",
            "@id": f"#{slug}",
            "name": spec["title"],
            "description": spec["description"],
            "inLanguage": spec.get("lang", "fa"),
            "isPartOf": {"@type": "WebSite", "name": brand},
        }
    ]

    by_block = {entry["block"]: entry for entry in spec["blocks"]}

    catalog = by_block.get("family-stack")
    if catalog:
        families = catalog.get("data", {}).get("families", [])
        graph.append({
            "@type": "ItemList",
            "name": catalog.get("data", {}).get("title", ""),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "name": family.get("title", ""),
                    "description": family.get("body", ""),
                }
                for index, family in enumerate(families, start=1)
            ],
        })

    faq = by_block.get("faq-grid")
    if faq:
        questions = faq.get("data", {}).get("questions", [])
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item.get("q", ""),
                    "acceptedAnswer": {"@type": "Answer", "text": item.get("a", "")},
                }
                for item in questions
            ],
        })

    return {"@context": "https://schema.org", "@graph": graph}


def render_page(spec: Mapping[str, Any], library: BlockLibrary | None = None) -> RenderedPage:
    library = library or load_library()
    composed = compose_page(
        library=library,
        slug=spec["slug"],
        sequence=spec["blocks"],
        shell=spec.get("shell"),
    )

    lang = spec.get("lang", "fa")
    direction = spec.get("direction", "rtl")
    schema = json.dumps(_schema_graph(spec, composed), ensure_ascii=False)
    canonical = spec.get("canonical", "")
    canonical_tag = f'<link rel="canonical" href="{_esc(canonical)}">' if canonical else ""

    document = (
        "<!doctype html>\n"
        f'<html lang="{_esc(lang)}" dir="{_esc(direction)}" data-page="{_esc(spec["slug"])}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        '<meta name="theme-color" content="#17161B">\n'
        f"<title>{_esc(spec['title'])}</title>\n"
        f'<meta name="description" content="{_esc(spec["description"])}">\n'
        f"{canonical_tag}\n"
        '<link rel="stylesheet" href="assets/styles.css">\n'
        f'<script type="application/ld+json">{schema}</script>\n'
        "</head>\n"
        "<body>\n"
        '<a class="skip-link" href="#main">پرش به محتوای اصلی</a>\n'
        f"{composed.body}\n"
        '<script src="assets/behavior.js" defer></script>\n'
        "</body>\n"
        "</html>"
    )

    return RenderedPage(
        slug=spec["slug"],
        html=document,
        css=composed.css,
        script=composed.script,
        composed=composed,
    )
