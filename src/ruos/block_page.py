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
    raw["shell"] = _resolve_shell(raw.get("shell"), raw.get("nav_section"), path)
    return raw


def _resolve_shell(shell: Any, nav_section: Any, path: Path) -> Any:
    """``"shell": "@site"`` means the one site-wide shell.

    The navigation lock's third clause is that two pages may not render
    different ``site-header``/``bottom-nav`` data. A page that writes its own
    copy can always drift from the others; ``@site`` is how a page says it
    takes the shared one, which makes drift impossible rather than merely
    tested for. See ``ruos.site_shell``.

    ``nav_section`` is the one thing a page still says for itself: which
    bottom-nav section it belongs to, so the liquid bubble rests on it.
    It is stated rather than derived from ``canonical`` because some pages'
    canonical still carries a pre-architecture path (urban-investment's is
    ``/services/urban-investment/``, while the registry records the
    investment hub as ``/investment/``, KEEP) and inferring from it would
    light up the wrong tab.
    """
    from .site_shell import SITE_SHELL_REF, site_shell

    if shell == SITE_SHELL_REF:
        return site_shell(active_href=nav_section)
    if isinstance(shell, str):
        raise BlockPageError(
            f"{path}: 'shell' must be an object or {SITE_SHELL_REF!r}, got {shell!r}"
        )
    return shell


def _schema_graph(spec: Mapping[str, Any], composed: ComposedPage) -> dict[str, Any]:
    """Derive structured data from the blocks that are actually on the page."""
    slug = spec["slug"]
    brand = (spec.get("shell", {}).get("site-header", {}).get("brand", {})).get("name", "")
    page_node: dict[str, Any] = {
        "@type": spec.get("page_type", "WebPage"),
        "@id": f"#{slug}",
        "name": spec["title"],
        "description": spec["description"],
        "inLanguage": spec.get("lang", "fa"),
        "isPartOf": {"@type": "WebSite", "name": brand},
    }
    if spec.get("canonical"):
        page_node["url"] = spec["canonical"]
    # Dates are stated, never derived: a page's review date is an editorial
    # promise (ru-senior-seo §5-ب.14), not the time the composer ran.
    for key, prop in (("date_published", "datePublished"), ("date_modified", "dateModified")):
        if spec.get(key):
            page_node[prop] = spec[key]
    graph: list[dict[str, Any]] = [page_node]

    # BreadcrumbList from the spec's stated trail (names from sitemap v5).
    trail = spec.get("breadcrumb") or []
    if trail:
        graph.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": step["name"], "item": step["url"]}
                for i, step in enumerate(trail, start=1)
            ],
        })

    by_block = {entry["block"]: entry for entry in spec["blocks"]}

    # A portfolio grid is a collection of creative works. Only samples that
    # carry a picture are emitted, and only the fields the card shows: an
    # empty slot is not a work, and a field WordPress has not filled yet
    # (client, city, year) is not stated here.
    grid = by_block.get("portfolio-grid")
    if grid:
        limit = int(spec.get("schema_items_limit", 12))
        works = [item for item in grid.get("data", {}).get("items", []) if item.get("src")][:limit]
        if works:
            graph.append({
                "@type": "ItemList",
                "name": grid.get("data", {}).get("title", ""),
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i,
                        "item": {
                            "@type": "CreativeWork",
                            "name": item.get("title", ""),
                            "genre": item.get("service_label", ""),
                            "url": item.get("href", ""),
                            "creator": {"@type": "Organization", "name": brand},
                            "image": {
                                "@type": "ImageObject",
                                "contentUrl": item.get("src", ""),
                                "description": item.get("alt", ""),
                            },
                        },
                    }
                    for i, item in enumerate(works, start=1)
                ],
            })

    catalog = by_block.get("products-section") or by_block.get("service-map")
    if catalog:
        data = catalog.get("data", {})
        families = data.get("products") or data.get("services") or []
        # A service hub's list items are Services, not bare names: the page
        # exists to be found for the service, so the item has to carry the
        # type, the provider and where the service is offered. Any other page
        # keeps the plain ListItem it has always emitted.
        as_service = spec.get("schema_item_type") == "Service"
        area_served = spec.get("schema_area_served") or []

        def _element(index: int, family: Mapping[str, Any]) -> dict[str, Any]:
            name = family.get("title", "")
            description = (
                family.get("meta", {}).get("use")
                or family.get("qualifier")
                or ""
            )
            element: dict[str, Any] = {"@type": "ListItem", "position": index}
            if not as_service:
                element["name"] = name
                element["description"] = description
                return element
            service: dict[str, Any] = {
                "@type": "Service",
                "name": name,
                "serviceType": family.get("meta", {}).get("type", name),
                "provider": {"@type": "Organization", "name": brand},
            }
            if description:
                service["description"] = description
            if area_served:
                service["areaServed"] = [
                    {"@type": "AdministrativeArea", "name": area} for area in area_served
                ]
            if family.get("href"):
                service["url"] = family["href"]
            element["item"] = service
            return element

        graph.append({
            "@type": "ItemList",
            "name": data.get("title", ""),
            "itemListElement": [
                _element(index, family) for index, family in enumerate(families, start=1)
            ],
        })

    faq = by_block.get("faq-section-final")
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


def _icon_sprite(library: BlockLibrary) -> str:
    """Inline the vendored icon sprite (see blocks/_foundation/assets/icon-sprite.svg)
    once per page so blocks can reference icons with <use href="#icon-name">."""
    foundation = library.blocks.get("_foundation")
    if foundation is None:
        return ""
    for asset in foundation.assets:
        if asset.name == "icon-sprite.svg":
            return asset.read_text(encoding="utf-8").strip() + "\n"
    return ""


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
    # A page whose blocks import a vendored behaviour library (see
    # block_registry.VENDOR_LIBRARIES) needs a module script so `import`
    # statements in behavior.js resolve; a page with none keeps the plain
    # classic script it always had.
    script_tag = (
        '<script type="module" src="assets/behavior.js"></script>\n'
        if composed.vendor else
        '<script src="assets/behavior.js" defer></script>\n'
    )
    icon_sprite = _icon_sprite(library)

    # Robots and Open Graph are stated per page. A page that states neither
    # renders exactly the head it always did.
    head_extra: list[str] = []
    if spec.get("robots"):
        head_extra.append(f'<meta name="robots" content="{_esc(spec["robots"])}">')
    og = spec.get("og") or {}
    if og:
        og_fields = [
            ("og:type", og.get("type", "website")),
            ("og:locale", og.get("locale", "fa_IR")),
            ("og:site_name", og.get("site_name", "")),
            ("og:title", og.get("title", spec["title"])),
            ("og:description", og.get("description", spec["description"])),
            ("og:url", canonical),
            ("og:image", og.get("image", "")),
            ("og:image:alt", og.get("image_alt", "")),
        ]
        head_extra += [f'<meta property="{p}" content="{_esc(v)}">' for p, v in og_fields if v]
        head_extra.append('<meta name="twitter:card" content="summary_large_image">')
    head_extra_html = "".join(line + "\n" for line in head_extra)

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
        f"{head_extra_html}"
        '<link rel="stylesheet" href="assets/styles.css">\n'
        f'<script type="application/ld+json">{schema}</script>\n'
        "</head>\n"
        "<body>\n"
        '<a class="skip-link" href="#main">پرش به محتوای اصلی</a>\n'
        f"{icon_sprite}"
        f"{composed.body}\n"
        f"{script_tag}"
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
