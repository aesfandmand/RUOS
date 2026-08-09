from pathlib import Path

from ruos.cie_build import generate_cie_blueprint
from ruos.cie_providers import CONFLICT_PRIORITY, DEFAULT_PROVIDERS
from ruos.spec_loader import load_page_spec


def test_provider_set_matches_orchestration_domains():
    assert {provider.provider_id for provider in DEFAULT_PROVIDERS} == {
        "reference_visual_analyst",
        "motion_interaction_analyst",
        "ux_journey_analyst",
        "industrial_product_analyst",
        "brand_editorial_analyst",
        "performance_accessibility_analyst",
        "competitive_differentiation_analyst",
        "seo_ai_knowledge_graph_analyst",
    }
    assert CONFLICT_PRIORITY[:4] == (
        "locked_project_rules",
        "user_and_business_goal",
        "evidence_and_truth",
        "accessibility_and_mobile",
    )


def test_structures_blueprint_contains_ready_provider_synthesis():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    pipeline = blueprint["provider_pipeline"]
    assert pipeline["synthesis"]["status"] == "ready"
    assert pipeline["synthesis"]["blockers"] == []
    assert pipeline["conflicts"] == []
    assert pipeline["confidence"] >= 0.9
    assert pipeline["quorum"]["passed"] is True
    assert pipeline["provenance_passed"] is True
    assert len(pipeline["providers"]) == 8
    assert "industrial_product_analyst" in pipeline["required_providers"]
    assert all(item["page_specific_recommendations"] for item in pipeline["providers"])
    assert all(item["provenance"] for item in pipeline["providers"])
