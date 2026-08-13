"""content_draft.py — the deterministic gap-filler + validator for drafted
rich-section content. Covers: a clean draft passes, an uncited real claim
blocks, a dishonestly-tagged placeholder blocks, a banned superlative is a
non-blocking refinement, gap-filling only touches genuinely empty slots and
tags what it fills, and a bad block contract blocks.
"""
from __future__ import annotations

import pytest

from ruos.block_registry import load_library
from ruos.content_draft import (
    LOREM_IPSUM,
    fill_draft_gaps,
    lorem_ipsum_of_length,
    validate_draft,
)
from ruos.live_research import LiveEvidence
from ruos.research_snapshot import ResearchSnapshot

LIBRARY = load_library()

_EVIDENCE = (
    LiveEvidence(
        source_id="s1", requested_url="https://example.com/1", final_url="https://example.com/1",
        origin="live-web", fetched_at="2026-08-13T10:00:00Z", status=200, content_type="text/html",
        content_sha256="a" * 64, byte_length=10, title="t", excerpt="e", full_text="e",
        observations=(), inferences=(), manual_claims=(),
    ),
)
_SNAPSHOT = ResearchSnapshot(page_slug="test-structure", created_at="2026-08-13T10:00:00Z", evidence=_EVIDENCE)


def _numbered_features(items: list[dict]) -> list[dict]:
    return [{"block": "numbered-features", "id": "why", "data": {"title": "چرا این سازه؟", "items": items}}]


def test_a_cited_real_claim_and_a_genuine_placeholder_both_pass() -> None:
    blocks = _numbered_features([
        {"index": "۰۱", "title": "هزینه", "body": "ادعای واقعی با منبع معتبر.", "icon": "icon-cost", "source_id": "s1"},
        {"index": "۰۲", "title": "جایگزین", "body": LOREM_IPSUM, "icon": "icon-check", "placeholder": True},
    ])
    report = validate_draft(blocks, _SNAPSHOT, LIBRARY)
    assert report.release_recommendation == "ready-for-owner-review"
    assert not report.blockers
    assert report.placeholder_count == 1
    assert all(f.severity == "strength" for f in report.findings)


def test_an_uncited_real_claim_is_a_blocker() -> None:
    blocks = _numbered_features([
        {"index": "۰۱", "title": "ادعا", "body": "یک ادعای خاص بدون منبع واقعی.", "icon": "icon-cost"},
    ])
    report = validate_draft(blocks, _SNAPSHOT, LIBRARY)
    assert report.release_recommendation == "rejected"
    assert any("citation" in b for b in report.blockers)


def test_a_source_id_outside_the_snapshot_is_still_uncited() -> None:
    blocks = _numbered_features([
        {"index": "۰۱", "title": "ادعا", "body": "ادعایی با منبع جعلی.", "icon": "icon-cost", "source_id": "does-not-exist"},
    ])
    report = validate_draft(blocks, _SNAPSHOT, LIBRARY)
    assert report.release_recommendation == "rejected"


def test_a_placeholder_tag_on_real_looking_persian_text_is_dishonest_and_blocks() -> None:
    blocks = _numbered_features([
        {"index": "۰۱", "title": "قلابی", "body": "این یک متن فارسی واقعی‌نما است که غلط علامت خورده.", "icon": "icon-cost", "placeholder": True},
    ])
    report = validate_draft(blocks, _SNAPSHOT, LIBRARY)
    assert report.release_recommendation == "rejected"
    assert any("placeholder-honesty" in b for b in report.blockers)


def test_a_banned_superlative_is_a_refinement_not_a_blocker() -> None:
    blocks = _numbered_features([
        {"index": "۰۱", "title": "ادعا", "body": "این سازه بهترین گزینه بازار است.", "icon": "icon-cost", "source_id": "s1"},
    ])
    report = validate_draft(blocks, _SNAPSHOT, LIBRARY)
    assert report.release_recommendation == "ready-for-owner-review"
    voice_finding = next(f for f in report.findings if f.discipline == "voice")
    assert voice_finding.severity == "refinement"


def test_a_broken_block_contract_is_a_blocker() -> None:
    blocks = [{"block": "numbered-features", "id": "why", "data": {"items": []}}]  # missing required "title"
    report = validate_draft(blocks, _SNAPSHOT, LIBRARY)
    assert report.release_recommendation == "rejected"
    assert any("block-contract" in b for b in report.blockers)


def test_an_unknown_block_id_is_a_blocker() -> None:
    blocks = [{"block": "does-not-exist", "id": "x", "data": {}}]
    report = validate_draft(blocks, _SNAPSHOT, LIBRARY)
    assert report.release_recommendation == "rejected"


def test_fill_draft_gaps_only_touches_genuinely_empty_slots() -> None:
    blocks = _numbered_features([
        {"index": "۰۱", "title": "واقعی", "body": "متن واقعی موجود.", "icon": "icon-cost", "source_id": "s1"},
        {"index": "۰۲", "title": "خالی", "body": "", "icon": "icon-check"},
        {"index": "۰۳", "title": "بدون کلید", "icon": "icon-check"},
    ])
    filled = fill_draft_gaps(blocks)
    items = filled[0]["data"]["items"]
    assert items[0]["body"] == "متن واقعی موجود."
    assert "placeholder" not in items[0]
    assert items[1]["placeholder"] is True
    assert "lorem ipsum" in items[1]["body"].lower()
    assert items[2]["placeholder"] is True


def test_fill_draft_gaps_sizes_the_filler_to_match_real_sibling_items() -> None:
    long_real_body = "متن واقعی نسبتاً بلند. " * 10
    blocks = _numbered_features([
        {"index": "۰۱", "title": "واقعی", "body": long_real_body, "icon": "icon-cost", "source_id": "s1"},
        {"index": "۰۲", "title": "خالی", "body": "", "icon": "icon-check"},
    ])
    filled = fill_draft_gaps(blocks)
    filler = filled[0]["data"]["items"][1]["body"]
    assert abs(len(filler) - len(long_real_body)) < 60  # roughly matched, not a fixed short stub


def test_fill_draft_gaps_leaves_unrelated_blocks_untouched() -> None:
    blocks = [{"block": "lead-form", "id": "quote", "data": {"title": "t", "fields": [], "submit": "s"}}]
    filled = fill_draft_gaps(blocks)
    assert filled == [dict(b) for b in blocks]


def test_lorem_ipsum_of_length_cuts_on_a_word_boundary() -> None:
    text = lorem_ipsum_of_length(50)
    assert len(text) <= 60
    assert not text.endswith(" ")


def test_report_reads_as_a_short_persian_summary() -> None:
    blocks = _numbered_features([
        {"index": "۰۱", "title": "واقعی", "body": "ادعای واقعی.", "icon": "icon-cost", "source_id": "s1"},
    ])
    text = validate_draft(blocks, _SNAPSHOT, LIBRARY).report()
    assert text.startswith("# بررسی پیش‌نویس محتوا:")
    assert "ready-for-owner-review" in text
