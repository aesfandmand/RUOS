from pathlib import Path
from types import SimpleNamespace

import pytest

from ruos.models import BuildContext, BuildResult
from ruos.production_build import (
    ProductionBuildError,
    compile_production_page,
    verify_production_research,
)
from ruos.research_verifier import VerifiedResearchEvidence
from ruos.spec_loader import load_page_spec


def _context(tmp_path: Path, *, required: bool = True) -> BuildContext:
    return BuildContext(
        project_root=tmp_path,
        output_root=tmp_path / "dist",
        strict=False,
        require_live_research=required,
        research_snapshot_root=tmp_path / ".ruos" / "research",
    )


def test_production_api_requires_live_research_flag(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    with pytest.raises(ProductionBuildError, match="requires live research"):
        verify_production_research(page, _context(tmp_path, required=False))


def test_production_api_requires_snapshot_root(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    context = BuildContext(
        project_root=tmp_path,
        output_root=tmp_path / "dist",
        require_live_research=True,
        research_snapshot_root=None,
    )
    with pytest.raises(ProductionBuildError, match="snapshot root"):
        verify_production_research(page, context)


def test_production_compile_verifies_before_compiling_and_injects_provenance(
    tmp_path: Path,
    monkeypatch,
) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    context = _context(tmp_path)
    calls: list[str] = []
    verified = VerifiedResearchEvidence(
        page_slug=page.slug,
        snapshot_sha256="a" * 64,
        created_at="2026-08-06T04:00:00Z",
        source_count=7,
        covered_source_ids=("one",),
        freshness_hours=1,
    )
    evidence = SimpleNamespace(payload=lambda: {
        "source_id": "one",
        "origin": "live-web",
        "fetched_at": "2026-08-06T04:00:00Z",
        "content_sha256": "b" * 64,
        "observations": ["Observed source content"],
        "inferences": [],
        "manual_claims": [],
    })
    snapshot = SimpleNamespace(
        sha256=verified.snapshot_sha256,
        evidence=(evidence,),
    )

    def fake_verify(page_arg, snapshot_path, *, max_age_days):
        calls.append("verify")
        assert page_arg.slug == page.slug
        assert snapshot_path == context.research_snapshot_root / "structures.json"
        assert max_age_days == 7
        return verified

    def fake_load(snapshot_path):
        calls.append("load")
        assert snapshot_path == context.research_snapshot_root / "structures.json"
        return snapshot

    def fake_compile(page_arg, context_arg):
        calls.append("compile")
        assert context_arg.strict is True
        assert context_arg.require_live_research is True
        provenance = page_arg.metadata["verified_live_research"]
        assert provenance["status"] == "verified-live"
        assert provenance["snapshot_sha256"] == verified.snapshot_sha256
        assert provenance["evidence"][0]["origin"] == "live-web"
        return BuildResult(
            page=page_arg,
            output_dir=context_arg.output_root / page_arg.slug,
            files=(),
            gates=(),
        )

    monkeypatch.setattr("ruos.production_build.require_verified_live_research", fake_verify)
    monkeypatch.setattr("ruos.production_build.load_snapshot", fake_load)
    monkeypatch.setattr("ruos.production_build.compile_page", fake_compile)

    result, returned_evidence = compile_production_page(page, context, max_age_days=7)

    assert calls == ["verify", "load", "compile"]
    assert result.page.slug == "structures"
    assert returned_evidence == verified


def test_production_compile_rejects_snapshot_changed_after_verification(
    tmp_path: Path,
    monkeypatch,
) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    context = _context(tmp_path)
    verified = VerifiedResearchEvidence(
        page_slug=page.slug,
        snapshot_sha256="a" * 64,
        created_at="2026-08-06T04:00:00Z",
        source_count=7,
        covered_source_ids=("one",),
        freshness_hours=1,
    )
    monkeypatch.setattr(
        "ruos.production_build.require_verified_live_research",
        lambda *args, **kwargs: verified,
    )
    monkeypatch.setattr(
        "ruos.production_build.load_snapshot",
        lambda *args, **kwargs: SimpleNamespace(sha256="c" * 64, evidence=()),
    )

    with pytest.raises(ProductionBuildError, match="changed before compilation"):
        compile_production_page(page, context)
