from pathlib import Path

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


def test_production_compile_verifies_before_compiling(tmp_path: Path, monkeypatch) -> None:
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

    def fake_verify(page_arg, snapshot_path, *, max_age_days):
        calls.append("verify")
        assert page_arg.slug == page.slug
        assert snapshot_path == context.research_snapshot_root / "structures.json"
        assert max_age_days == 7
        return verified

    def fake_compile(page_arg, context_arg):
        calls.append("compile")
        assert context_arg.strict is True
        assert context_arg.require_live_research is True
        return BuildResult(
            page=page_arg,
            output_dir=context_arg.output_root / page_arg.slug,
            files=(),
            gates=(),
        )

    monkeypatch.setattr("ruos.production_build.require_verified_live_research", fake_verify)
    monkeypatch.setattr("ruos.production_build.compile_page", fake_compile)

    result, evidence = compile_production_page(page, context, max_age_days=7)

    assert calls == ["verify", "compile"]
    assert result.page.slug == "structures"
    assert evidence == verified
