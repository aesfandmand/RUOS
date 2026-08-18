import pytest

from ruos.content_intelligence_instagram import (
    InstagramConfig,
    InstagramConfigError,
    normalize_insights_payload,
)


def test_instagram_endpoint_requires_runtime_version_but_builds_clean_url():
    config = InstagramConfig(
        access_token="secret",
        user_id="17890000000000000",
        api_version="v99.0",
    )
    assert (
        config.endpoint("123/insights")
        == "https://graph.instagram.com/v99.0/123/insights"
    )


def test_instagram_config_from_env_rejects_missing_values(monkeypatch):
    monkeypatch.delenv("CI_INSTAGRAM_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("CI_INSTAGRAM_USER_ID", raising=False)
    monkeypatch.delenv("CI_META_GRAPH_API_VERSION", raising=False)
    with pytest.raises(InstagramConfigError):
        InstagramConfig.from_env()


def test_normalize_insights_supports_values_and_total_value_shapes():
    payload = {
        "data": [
            {"name": "views", "values": [{"value": 1200}]},
            {"name": "shares", "total_value": {"value": 44}},
            {"name": "ignored", "values": []},
        ]
    }
    assert normalize_insights_payload(payload) == {"views": 1200, "shares": 44}
