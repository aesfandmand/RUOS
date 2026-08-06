from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .open_source_registry import OpenSourceAsset, OpenSourceRegistry, OpenSourceRegistryError


def write_registry(registry: OpenSourceRegistry, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**registry.payload(), "sha256": registry.sha256}
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _asset(item: object, index: int) -> OpenSourceAsset:
    if not isinstance(item, dict):
        raise OpenSourceRegistryError(f"Registry asset #{index} must be an object")
    metrics = item.get("metrics")
    scores = item.get("scores")
    if not isinstance(metrics, dict) or not isinstance(scores, dict):
        raise OpenSourceRegistryError(f"Registry asset #{index} metrics or scores are invalid")
    try:
        return OpenSourceAsset(
            id=str(item["id"]),
            name=str(item["name"]),
            category=str(item["category"]),
            repository_url=str(item["repository_url"]),
            homepage_url=str(item.get("homepage_url", "")),
            package_name=str(item.get("package_name", "")),
            license_spdx=str(item["license_spdx"]),
            version=str(item.get("version", "")),
            source_commit=str(item["source_commit"]),
            observed_at=str(item["observed_at"]),
            stars=int(metrics["stars"]),
            open_issues=int(metrics["open_issues"]),
            days_since_push=int(metrics["days_since_push"]),
            maintenance_score=int(scores["maintenance"]),
            documentation_score=int(scores["documentation"]),
            accessibility_score=int(scores["accessibility"]),
            performance_score=int(scores["performance"]),
            rtl_score=int(scores["rtl"]),
            ecosystem_score=int(scores["ecosystem"]),
            production_score=int(scores["production"]),
            capabilities=tuple(str(value) for value in item.get("capabilities", [])),
            constraints=tuple(str(value) for value in item.get("constraints", [])),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise OpenSourceRegistryError(f"Registry asset #{index} is invalid") from exc


def load_registry(path: Path) -> OpenSourceRegistry:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OpenSourceRegistryError(f"Unable to read open-source registry: {path}") from exc
    if not isinstance(raw, dict):
        raise OpenSourceRegistryError("Open-source registry root must be an object")
    if int(raw.get("schema_version", 0)) != 1:
        raise OpenSourceRegistryError("Unsupported open-source registry schema version")
    rows = raw.get("assets")
    if not isinstance(rows, list):
        raise OpenSourceRegistryError("Open-source registry assets must be a list")
    registry = OpenSourceRegistry.build(_asset(item, index) for index, item in enumerate(rows, start=1))
    if int(raw.get("asset_count", -1)) != len(registry.assets):
        raise OpenSourceRegistryError("Open-source registry asset count is inconsistent")
    if str(raw.get("sha256", "")) != registry.sha256:
        raise OpenSourceRegistryError("Open-source registry checksum does not match its contents")
    return registry
