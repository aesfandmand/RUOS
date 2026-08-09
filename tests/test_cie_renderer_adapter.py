import hashlib
import json
from pathlib import Path

from ruos.cie_build import compile_page_with_cie
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


def test_cie_contract_drives_real_html_css_and_runtime_natively(tmp_path):
    page = load_page_spec(Path("pages/structures.json"))
    context = BuildContext(project_root=Path("."), output_root=tmp_path, strict=False)
    result = compile_page_with_cie(page, context)

    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    css = (result.output_dir / "assets/styles.css").read_text(encoding="utf-8")
    runtime = (result.output_dir / "assets/runtime.js").read_text(encoding="utf-8")

    assert 'data-cie-renderer="native-contract"' in html
    assert html.count('data-cie-contract="native"') == len(page.sections)
    assert 'data-cie-variant=' in html
    assert 'data-cie-stage' in html
    assert 'data-cie-industrial-anatomy' in html
    assert 'data-cie-hotspot="foundation"' in html
    assert "CIE native contract-driven renderer" in css
    assert 'min-inline-size:44px' in css
    assert "prefers-reduced-motion:reduce" in css
    assert "RUOS_CIE_NATIVE" in runtime
    assert "dataset.cieRuntime='native'" in runtime
    assert "data-cie-hotspot" in runtime


def test_cie_native_renderer_manifest_hashes_are_canonical(tmp_path):
    page = load_page_spec(Path("pages/structures.json"))
    context = BuildContext(project_root=Path("."), output_root=tmp_path, strict=False)
    result = compile_page_with_cie(page, context)
    manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))

    assert manifest["cie_native_renderer"]["status"] == "native"
    assert manifest["cie_native_renderer"]["section_count"] == len(page.sections)
    assert manifest["cie_implementation_contract_sha256"]
    for relative in ("index.html", "assets/styles.css", "assets/runtime.js", "assets/cie-implementation-contract.json"):
        digest = hashlib.sha256((result.output_dir / relative).read_bytes()).hexdigest()
        assert manifest["sha256"][relative] == digest

    build_id = (result.output_dir / ".ruos-build").read_text(encoding="utf-8").strip()
    assert build_id == manifest["build_id"]


def test_blueprint_records_native_renderer_status(tmp_path):
    page = load_page_spec(Path("pages/structures.json"))
    context = BuildContext(project_root=Path("."), output_root=tmp_path, strict=False)
    result = compile_page_with_cie(page, context)
    blueprint = json.loads((result.output_dir / "creative-blueprint.json").read_text(encoding="utf-8"))

    assert blueprint["renderer"]["status"] == "native-contract-driven"
    assert blueprint["renderer"]["legacy_adapter_required"] is False
    assert "assets/cie-implementation-contract.json" in blueprint["renderer"]["target_artifacts"]
