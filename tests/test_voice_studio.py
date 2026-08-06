import json
from dataclasses import replace
from pathlib import Path

import pytest

from ruos.spec_loader import load_page_spec
from ruos.voice_studio import VoiceStudioError, select_voice


def _page():
    page = load_page_spec(Path("pages/structures.json"))
    approval = json.loads(Path("voice-approvals/structures.json").read_text(encoding="utf-8"))
    metadata = dict(page.metadata)
    metadata["voice"] = {
        "approval_status": approval["approval_status"],
        "approved_voice_id": approval["approved_voice_id"],
    }
    return replace(page, metadata=metadata)


def test_approved_persian_voice_is_deterministic() -> None:
    first = select_voice(_page())
    second = select_voice(_page())

    assert first.approved.id == "strategic-editorial-fa"
    assert first.approval_status == "approved"
    assert len(first.candidates) == 3
    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert len(first.sha256) == 64


def test_unapproved_voice_blocks_content_production() -> None:
    page = _page()
    metadata = dict(page.metadata)
    metadata["voice"] = {
        "approval_status": "pending",
        "approved_voice_id": "strategic-editorial-fa",
    }

    with pytest.raises(VoiceStudioError, match="blocked"):
        select_voice(replace(page, metadata=metadata))


def test_unknown_approved_voice_is_rejected() -> None:
    page = _page()
    metadata = dict(page.metadata)
    metadata["voice"] = {
        "approval_status": "approved",
        "approved_voice_id": "invented-voice",
    }

    with pytest.raises(VoiceStudioError, match="not a candidate"):
        select_voice(replace(page, metadata=metadata))
