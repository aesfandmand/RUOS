import json
from pathlib import Path

from ruos.component_resolver import resolve_components
from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.render import render_document
from ruos.semantic_enhancer import enhance_semantics
from ruos.spec_loader import load_page_spec


def _enhanced():
    page = load_page_spec(Path("pages/structures.json"))
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    components = resolve_components(page)
    return page, enhance_semantics(page, intelligence, render_document(page, components))


def test_semantic_output_has_one_h1_and_four_schema_nodes() -> None:
    page, result = _enhanced()

    assert result.html.count("<h1") == 1
    assert result.html.count("<h2") == len(page.sections) - 1
    assert result.primary_heading == page.sections[0].title
    assert [node["@type"] for node in result.schema_graph] == [
        "WebPage",
        "BreadcrumbList",
        "ItemList",
        "FAQPage",
    ]


def test_schema_json_is_embedded_and_extractable() -> None:
    _, result = _enhanced()
    marker = '<script type="application/ld+json">'
    start = result.html.index(marker) + len(marker)
    end = result.html.index("</script>", start)
    schema = json.loads(result.html[start:end])

    assert schema["@context"] == "https://schema.org"
    assert len(schema["@graph"]) == 4
    faq = next(node for node in schema["@graph"] if node["@type"] == "FAQPage")
    item_list = next(node for node in schema["@graph"] if node["@type"] == "ItemList")
    assert len(faq["mainEntity"]) == 4
    assert len(item_list["itemListElement"]) >= 3
    assert all(item["name"] for item in item_list["itemListElement"])
