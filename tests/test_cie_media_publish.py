from pathlib import Path

import pytest

from ruos.cie_media_publish import MediaPublishError, enforce_publish_media, resolve_asset_registry, validate_publish_media


def _registry():
    return {
        "entries": [
            {"asset_id": "hero-image", "media_type": "image", "status": "unresolved", "integrity": {"algorithm": "sha256", "value": None}, "provenance": {}, "semantics": {"decorative": False}, "poster_uri": None},
            {"asset_id": "structure-model", "media_type": "model-3d", "status": "unresolved", "integrity": {"algorithm": "sha256", "value": None}, "provenance": {}, "semantics": {"decorative": False}, "poster_uri": None},
        ]
    }


def test_publish_gate_blocks_unresolved_assets():
    report = validate_publish_media(_registry())
    assert report["status"] == "blocked"
    assert any("source is not resolved" in failure for failure in report["failures"])
    with pytest.raises(MediaPublishError):
        enforce_publish_media(_registry())


def test_real_asset_resolver_computes_integrity_and_publish_gate_passes(tmp_path: Path):
    image = tmp_path / "hero.webp"; image.write_bytes(b"hero-image")
    model = tmp_path / "structure.glb"; model.write_bytes(b"glb-model")
    poster = tmp_path / "poster.webp"; poster.write_bytes(b"poster")
    bindings = {
        "hero-image": {"uri": image.name, "provenance": {"provider": "studio", "license": "owned"}, "semantics": {"alt": "نمای سازه تبلیغاتی"}},
        "structure-model": {"uri": model.name, "poster_uri": poster.name, "provenance": {"provider": "studio", "license": "owned"}},
    }
    resolved = resolve_asset_registry(_registry(), tmp_path, bindings)
    assert resolved["resolution"] == {"resolved": 2, "total": 2}
    assert all(entry["integrity"]["value"] for entry in resolved["entries"])
    assert validate_publish_media(resolved)["status"] == "pass"
    enforce_publish_media(resolved)
