from ruos.cie_runtime_media import render_runtime_media_js, render_runtime_media_markup


def _binding():
    return {
        "asset_id": "structure-model",
        "section_id": "knowledge",
        "media_type": "model-3d",
        "status": "ready",
        "poster_uri": "assets/media/structure-model/poster.webp",
        "alt": "مدل سه‌بعدی سازه تبلیغاتی",
        "variants": [
            {"status": "produced", "format": "glb", "lod": "medium", "uri": "assets/media/structure-model/model-medium.glb"},
            {"status": "produced", "format": "glb", "lod": "high", "uri": "assets/media/structure-model/model-high.glb"},
        ],
        "hotspots": [
            {"id": "foundation", "label": "فونداسیون", "position": "0m 0m 0m", "normal": "0m 1m 0m", "state": "foundation"},
            {"id": "lighting", "label": "نورپردازی", "position": "0m 1m 0m", "normal": "0m 1m 0m", "state": "lighting"},
        ],
    }


def test_model_markup_uses_real_progressive_model_viewer_and_hotspots():
    markup = render_runtime_media_markup(_binding())
    assert "<model-viewer" in markup
    assert "data-cie-model-medium" in markup
    assert "model-medium.glb" in markup
    assert 'data-cie-model-hotspot="foundation"' in markup
    assert 'data-cie-state-target="lighting"' in markup
    assert "poster.webp" in markup


def test_webgl_runtime_has_capability_lod_and_scene_hotspot_sync():
    delivery = {
        "status": "ready",
        "selection_policy": {"model_3d": "progressive-model-viewer-webgl", "hotspot_state_sync": True},
    }
    runtime = render_runtime_media_js(delivery)
    assert "cieWebGLCapable" in runtime
    assert "navigator.connection" in runtime
    assert "customElements.get('model-viewer')" in runtime
    assert "cieSelectedLod" in runtime
    assert "MutationObserver" in runtime
    assert "cie:hotspot-change" in runtime
    assert "data-cie-state" in runtime or "dataset.cieState" in runtime
