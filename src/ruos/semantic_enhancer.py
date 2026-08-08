from __future__ import annotations

import json
from dataclasses import dataclass

from .creative_intelligence import CreativeIntelligencePlan
from .models import PageSpec


class SemanticEnhancementError(ValueError):
    """Raised when rendered output cannot be upgraded to the semantic contract."""


@dataclass(frozen=True)
class SemanticEnhancement:
    html: str
    schema_graph: tuple[dict[str, object], ...]
    primary_heading: str


def _schema_graph(page: PageSpec, intelligence: CreativeIntelligencePlan) -> tuple[dict[str, object], ...]:
    knowledge = next((section for section in page.sections if section.kind == "knowledge"), None)
    if knowledge is None or not knowledge.items:
        raise SemanticEnhancementError("Semantic enhancement requires a populated knowledge section")

    faq_sources = [section for section in page.sections if section.body.strip()]
    faq_entities = [
        {
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {
                "@type": "Answer",
                "text": faq_sources[min(index, len(faq_sources) - 1)].body.strip(),
            },
        }
        for index, question in enumerate(intelligence.semantic.answer_targets)
    ]
    graph: tuple[dict[str, object], ...] = (
        {
            "@type": "WebPage",
            "@id": f"#{page.slug}",
            "name": page.title,
            "description": page.description,
            "inLanguage": page.lang,
            "about": {"@type": "Thing", "name": intelligence.semantic.primary_entity},
            "isPartOf": {"@type": "WebSite", "name": page.brand},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": page.brand, "item": "/"},
                {"@type": "ListItem", "position": 2, "name": page.title, "item": f"/{page.slug}/"},
            ],
        },
        {
            "@type": "ItemList",
            "name": knowledge.title,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index,
                    "name": str(item.get("title", "")).strip(),
                    "description": str(item.get("body", "")).strip(),
                }
                for index, item in enumerate(knowledge.items, start=1)
            ],
        },
        {"@type": "FAQPage", "mainEntity": faq_entities},
    )
    return graph


def enhance_semantics(
    page: PageSpec,
    intelligence: CreativeIntelligencePlan,
    rendered_html: str,
) -> SemanticEnhancement:
    h1_count = rendered_html.count("<h1")
    h2_count = rendered_html.count("<h2")
    if h1_count > 1:
        raise SemanticEnhancementError("Rendered document contains more than one H1")
    if h1_count == 0 and h2_count < 1:
        raise SemanticEnhancementError("Rendered document has no heading available for H1 promotion")
    if rendered_html.count('type="application/ld+json"') != 1:
        raise SemanticEnhancementError("Rendered document must contain exactly one JSON-LD script")

    if h1_count == 0:
        html = rendered_html.replace("<h2>", "<h1>", 1).replace("</h2>", "</h1>", 1)
    else:
        html = rendered_html

    graph = _schema_graph(page, intelligence)
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)
    script_start = html.index('<script type="application/ld+json">')
    content_start = html.index(">", script_start) + 1
    script_end = html.index("</script>", content_start)
    html = html[:content_start] + schema + html[script_end:]

    if html.count("<h1") != 1:
        raise SemanticEnhancementError("Semantic output must contain exactly one H1")
    return SemanticEnhancement(html=html, schema_graph=graph, primary_heading=page.sections[0].title)
