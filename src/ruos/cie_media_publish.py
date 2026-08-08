from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Mapping, Sequence


class MediaPublishError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_asset_registry(
    registry: Mapping[str, Any],
    project_root: Path,
    bindings: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    bindings = bindings or {}
    entries: list[dict[str, Any]] = []
    for raw in registry.get("entries", []) if isinstance(registry, Mapping) else []:
        if not isinstance(raw, Mapping):
            continue
        entry = dict(raw)
        asset_id = str(entry.get("asset_id", ""))
        binding = bindings.get(asset_id, {})
        uri = binding.get("uri", entry.get("uri"))
        poster_uri = binding.get("poster_uri", entry.get("poster_uri"))
        entry["uri"] = uri
        entry["poster_uri"] = poster_uri
        entry["responsive_sources"] = list(binding.get("responsive_sources", entry.get("responsive_sources", [])) or [])
        entry["provenance"] = {**dict(entry.get("provenance", {})), **dict(binding.get("provenance", {}))}
        entry["semantics"] = {**dict(entry.get("semantics", {})), **dict(binding.get("semantics", {}))}
        entry["hotspots"] = list(binding.get("hotspots", entry.get("hotspots", [])) or [])

        if uri:
            candidate = Path(str(uri))
            local = candidate if candidate.is_absolute() else project_root / candidate
            if local.is_file():
                checksum = _sha256(local)
                entry["checksum"] = checksum
                entry["integrity"] = {"algorithm": "sha256", "value": checksum}
                entry["mime_type"] = binding.get("mime_type") or mimetypes.guess_type(local.name)[0]
                entry["status"] = "resolved"
            else:
                entry["status"] = "missing-source"
        else:
            entry["status"] = "unresolved"
        entries.append(entry)

    result = dict(registry)
    result["entries"] = entries
    result["resolution"] = {
        "resolved": sum(1 for item in entries if item.get("status") == "resolved"),
        "total": len(entries),
    }
    return result


def validate_publish_media(registry: Mapping[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    for entry in registry.get("entries", []) if isinstance(registry, Mapping) else []:
        if not isinstance(entry, Mapping):
            continue
        asset_id = str(entry.get("asset_id", "unknown"))
        media_type = str(entry.get("media_type", "image"))
        semantics = entry.get("semantics", {}) if isinstance(entry.get("semantics"), Mapping) else {}
        provenance = entry.get("provenance", {}) if isinstance(entry.get("provenance"), Mapping) else {}
        decorative = bool(semantics.get("decorative", False))

        if entry.get("status") != "resolved":
            failures.append(f"{asset_id}: source is not resolved")
        integrity = entry.get("integrity", {}) if isinstance(entry.get("integrity"), Mapping) else {}
        if not integrity.get("value"):
            failures.append(f"{asset_id}: sha256 integrity is missing")
        if not provenance.get("provider") and not provenance.get("source_url"):
            failures.append(f"{asset_id}: provenance is missing")
        if not provenance.get("license"):
            failures.append(f"{asset_id}: license is missing")
        if not decorative and media_type in {"image", "svg"} and not semantics.get("alt"):
            failures.append(f"{asset_id}: semantic alt is missing")
        if media_type in {"model-3d", "video"} and not entry.get("poster_uri"):
            failures.append(f"{asset_id}: poster is required for {media_type}")

    return {
        "status": "pass" if not failures else "blocked",
        "failures": failures,
        "checked_assets": len(registry.get("entries", [])) if isinstance(registry, Mapping) else 0,
    }


def enforce_publish_media(registry: Mapping[str, Any]) -> None:
    report = validate_publish_media(registry)
    if report["status"] != "pass":
        raise MediaPublishError("CIE publish media gate blocked: " + "; ".join(report["failures"]))
