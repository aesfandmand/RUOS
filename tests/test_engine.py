from pathlib import Path

from ruos.compiler import compile_page
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


def test_structures_build_passes(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    result = compile_page(
        page,
        BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True),
    )

    assert result.passed
    assert (result.output_dir / "index.html").exists()
    assert (result.output_dir / "assets/styles.css").exists()
    assert (result.output_dir / "assets/runtime.js").exists()
    assert (result.output_dir / "build-manifest.json").exists()
    assert len(result.gates) == 10
