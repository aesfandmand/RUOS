import hashlib
import json
from pathlib import Path

from ruos.cie_build import compile_page_with_cie
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


def test_cie_contract_is_bound_to_real_html_css_and_runtime(tmp_path):
    page = load_page_spec(Path("pages/structures.json"))
    context = BuildContext(project_root=Path("."), output_root=tmp_path, strict=False)
    result = compile_page_with_cie(page, context)

    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    css = (result.output_dir / "assets/styles.css").read_text(encoding="utf-8")
    runtime = (result.output_dir / "assets/runtime.js").read_text(encoding="utf-8")

    assert 'data-cie-renderer="implementation-contract"' in html
    assert html.count('data-cie-contract="applied"') == len(page.sections)
    assert 'data-cie-variant=' in html
    assert "CIE implementation contract adapter" in css
    assert 'min-inline-size:44px' in css
    assert "prefers-reduced-motion:reduce" in css
    assert "RUOS_CIE_IMPLEMENTATION" in runtime
    assert "dataset.cieRuntime='bound'" in runtime


def test_cie_renderer_refreshes_build_manifest_hashes(tmp_path):
    page = load_page_spec(Path("pages/structures.json"))
    context = BuildContext(project_root=Path("."), output_root=tmp_path, strict=False)
    result = compile_page_with_cie(page, context)
    manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))

    assert manifest["cie_renderer_adapter"]["status"] == "applied"
    assert manifest["cie_renderer_adapter"]["section_count"] == len(page.sections)
    for relative in ("index.html", "assets/styles.css", "assets/runtime.js", "qa-report.json"):
        digest = hashlib.sha256((result.output_dir / relative).read_bytes()).hexdigest()
        assert manifest["sha256"][relative] == digest

    build_id = (result.output_dir / ".ruos-build").read_text(encoding="utf-8").strip()
    assert build_id == manifest["build_id"]


def test_blueprint_records_post_render_adapter_status(tmp_path):
    page = load_page_spec(Path("pages/structures.json"))
    context = BuildContext(project_root=Path("."), output_root=tmp_path, strict=False)
    result = compile_page_with_cie(page, context)
    blueprint = json.loads((result.output_dir / "creative-blueprint.json").read_text(encoding="utf-8"))

    assert blueprint["renderer_adapter"]["status"] == "applied"
    assert blueprint["renderer_adapter"]["target_artifacts"] == ["index.html", "assets/styles.css", "assets/runtime.js"]
