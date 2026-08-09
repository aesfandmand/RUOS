import json
from pathlib import Path

import yaml

from ruos import generate as generate_module
from ruos.design_approach import MATCHED, DesignApproach, DesignApproachResult
from ruos.generate import (
    COMPOSE_REJECTED,
    CONTENT_NOT_YET_AUTHORED,
    DESIGN_NOT_YET_DESIGNED,
    GENERATED,
    generate_next,
)

REAL_PROJECT_ROOT = Path(".")
REAL_SPEC = json.loads(Path("pages/blocks/urban-investment.json").read_text(encoding="utf-8"))


def _write_registry(registry_root: Path, entities: list[dict]) -> None:
    registry_root.mkdir(parents=True, exist_ok=True)
    (registry_root / "architecture-entity-registry-v2.1.yaml").write_text(
        yaml.dump({"records": entities}, allow_unicode=True), encoding="utf-8")
    (registry_root / "structure-page-registry-v2.1.yaml").write_text(
        yaml.dump({"records": []}), encoding="utf-8")


def _entity(**overrides) -> dict:
    base = {
        "id": "TEST-001",
        "commercial_status": "ACTIVE",
        "publication_status": "INDEX",
        "indexability": "index",
        "url_candidate": "/test-page/",
        "url_status": "KEEP",
        "page_level": "LANDING",
        "page_type": "TEST_PAGE_TYPE",
    }
    base.update(overrides)
    return base


def _mini_composable_spec(slug: str) -> dict:
    """A real two-block sequence (open + close) known to pass the composer."""
    spec = dict(REAL_SPEC)
    spec["slug"] = slug
    spec["blocks"] = [b for b in REAL_SPEC["blocks"] if b["block"] in ("hero-scroll-scene", "review-gate")]
    return spec


def test_a_page_type_with_no_design_approach_is_reported_and_skipped(tmp_path: Path) -> None:
    registry_root = tmp_path / "registry"
    _write_registry(registry_root, [_entity()])

    report = generate_next(project_root=REAL_PROJECT_ROOT, registry_root=registry_root,
                            spec_root=str(tmp_path / "pages" / "blocks"))

    assert report.generated_page is None
    assert report.attempts[0].stage == DESIGN_NOT_YET_DESIGNED


def test_a_matched_design_with_no_authored_spec_is_reported_and_skipped(tmp_path: Path, monkeypatch) -> None:
    registry_root = tmp_path / "registry"
    _write_registry(registry_root, [_entity()])
    fake_approach = DesignApproach(
        id="fake-approach", name="fake", block_sequence=("hero-scroll-scene", "review-gate"),
        source_reference="test", note="test",
    )
    monkeypatch.setattr(generate_module, "select_design_approach",
                         lambda page_type: DesignApproachResult(page_type or "", MATCHED, fake_approach, "matched"))

    report = generate_next(project_root=REAL_PROJECT_ROOT, registry_root=registry_root,
                            spec_root=str(tmp_path / "pages" / "blocks"))

    assert report.generated_page is None
    assert report.attempts[0].stage == CONTENT_NOT_YET_AUTHORED


def test_a_matched_design_whose_sequence_the_composer_rejects_is_reported(tmp_path: Path, monkeypatch) -> None:
    registry_root = tmp_path / "registry"
    _write_registry(registry_root, [_entity()])
    spec_dir = tmp_path / "pages" / "blocks"
    spec_dir.mkdir(parents=True)
    (spec_dir / "test-page.json").write_text(json.dumps(REAL_SPEC), encoding="utf-8")

    rejected_approach = DesignApproach(
        id="v16-full", name="full v16 sequence",
        block_sequence=tuple(b["block"] for b in REAL_SPEC["blocks"]),
        source_reference="test", note="known to fail the shape rules",
    )
    monkeypatch.setattr(generate_module, "select_design_approach",
                         lambda page_type: DesignApproachResult(page_type or "", MATCHED, rejected_approach, "matched"))

    report = generate_next(project_root=REAL_PROJECT_ROOT, registry_root=registry_root, spec_root=str(spec_dir))

    assert report.generated_page is None
    assert report.attempts[0].stage == COMPOSE_REJECTED
    assert "repeated pattern" in report.attempts[0].reason


def test_a_fully_ready_candidate_is_composed_end_to_end(tmp_path: Path, monkeypatch) -> None:
    registry_root = tmp_path / "registry"
    _write_registry(registry_root, [_entity(url_candidate="/mini-test-page/")])
    spec_dir = tmp_path / "pages" / "blocks"
    spec_dir.mkdir(parents=True)
    (spec_dir / "mini-test-page.json").write_text(
        json.dumps(_mini_composable_spec("mini-test-page")), encoding="utf-8")

    small_approach = DesignApproach(
        id="mini-approach", name="mini", block_sequence=("hero-scroll-scene", "review-gate"),
        source_reference="test", note="test",
    )
    monkeypatch.setattr(generate_module, "select_design_approach",
                         lambda page_type: DesignApproachResult(page_type or "", MATCHED, small_approach, "matched"))

    report = generate_next(project_root=REAL_PROJECT_ROOT, registry_root=registry_root, spec_root=str(spec_dir))

    assert report.generated_page is not None
    assert report.generated_page.slug == "mini-test-page"
    assert report.attempts[-1].stage == GENERATED
    assert [b.block_id for b in report.generated_page.composed.blocks] == ["hero-scroll-scene", "review-gate"]


def test_generate_walks_past_a_blocked_candidate_to_a_ready_one(tmp_path: Path, monkeypatch) -> None:
    registry_root = tmp_path / "registry"
    _write_registry(registry_root, [
        _entity(id="BLOCKED-001", url_candidate="/blocked/", page_type="NO_APPROACH_TYPE"),
        _entity(id="READY-001", url_candidate="/mini-test-page/", page_type="TEST_PAGE_TYPE"),
    ])
    spec_dir = tmp_path / "pages" / "blocks"
    spec_dir.mkdir(parents=True)
    (spec_dir / "mini-test-page.json").write_text(
        json.dumps(_mini_composable_spec("mini-test-page")), encoding="utf-8")

    small_approach = DesignApproach(
        id="mini-approach", name="mini", block_sequence=("hero-scroll-scene", "review-gate"),
        source_reference="test", note="test",
    )

    def fake_select(page_type):
        if page_type == "TEST_PAGE_TYPE":
            return DesignApproachResult(page_type, MATCHED, small_approach, "matched")
        return DesignApproachResult(page_type or "", "not_yet_designed", None, "no approach")

    monkeypatch.setattr(generate_module, "select_design_approach", fake_select)

    report = generate_next(project_root=REAL_PROJECT_ROOT, registry_root=registry_root, spec_root=str(spec_dir))

    assert report.generated_page is not None
    assert report.attempts[0].candidate.source_id == "BLOCKED-001"
    assert report.attempts[0].stage == DESIGN_NOT_YET_DESIGNED
    assert report.attempts[-1].candidate.source_id == "READY-001"
    assert report.attempts[-1].stage == GENERATED
