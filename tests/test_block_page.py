import copy
from pathlib import Path

from ruos.block_page import load_page_spec, render_page
from ruos.block_registry import load_library

SPEC_PATH = Path("pages/blocks/urban-investment.json")


def _spec() -> dict:
    return copy.deepcopy(load_page_spec(SPEC_PATH))


def _entry(spec: dict, block_id: str) -> dict:
    return next(entry for entry in spec["blocks"] if entry["block"] == block_id)


def _passing_sequence(spec: dict) -> list:
    return [
        _entry(spec, "hero-scroll-scene"),
        _entry(spec, "opportunity-section"),
        _entry(spec, "products-section"),
        _entry(spec, "assessment-section"),
        _entry(spec, "proof-section-final"),
        _entry(spec, "process-section-final"),
        _entry(spec, "faq-section-final"),
        _entry(spec, "review-gate"),
    ]


def test_a_page_that_pulls_in_a_vendor_library_gets_a_module_script() -> None:
    """_foundation declares vendor:["motion"], so every real page needs type=module
    for its behavior.js `import` statement to resolve in the browser."""
    spec = _spec()
    spec["blocks"] = _passing_sequence(spec)
    page = render_page(spec, load_library())
    assert '<script type="module" src="assets/behavior.js"></script>' in page.html
    assert '<script src="assets/behavior.js" defer></script>' not in page.html


def test_the_written_script_actually_imports_the_vendored_library() -> None:
    page_script = load_library().get("_foundation").script
    assert page_script.startswith('import { scroll } from "./motion.min.mjs";')
