import json
from pathlib import Path

import pytest

from ruos.compiler import compile_page
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec
from ruos.visual_dna import VisualDNAError, available_profiles, contrast_ratio, resolve_visual_dna


def test_red_umbrella_profile_is_accessible_and_deterministic() -> None:
    dna = resolve_visual_dna("red-umbrella-v16")

    assert dna.id in available_profiles()
    assert contrast_ratio(dna.colors["color-ink"], dna.colors["color-bg"]) >= 7
    assert contrast_ratio(dna.colors["color-accent-ink"], dna.colors["color-accent"]) >= 4.5
    assert dna.css_variables() == dna.css_variables()
    assert "--font-size-display:" in dna.css_variables()


def test_unknown_profile_is_rejected() -> None:
    with pytest.raises(VisualDNAError, match="Unknown visual profile"):
        resolve_visual_dna("missing-profile")


def test_build_manifest_contains_visual_dna_fingerprint(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    result = compile_page(page, BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True))
    manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))

    assert manifest["visual_profile"] == "red-umbrella-v16"
    assert len(manifest["visual_dna_sha256"]) == 64
    assert manifest["visual_dna"]["color-accent"] == "#D21E2B"
    css = (result.output_dir / "assets/styles.css").read_text(encoding="utf-8")
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    assert "--color-accent:#D21E2B" in css
    assert "ruos-bottom-nav" in html
