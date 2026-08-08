from ruos.cie_mesh_state import build_mesh_state_plan, render_mesh_state_runtime


def test_mesh_state_plan_maps_scene_states_to_authored_model_contracts():
    scenes = {"sections": [{"section_id": "knowledge", "scenes": [
        {"id": "overview", "state": "overview"},
        {"id": "structure", "state": "structure"},
        {"id": "foundation", "state": "foundation"},
        {"id": "context", "state": "placement"},
    ]}]}
    delivery = {"bindings": [{"section_id": "knowledge", "media_type": "model-3d", "status": "ready"}]}
    plan = build_mesh_state_plan(scenes, delivery)
    assert plan["status"] == "ready"
    states = {item["state"]: item for item in plan["sections"][0]["states"]}
    assert states["structure"]["variant"] == "structure"
    assert states["foundation"]["animation"] == "cie-explode-foundation"
    assert states["placement"]["mode"] == "context-highlight"
    assert plan["policy"]["exploded_view_requires_authored_glb_variant_or_animation"] is True


def test_mesh_state_runtime_uses_model_viewer_variants_animations_and_fallback():
    plan = {"status": "ready", "sections": [{"section_id": "knowledge", "states": [
        {"state": "overview", "variant": "overview", "animation": "cie-overview", "mode": "assembled", "fallback": "camera-and-hotspot-only"},
        {"state": "foundation", "variant": "foundation", "animation": "cie-explode-foundation", "mode": "isolate-highlight", "fallback": "camera-and-hotspot-only"},
    ]}]}
    runtime = render_mesh_state_runtime(plan)
    assert "RUOS_CIE_MESH_STATE" in runtime
    assert "availableVariants" in runtime
    assert "availableAnimations" in runtime
    assert "variantName" in runtime
    assert "animationName" in runtime
    assert "cie:model-state" in runtime
    assert "prefers-reduced-motion" in runtime
