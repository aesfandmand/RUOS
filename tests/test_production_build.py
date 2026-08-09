from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from ruos.discovery_verifier import VerifiedSearchDiscovery
from ruos.models import BuildContext, BuildResult
from ruos.production_build import (
    ProductionBuildError,
    compile_production_page,
    verify_production_discovery,
    verify_production_research,
)
from ruos.research_verifier import VerifiedResearchEvidence
from ruos.spec_loader import load_page_spec


def _context(tmp_path: Path, *, required: bool = True, discovery: bool = False) -> BuildContext:
    return BuildContext(
        project_root=tmp_path,
        output_root=tmp_path / "dist",
        strict=False,
        require_live_research=required,
        research_snapshot_root=tmp_path / ".ruos" / "research",
        require_search_discovery=discovery,
        discovery_snapshot_root=tmp_path / ".ruos" / "discovery",
    )


def _with_prebuild(page):
    metadata = dict(page.metadata)
    metadata["prebuild_intelligence"] = {
        "target_market": "ir",
        "target_language": "fa",
        "iranian_query_set": ["سازه‌های تبلیغاتی"],
        "serp_landscape": ["verified landscape"],
        "search_intent_map": ["commercial investigation"],
        "funnel_role": "discover-compare-route",
        "conversion_goal": "qualified conversation",
        "pillar": "advertising structures",
        "cluster": "structure catalog",
        "title_strategy": "query-led",
        "h1": "سازه‌های تبلیغاتی",
        "heading_architecture": ["discover", "compare", "decide"],
        "discover_hook": "choose the right structure",
        "faq_and_paa_plan": ["types", "selection", "buying"],
        "entity_graph": ["structure", "indoor", "outdoor"],
        "schema_plan": ["WebPage", "ItemList", "FAQPage"],
        "capability_evidence_plan": ["real projects", "technical evidence"],
        "internal_linking_plan": ["indoor", "outdoor", "investment"],
        "related_blog_and_video_plan": ["structure guides"],
        "writer_profile": "specialist Persian B2B writer",
        "iranian_editor_profile": "senior Iranian editor",
        "voice_constraints": ["clear", "specific", "non-translated"],
        "live_library_research_report": ["verified sources"],
        "selected_technology_stack": ["semantic HTML", "CSS", "JavaScript"],
        "aspirational_reference_translation": ["reference-led, not copied"],
        "motion_direction": ["semantic progressive reveal"],
        "conversion_instrumentation_plan": ["primary CTA", "qualified conversation"],
    }
    return replace(page, metadata=metadata)


def test_production_api_requires_live_research_flag(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    with pytest.raises(ProductionBuildError, match="requires live research"):
        verify_production_research(page, _context(tmp_path, required=False))


def test_production_api_requires_snapshot_root(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    context = BuildContext(tmp_path, tmp_path / "dist", require_live_research=True)
    with pytest.raises(ProductionBuildError, match="snapshot root"):
        verify_production_research(page, context)


def test_production_discovery_requires_flag(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    with pytest.raises(ProductionBuildError, match="requires search discovery"):
        verify_production_discovery(page, _context(tmp_path))


def test_production_compile_verifies_before_compiling_and_injects_provenance(tmp_path: Path, monkeypatch) -> None:
    page = _with_prebuild(load_page_spec(Path("pages/structures.json")))
    context = _context(tmp_path)
    calls: list[str] = []
    verified = VerifiedResearchEvidence(page.slug, "a" * 64, "2026-08-06T04:00:00Z", 7, ("one",), 1)
    evidence = SimpleNamespace(payload=lambda: {"source_id": "one", "origin": "live-web"})
    snapshot = SimpleNamespace(sha256=verified.snapshot_sha256, evidence=(evidence,))

    def fake_verify(page_arg, snapshot_path, *, max_age_days):
        calls.append("verify")
        assert snapshot_path == context.research_snapshot_root / "structures.json"
        return verified

    def fake_load(snapshot_path):
        calls.append("load")
        return snapshot

    def fake_compile(page_arg, context_arg):
        calls.append("compile")
        assert page_arg.metadata["verified_live_research"]["status"] == "verified-live"
        return BuildResult(page_arg, context_arg.output_root / page_arg.slug, (), ())

    monkeypatch.setattr("ruos.production_build.require_verified_live_research", fake_verify)
    monkeypatch.setattr("ruos.production_build.load_snapshot", fake_load)
    monkeypatch.setattr("ruos.production_build.compile_page", fake_compile)

    result, returned_evidence, discovery = compile_production_page(page, context, max_age_days=7)
    assert calls == ["verify", "load", "compile"]
    assert result.page.slug == "structures"
    assert returned_evidence == verified
    assert discovery is None


def test_production_compile_injects_verified_discovery(tmp_path: Path, monkeypatch) -> None:
    page = _with_prebuild(load_page_spec(Path("pages/structures.json")))
    context = _context(tmp_path, discovery=True)
    research = VerifiedResearchEvidence(page.slug, "a" * 64, "2026-08-06T04:00:00Z", 7, ("one",), 1)
    discovery = VerifiedSearchDiscovery("brave", "سازه‌های تبلیغاتی", "ir", "fa", "2026-08-06T04:00:00Z", 5, 1, "b" * 64)
    research_snapshot = SimpleNamespace(sha256=research.snapshot_sha256, evidence=())
    result_item = SimpleNamespace(payload=lambda: {"rank": 1, "title": "نتیجه", "url": "https://example.com", "snippet": ""})
    discovery_snapshot = SimpleNamespace(sha256=discovery.sha256, results=(result_item,))

    monkeypatch.setattr("ruos.production_build.verify_production_research", lambda *args, **kwargs: research)
    monkeypatch.setattr("ruos.production_build.verify_production_discovery", lambda *args, **kwargs: discovery)
    monkeypatch.setattr("ruos.production_build.load_snapshot", lambda *args, **kwargs: research_snapshot)
    monkeypatch.setattr("ruos.production_build.load_discovery", lambda *args, **kwargs: discovery_snapshot)

    def fake_compile(page_arg, context_arg):
        payload = page_arg.metadata["verified_search_discovery"]
        provenance = page_arg.metadata["verified_live_research"]
        assert payload["status"] == "verified-search-discovery"
        assert payload["results"][0]["rank"] == 1
        assert provenance["status"] == "verified-live-with-search-discovery"
        assert provenance["search_discovery"] == payload
        return BuildResult(page_arg, context_arg.output_root / page_arg.slug, (), ())

    monkeypatch.setattr("ruos.production_build.compile_page", fake_compile)
    _, _, returned = compile_production_page(page, context)
    assert returned == discovery


def test_production_compile_rejects_snapshot_changed_after_verification(tmp_path: Path, monkeypatch) -> None:
    page = _with_prebuild(load_page_spec(Path("pages/structures.json")))
    context = _context(tmp_path)
    verified = VerifiedResearchEvidence(page.slug, "a" * 64, "2026-08-06T04:00:00Z", 7, ("one",), 1)
    monkeypatch.setattr("ruos.production_build.require_verified_live_research", lambda *args, **kwargs: verified)
    monkeypatch.setattr("ruos.production_build.load_snapshot", lambda *args, **kwargs: SimpleNamespace(sha256="c" * 64, evidence=()))
    with pytest.raises(ProductionBuildError, match="changed before compilation"):
        compile_production_page(page, context)
