from ruos.cie_build import generate_cie_blueprint
from ruos.cie_providers import DEFAULT_PROVIDERS
from ruos.spec_loader import load_page_spec


def test_provider_set_covers_required_creative_domains():
    assert {provider.domain for provider in DEFAULT_PROVIDERS} == {
        "research_reference",
        "ux_storytelling",
        "visual_direction",
        "motion_interaction",
        "seo_ai_knowledge_graph",
    }


def test_structures_blueprint_contains_ready_provider_synthesis():
    page = load_page_spec("pages/structures.json")
    blueprint = generate_cie_blueprint(page)
    pipeline = blueprint["provider_pipeline"]
    assert pipeline["synthesis"]["status"] == "ready"
    assert pipeline["conflicts"] == []
    assert pipeline["confidence"] >= 0.9
    assert len(pipeline["providers"]) == 5
    assert all(item["recommendation"] for item in pipeline["providers"])
    assert all(item["rationale"] for item in pipeline["providers"])
