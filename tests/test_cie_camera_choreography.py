from ruos.cie_camera_choreography import build_camera_choreography_plan, render_camera_choreography_runtime


def test_camera_plan_maps_scene_states_to_model_keyframes():
    scenes = {"sections": [{"section_id": "knowledge", "scenes": [
        {"id": "overview", "state": "overview", "range": [0.0, 0.25]},
        {"id": "structure", "state": "structure", "range": [0.25, 0.5]},
        {"id": "foundation", "state": "foundation", "range": [0.5, 0.75]},
        {"id": "context", "state": "placement", "range": [0.75, 1.0]},
    ]}]}
    delivery = {"bindings": [{"section_id": "knowledge", "media_type": "model-3d", "status": "ready"}]}
    plan = build_camera_choreography_plan(scenes, delivery)
    assert plan["status"] == "ready"
    frames = plan["sections"][0]["keyframes"]
    assert [item["state"] for item in frames] == ["overview", "structure", "foundation", "placement"]
    assert frames[1]["focus_hotspot"] == "structure"
    assert frames[2]["camera"]["target"] == "0m -.35m 0m"


def test_camera_runtime_preserves_user_control_and_state_sync():
    plan = {"status": "ready", "sections": [{"section_id": "knowledge", "keyframes": [{"scene_id": "structure", "state": "structure", "range": [0, 1], "camera": {"orbit": "60deg 63deg 98%", "target": "0m .35m 0m", "fov": "29deg"}}]}]}
    runtime = render_camera_choreography_runtime(plan)
    assert "RUOS_CIE_CAMERA" in runtime
    assert "cameraOrbit" in runtime
    assert "cameraTarget" in runtime
    assert "fieldOfView" in runtime
    assert "user-interaction" in runtime
    assert "cie:hotspot-change" in runtime
    assert "prefers-reduced-motion" in runtime
