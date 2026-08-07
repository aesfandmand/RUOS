from ruos.prebuild_intelligence import enforce_prebuild_dossier, validate_prebuild_dossier


def _valid():
    return {
        "target_market": "ir",
        "target_language": "fa",
        "iranian_query_set": ["استرابورد چیست", "خرید استرابورد"],
        "serp_landscape": ["example"],
        "search_intent_map": {"informational": ["استرابورد چیست"]},
        "funnel_role": "consideration",
        "conversion_goal": "route-to-relevant-journey",
        "pillar": "structures",
        "cluster": "outdoor-structures",
        "title_strategy": "evidence-backed",
        "h1": "استرابورد",
        "heading_architecture": ["H2"],
        "discover_hook": "visual-first factual hook",
        "faq_and_paa_plan": ["question"],
        "entity_graph": {"entity": "starboard"},
        "schema_plan": ["Product"],
        "capability_evidence_plan": ["proof"],
        "internal_linking_plan": ["/structures"],
        "related_blog_and_video_plan": ["video"],
        "writer_profile": {"id": "approved"},
        "iranian_editor_profile": {"id": "approved"},
        "voice_constraints": ["no fake urgency"],
        "live_library_research_report": {"status": "verified"},
        "selected_technology_stack": ["selected"],
        "aspirational_reference_translation": ["motion principle"],
        "motion_direction": "purposeful",
        "conversion_instrumentation_plan": ["cta_click"],
    }


def test_valid_prebuild_dossier_passes():
    dossier = _valid()
    assert validate_prebuild_dossier(dossier).passed
    enforce_prebuild_dossier(dossier)


def test_missing_editorial_profile_fails():
    dossier = _valid()
    dossier.pop("iranian_editor_profile")
    report = validate_prebuild_dossier(dossier)
    assert not report.passed
    assert "iranian_editor_profile" in report.missing


def test_persian_query_is_required():
    dossier = _valid()
    dossier["iranian_query_set"] = ["starboard billboard"]
    report = validate_prebuild_dossier(dossier)
    assert not report.passed
    assert "iranian_query_set:requires_persian_query" in report.invalid
