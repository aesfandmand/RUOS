import hashlib
import json
from pathlib import Path

from ruos.compiler import compile_page
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


EXPECTED_STUDIO_FILES = (
    "research.json",
    "query-intelligence.json",
    "competitive-analysis.json",
    "pattern-selection.json",
    "knowledge-graph.json",
    "component-selection.json",
    "design-brief.json",
    "creative-direction.json",
    "art-direction.json",
    "ux-plan.json",
    "ui-plan.json",
    "motion-plan.json",
    "content-plan.json",
    "seo-plan.json",
    "cro-plan.json",
    "design-critique.json",
    "agency-review.json",
)


def _build(tmp_path: Path):
    page = load_page_spec(Path("pages/structures.json"))
    return compile_page(page, BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True))


def test_compiler_publishes_complete_studio_bundle(tmp_path: Path) -> None:
    result = _build(tmp_path)
    studio = result.output_dir / "studio"
    manifest = json.loads((studio / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["pipeline"] == list(EXPECTED_STUDIO_FILES)
    for name in EXPECTED_STUDIO_FILES:
        path = studio / name
        assert path.exists()
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload
        expected = manifest["artifacts"][name]["sha256"]
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == expected

    graph = json.loads((studio / "knowledge-graph.json").read_text(encoding="utf-8"))
    selection = json.loads((studio / "component-selection.json").read_text(encoding="utf-8"))
    critique = json.loads((studio / "design-critique.json").read_text(encoding="utf-8"))
    assert graph["page_slug"] == "structures"
    assert graph["entities"]
    assert graph["relations"]
    assert selection["page_slug"] == "structures"
    assert len(selection["decisions"]) == 6
    assert all(decision["score"] >= 88 for decision in selection["decisions"])
    assert critique["page_slug"] == "structures"
    assert len(critique["findings"]) == 10
    assert critique["release_recommendation"] != "reject"


def test_agency_review_requires_unanimous_specialist_approval(tmp_path: Path) -> None:
    result = _build(tmp_path)
    review = json.loads((result.output_dir / "studio/agency-review.json").read_text(encoding="utf-8"))
    build_manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))

    assert review["unanimous"] is True
    assert review["publishable"] is True
    assert review["total_score"] >= 88
    assert len(review["verdicts"]) == 10
    assert all(verdict["passed"] for verdict in review["verdicts"])
    assert len(review["research"]["knowledge_graph_sha256"]) == 64
    assert len(review["research"]["component_selection_sha256"]) == 64
    assert len(review["design_critique_sha256"]) == 64
    assert review["design_critique_recommendation"] != "reject"
    assert build_manifest["passed"] is True
    assert len(build_manifest["studio_sha256"]) == 64
    assert build_manifest["studio"]["artifacts"]["agency-review.json"]["payload"]["publishable"] is True


def test_studio_files_are_reproducible(tmp_path: Path) -> None:
    first = _build(tmp_path)
    first_hashes = {
        name: hashlib.sha256((first.output_dir / "studio" / name).read_bytes()).hexdigest()
        for name in ("manifest.json",) + EXPECTED_STUDIO_FILES
    }
    second = _build(tmp_path)
    second_hashes = {
        name: hashlib.sha256((second.output_dir / "studio" / name).read_bytes()).hexdigest()
        for name in ("manifest.json",) + EXPECTED_STUDIO_FILES
    }
    assert second_hashes == first_hashes
