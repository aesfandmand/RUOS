from pathlib import Path

import yaml

from ruos.page_selector import select_candidates, select_next


def _write_registries(root: Path, entities: list[dict], structures: list[dict] | None = None) -> None:
    (root / "architecture-entity-registry-v2.1.yaml").write_text(
        yaml.dump({"records": entities}, allow_unicode=True), encoding="utf-8")
    (root / "structure-page-registry-v2.1.yaml").write_text(
        yaml.dump({"records": structures or []}, allow_unicode=True), encoding="utf-8")


def _entity(**overrides) -> dict:
    base = {
        "id": "ENT-001",
        "commercial_status": "ACTIVE",
        "publication_status": "INDEX",
        "indexability": "index",
        "url_candidate": "/example/",
        "url_status": "KEEP",
        "page_level": "LANDING",
        "page_type": "SERVICE_LANDING",
    }
    base.update(overrides)
    return base


def test_a_commercially_inactive_entity_is_skipped(tmp_path: Path) -> None:
    _write_registries(tmp_path, [_entity(commercial_status="RESEARCH")])
    candidates, skipped = select_candidates(tmp_path, tmp_path)
    assert candidates == ()
    assert "not ACTIVE" in skipped[0].reason


def test_an_entity_with_no_concrete_url_is_skipped(tmp_path: Path) -> None:
    _write_registries(tmp_path, [_entity(url_candidate="PENDING", url_status="PENDING_AUDIT")])
    candidates, skipped = select_candidates(tmp_path, tmp_path)
    assert candidates == ()
    assert "no concrete URL" in skipped[0].reason


def test_a_ready_entity_is_the_top_candidate(tmp_path: Path) -> None:
    _write_registries(tmp_path, [_entity()])
    candidates, _ = select_candidates(tmp_path, tmp_path)
    assert len(candidates) == 1
    assert candidates[0].slug == "example"
    assert candidates[0].source_id == "ENT-001"


def test_locked_url_status_outranks_pending_audit(tmp_path: Path) -> None:
    _write_registries(tmp_path, [
        _entity(id="ENT-PENDING", url_candidate="/pending/", url_status="PENDING_AUDIT"),
        _entity(id="ENT-KEEP", url_candidate="/keep/", url_status="KEEP"),
    ])
    candidates, _ = select_candidates(tmp_path, tmp_path)
    assert [c.source_id for c in candidates] == ["ENT-KEEP", "ENT-PENDING"]


def test_a_structure_slug_template_expands_against_the_structure_registry(tmp_path: Path) -> None:
    _write_registries(
        tmp_path,
        [_entity(id="STR-DETAIL", url_candidate="/structures/{structure-slug}/", url_status="CANONICAL_PATTERN")],
        structures=[
            {"id": "STR-001", "name_fa": "بیلبورد", "family": "بیلبورد", "url": "/structures/billboard/", "route": "x"},
            {"id": "STR-002", "name_fa": "لایت‌باکس", "family": "لایت‌باکس", "url": "/structures/lightbox/", "route": "x"},
        ],
    )
    candidates, _ = select_candidates(tmp_path, tmp_path)
    assert {c.slug for c in candidates} == {"billboard", "lightbox"}
    assert all(c.source_kind == "structure" for c in candidates)


def test_an_unexpandable_template_is_skipped_not_guessed(tmp_path: Path) -> None:
    _write_registries(tmp_path, [
        _entity(id="PRJ-DETAIL", url_candidate="/projects/{project-slug}/", url_status="CANONICAL_PATTERN")
    ])
    candidates, skipped = select_candidates(tmp_path, tmp_path)
    assert candidates == ()
    assert "template" in skipped[0].reason


def test_a_page_with_an_authored_spec_but_no_output_is_still_a_candidate(tmp_path: Path) -> None:
    """An authored content spec means the page is ready to compose, not that it is done."""
    _write_registries(tmp_path, [_entity(url_candidate="/example/")])
    spec_dir = tmp_path / "pages" / "blocks"
    spec_dir.mkdir(parents=True)
    (spec_dir / "example.json").write_text("{}", encoding="utf-8")
    candidates, _ = select_candidates(tmp_path, tmp_path)
    assert len(candidates) == 1
    assert candidates[0].slug == "example"


def test_a_page_that_has_already_been_generated_is_excluded(tmp_path: Path) -> None:
    _write_registries(tmp_path, [_entity(url_candidate="/example/")])
    output_dir = tmp_path / "dist" / "example"
    output_dir.mkdir(parents=True)
    (output_dir / "index.html").write_text("<html></html>", encoding="utf-8")
    candidates, skipped = select_candidates(tmp_path, tmp_path)
    assert candidates == ()
    assert any("already generated" in s.reason for s in skipped)


def test_select_next_returns_none_when_nothing_is_buildable(tmp_path: Path) -> None:
    _write_registries(tmp_path, [_entity(commercial_status="FUTURE")])
    assert select_next(tmp_path, tmp_path) is None


def test_select_next_returns_the_top_ranked_candidate(tmp_path: Path) -> None:
    _write_registries(tmp_path, [
        _entity(id="ENT-A", url_candidate="/a/", page_level="LANDING"),
        _entity(id="ENT-B", url_candidate="/b/", page_level="PILLAR/HUB"),
    ])
    top = select_next(tmp_path, tmp_path)
    assert top is not None
    assert top.source_id == "ENT-B"
