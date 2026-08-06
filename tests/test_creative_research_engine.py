import json
from pathlib import Path

from ruos.competitive_intelligence import build_competitive_intelligence
from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.design_brief import compile_design_brief
from ruos.models import BuildContext
from ruos.pattern_intelligence import select_patterns
from ruos.query_intelligence import build_query_intelligence
from ruos.research_studio import conduct_research
from ruos.spec_loader import load_page_spec
from ruos.voice_studio import select_voice
from ruos.compiler import compile_page


def _research_stack():
    page = load_page_spec(Path("pages/structures.json"))
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    research = conduct_research(page, intelligence)
    queries = build_query_intelligence(page, research, intelligence)
    competition = build_competitive_intelligence(page, research)
    patterns = select_patterns(page, research, queries, competition)
    voice = select_voice(page)
    brief = compile_design_brief(page, research, queries, competition, patterns, voice)
    return page, research, queries, competition, patterns, brief


def test_query_intelligence_clusters_real_commercial_routes() -> None:
    _, _, queries, _, _, _ = _research_stack()
    names = {cluster.name for cluster in queries.clusters}
    assert "commercial" in names
    assert "investment" in names
    assert "comparison" in names
    assert queries.primary_query == "سازه‌های تبلیغاتی"
    assert queries.evidence_source_ids
    assert len(queries.sha256) == 64


def test_pattern_selection_is_evidence_backed_and_deterministic() -> None:
    first = _research_stack()[4]
    second = _research_stack()[4]
    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert {item.kind for item in first.selected} >= {"storytelling", "interaction", "motion"}
    assert all(item.score >= 75 for item in first.selected)
    assert all(item.source_id for item in first.selected)


def test_design_brief_carries_source_hashes_and_non_copying_constraints() -> None:
    _, research, queries, competition, patterns, brief = _research_stack()
    assert brief.source_hashes == {
        "research": research.sha256,
        "query_intelligence": queries.sha256,
        "competitive_intelligence": competition.sha256,
        "pattern_intelligence": patterns.sha256,
        "voice": brief.source_hashes["voice"],
    }
    assert "No copied layouts, code, copy or branded assets" in brief.constraints
    assert "Reduced-motion equivalent experience" in brief.constraints
    assert brief.voice_id == "strategic-editorial-fa"


def test_build_publishes_phase_one_artifacts(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    result = compile_page(page, BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True))
    expected = (
        "query-intelligence.json",
        "competitive-analysis.json",
        "pattern-selection.json",
        "design-brief.json",
    )
    for name in expected:
        path = result.output_dir / "studio" / name
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8"))

    manifest = json.loads((result.output_dir / "studio/manifest.json").read_text(encoding="utf-8"))
    pipeline = manifest["pipeline"]
    assert pipeline.index("query-intelligence.json") < pipeline.index("creative-direction.json")
    assert pipeline.index("design-brief.json") < pipeline.index("creative-direction.json")
    assert all(name in manifest["artifacts"] for name in expected)
