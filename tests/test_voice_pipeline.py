import json
from pathlib import Path

import pytest

from ruos.compiler import compile_page
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec
from ruos.voice_studio import VoiceStudioError


def test_approved_voice_is_embedded_in_content_and_review(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    result = compile_page(
        page,
        BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True),
    )

    content = json.loads(
        (result.output_dir / "studio/content-plan.json").read_text(encoding="utf-8")
    )
    review = json.loads(
        (result.output_dir / "studio/agency-review.json").read_text(encoding="utf-8")
    )

    assert content["voice"]["approved_voice_id"] == "strategic-editorial-fa"
    assert content["voice"]["approval_status"] == "approved"
    assert len(content["voice"]["sha256"]) == 64
    assert all(
        block["attributes"]["voice_id"] == "strategic-editorial-fa"
        for block in content["blocks"]
    )
    assert review["content_voice"]["approved_voice_id"] == "strategic-editorial-fa"
    assert review["content_voice"]["sha256"] == content["voice"]["sha256"]


def test_compiler_rejects_page_without_voice_approval(tmp_path: Path) -> None:
    page = load_page_spec(Path("pages/structures.json"))
    page.metadata["voice"] = {
        "approved_voice_id": "strategic-editorial-fa",
        "approval_status": "pending",
    }

    with pytest.raises(VoiceStudioError, match="blocked until a voice candidate is approved"):
        compile_page(
            page,
            BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True),
        )
