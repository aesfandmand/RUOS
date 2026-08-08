from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from PIL import Image


class MediaProductionError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record(path: Path, project_root: Path) -> dict[str, Any]:
    try:
        uri = path.relative_to(project_root).as_posix()
    except ValueError:
        uri = path.as_posix()
    return {
        "uri": uri,
        "bytes": path.stat().st_size,
        "kb": max(1, (path.stat().st_size + 1023) // 1024),
        "sha256": _sha256(path),
    }


def _source_path(project_root: Path, uri: object) -> Path | None:
    if not uri:
        return None
    candidate = Path(str(uri))
    path = candidate if candidate.is_absolute() else project_root / candidate
    return path if path.is_file() else None


def _produce_image(asset: Mapping[str, Any], source: Path, output_dir: Path, project_root: Path) -> list[dict[str, Any]]:
    variants = asset.get("variants", []) if isinstance(asset.get("variants"), list) else []
    produced: list[dict[str, Any]] = []
    with Image.open(source) as image:
        base = image.convert("RGB") if image.mode not in {"RGB", "RGBA"} else image.copy()
        for variant in variants:
            if not isinstance(variant, Mapping):
                continue
            fmt = str(variant.get("format", "")).lower()
            width = int(variant.get("width", base.width) or base.width)
            if fmt not in {"webp", "avif"}:
                continue
            scale = min(1.0, width / max(1, base.width))
            target = base if scale == 1.0 else base.resize((max(1, round(base.width * scale)), max(1, round(base.height * scale))), Image.Resampling.LANCZOS)
            path = output_dir / f"{asset['asset_id']}-{width}.{fmt}"
            try:
                target.save(path, format=fmt.upper(), quality=82, optimize=True)
            except Exception as exc:
                raise MediaProductionError(f"{asset['asset_id']}: failed to encode {fmt}: {exc}") from exc
            item = {**dict(variant), **_record(path, project_root), "status": "produced"}
            produced.append(item)
    return produced


def _produce_svg(asset: Mapping[str, Any], source: Path, output_dir: Path, project_root: Path) -> list[dict[str, Any]]:
    path = output_dir / f"{asset['asset_id']}.svg"
    shutil.copy2(source, path)
    return [{"format": "svg", "mode": "original-vector", **_record(path, project_root), "status": "produced"}]


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise MediaProductionError((completed.stderr or completed.stdout or "media tool failed").strip())


def _produce_video(asset: Mapping[str, Any], source: Path, output_dir: Path, project_root: Path) -> list[dict[str, Any]]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return [{"status": "blocked", "reason": "ffmpeg-not-installed", "format": str(v.get("format", ""))} for v in asset.get("variants", []) if isinstance(v, Mapping)]
    produced: list[dict[str, Any]] = []
    for variant in asset.get("variants", []) if isinstance(asset.get("variants"), list) else []:
        if not isinstance(variant, Mapping):
            continue
        fmt = str(variant.get("format", "mp4"))
        max_width = int(variant.get("max_width", 1280) or 1280)
        path = output_dir / f"{asset['asset_id']}-{variant.get('profile','default')}.{fmt}"
        codec = ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "34"] if fmt == "webm" else ["-c:v", "libx264", "-crf", "23", "-preset", "medium", "-movflags", "+faststart"]
        _run([ffmpeg, "-y", "-i", str(source), "-vf", f"scale='min({max_width},iw)':-2", *codec, "-an", str(path)])
        produced.append({**dict(variant), **_record(path, project_root), "status": "produced"})
    return produced


def _produce_model(asset: Mapping[str, Any], source: Path, output_dir: Path, project_root: Path) -> list[dict[str, Any]]:
    tool = shutil.which("gltf-transform")
    produced: list[dict[str, Any]] = []
    variants = asset.get("variants", []) if isinstance(asset.get("variants"), list) else []
    for variant in variants:
        if not isinstance(variant, Mapping):
            continue
        lod = str(variant.get("lod", "high"))
        if lod == "high":
            path = output_dir / f"{asset['asset_id']}-high.glb"
            shutil.copy2(source, path)
            produced.append({**dict(variant), **_record(path, project_root), "status": "produced"})
            continue
        if lod == "poster":
            produced.append({**dict(variant), "status": "external-poster-required"})
            continue
        if not tool:
            produced.append({**dict(variant), "status": "blocked", "reason": "gltf-transform-not-installed"})
            continue
        path = output_dir / f"{asset['asset_id']}-{lod}.glb"
        _run([tool, "optimize", str(source), str(path), "--compress", "meshopt"])
        produced.append({**dict(variant), **_record(path, project_root), "status": "produced"})
    return produced


def produce_media_derivatives(
    manifest: Mapping[str, Any],
    registry: Mapping[str, Any],
    project_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    sources = {str(item.get("asset_id")): item for item in registry.get("entries", []) if isinstance(item, Mapping)}
    output_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for asset in manifest.get("assets", []) if isinstance(manifest, Mapping) else []:
        if not isinstance(asset, Mapping):
            continue
        asset_id = str(asset.get("asset_id", ""))
        entry = sources.get(asset_id, {})
        source = _source_path(project_root, entry.get("uri"))
        media_type = str(asset.get("media_type", "image"))
        if source is None:
            results.append({"asset_id": asset_id, "media_type": media_type, "status": "blocked", "reason": "source-not-found", "variants": []})
            continue
        target_dir = output_root / asset_id
        target_dir.mkdir(parents=True, exist_ok=True)
        if media_type == "image": variants = _produce_image(asset, source, target_dir, project_root)
        elif media_type == "svg": variants = _produce_svg(asset, source, target_dir, project_root)
        elif media_type == "video": variants = _produce_video(asset, source, target_dir, project_root)
        elif media_type == "model-3d": variants = _produce_model(asset, source, target_dir, project_root)
        else:
            path = target_dir / source.name
            shutil.copy2(source, path)
            variants = [{"format": "original", **_record(path, project_root), "status": "produced"}]
        status = "produced" if any(v.get("status") == "produced" for v in variants) and not any(v.get("status") == "blocked" for v in variants) else "partial" if any(v.get("status") == "produced" for v in variants) else "blocked"
        results.append({"asset_id": asset_id, "media_type": media_type, "status": status, "variants": variants})
    observed = {
        "produced_bytes": sum(int(v.get("bytes", 0) or 0) for item in results for v in item.get("variants", []) if isinstance(v, Mapping)),
        "produced_assets": sum(1 for item in results if item.get("status") == "produced"),
        "partial_assets": sum(1 for item in results if item.get("status") == "partial"),
        "blocked_assets": sum(1 for item in results if item.get("status") == "blocked"),
    }
    report = {"version": "1.0", "status": "produced" if results and observed["blocked_assets"] == 0 else "partial" if results else "blocked", "assets": results, "observed": observed}
    (output_root / "media-production-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return report
