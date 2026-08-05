from dataclasses import replace
from pathlib import Path

import pytest

from ruos.content_composer import ContentCompositionError, compose_content
from ruos.spec_loader import load_page_spec


def test_content_plan_is_semantic_and_deterministic() -> None:
    page = load_page_spec(Path("pages/structures.json"))
    first = compose_content(page)
    second = compose_content(page)

    assert first.fingerprint_payload() == second.fingerprint_payload()
    assert first.language == "fa"
    assert first.direction == "rtl"
    assert first.blocks[0].heading_level == 1
    assert sum(block.heading_level == 1 for block in first.blocks) == 1
    assert first.blocks[-1].role == "conversion"
    assert first.primary_intent == "qualified-conversation"
    assert first.blocks[2].entities == ("ایندور", "اوتدور", "دیجیتال")


def test_unpaired_cta_is_rejected() -> None:
    page = load_page_spec(Path("pages/structures.json"))
    broken = replace(page.sections[0], cta_href="")
    invalid = replace(page, sections=(broken,) + page.sections[1:])

    with pytest.raises(ContentCompositionError, match="CTA label and href must be paired"):
        compose_content(invalid)


def test_thin_production_copy_is_rejected() -> None:
    page = load_page_spec(Path("pages/structures.json"))
    broken = replace(page.sections[1], body="کوتاه")
    invalid = replace(page, sections=(page.sections[0], broken) + page.sections[2:])

    with pytest.raises(ContentCompositionError, match="too thin"):
        compose_content(invalid)
