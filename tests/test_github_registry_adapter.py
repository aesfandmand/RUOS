from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

import pytest

from ruos.github_registry_adapter import GitHubRegistryAdapter, GitHubRegistryError


class FakeTransport:
    def __init__(self, responses: Mapping[str, Mapping[str, object]]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def get_json(self, path: str) -> Mapping[str, object]:
        self.calls.append(path)
        response = self.responses.get(path)
        if response is None:
            raise GitHubRegistryError(f"missing fake response: {path}")
        return response


def _responses(*, archived: bool = False, license_spdx: str = "MIT") -> dict[str, Mapping[str, object]]:
    return {
        "/repos/lucide-icons/lucide": {
            "default_branch": "main",
            "html_url": "https://github.com/lucide-icons/lucide",
            "homepage": "https://lucide.dev",
            "description": "Icon toolkit",
            "license": {"spdx_id": license_spdx},
            "stargazers_count": 20000,
            "open_issues_count": 100,
            "pushed_at": "2026-08-01T00:00:00Z",
            "archived": archived,
            "disabled": False,
            "fork": False,
        },
        "/repos/lucide-icons/lucide/commits/main": {"sha": "a" * 40},
        "/repos/lucide-icons/lucide/releases/latest": {"tag_name": "v1.0.0"},
    }


def _adapter(responses: Mapping[str, Mapping[str, object]]) -> GitHubRegistryAdapter:
    return GitHubRegistryAdapter(
        transport=FakeTransport(responses),
        clock=lambda: datetime(2026, 8, 6, 0, 0, tzinfo=timezone.utc),
    )


def test_adapter_collects_live_repository_provenance() -> None:
    evidence = _adapter(_responses()).inspect("lucide-icons/lucide")

    assert evidence.repository == "lucide-icons/lucide"
    assert evidence.source_commit == "a" * 40
    assert evidence.license_spdx == "MIT"
    assert evidence.latest_release == "v1.0.0"
    assert evidence.days_since_push == 5
    assert evidence.observed_at == "2026-08-06T00:00:00Z"


def test_adapter_builds_registry_asset_from_observed_metadata() -> None:
    asset = _adapter(_responses()).build_asset(
        "lucide-icons/lucide",
        asset_id="lucide",
        name="Lucide",
        category="icon",
        package_name="lucide",
        maintenance_score=95,
        documentation_score=92,
        accessibility_score=90,
        performance_score=94,
        rtl_score=95,
        ecosystem_score=93,
        production_score=95,
        capabilities=("svg", "rtl-safe", "tree-shakable"),
    )

    assert asset.repository_url == "https://github.com/lucide-icons/lucide"
    assert asset.version == "v1.0.0"
    assert asset.stars == 20000
    assert asset.source_commit == "a" * 40


def test_adapter_rejects_archived_repository() -> None:
    with pytest.raises(GitHubRegistryError, match="Archived or disabled"):
        _adapter(_responses(archived=True)).inspect("lucide-icons/lucide")


def test_adapter_rejects_missing_license_evidence() -> None:
    with pytest.raises(GitHubRegistryError, match="SPDX license"):
        _adapter(_responses(license_spdx="NOASSERTION")).inspect("lucide-icons/lucide")


def test_adapter_rejects_repository_identity_mismatch() -> None:
    responses = _responses()
    responses["/repos/lucide-icons/lucide"] = {
        **responses["/repos/lucide-icons/lucide"],
        "html_url": "https://github.com/attacker/repository",
    }
    with pytest.raises(GitHubRegistryError, match="does not match"):
        _adapter(responses).inspect("lucide-icons/lucide")


def test_adapter_is_deterministic_for_same_observation_time() -> None:
    first = _adapter(_responses()).inspect("lucide-icons/lucide")
    second = _adapter(_responses()).inspect("lucide-icons/lucide")

    assert first.payload() == second.payload()
