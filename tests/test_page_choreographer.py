from pathlib import Path

from ruos.compiler import compile_page
from ruos.models import BuildContext
from ruos.page_choreographer import choreograph_page
from ruos.spec_loader import load_page_spec


def test_structures_choreography_is_deterministic() -> None:
    page = load_page_spec(Path("pages/structures.json"))
    source = ("<body><section id=\"story\"><div></div></section><section id=\"knowledge\">"
              "<div class=\"ruos-hero-art\" aria-hidden=\"true\"></div>"
              "<div class=\"ruos-decision-console\"></div></body>")
    first = choreograph_page(page, source, "base", "runtime")
    second = choreograph_page(page, source, "base", "runtime")
    assert first == second
    assert "ruos-choreographed" in first[0]
    assert "ruos-route-ribbon" in first[0]
    assert "prefers-reduced-motion:reduce" in first[1]
    assert "aria-current" in first[2]


def test_compiled_page_contains_non_card_story_choreography(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    result = compile_page(page, BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True))
    html = (result.output_dir / "index.html").read_text(encoding="utf-8")
    css = (result.output_dir / "assets/styles.css").read_text(encoding="utf-8")
    runtime = (result.output_dir / "assets/runtime.js").read_text(encoding="utf-8")
    assert 'body class="ruos-choreographed"' in html
    assert "ruos-story-aside" in html
    assert "ruos-hero-meta" in html
    assert "ruos-route-ribbon" in html
    assert "#knowledge .ruos-items{display:flex" in css
    assert "chapterObserver" in runtime
    assert "prefers-reduced-motion: reduce" in runtime
