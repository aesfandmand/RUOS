from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Mapping


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _entry_index(registry: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(item.get("asset_id")): item for item in registry.get("entries", []) if isinstance(item, Mapping) and item.get("asset_id")}


def _section_index(asset_media_plan: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for section in asset_media_plan.get("sections", []) if isinstance(asset_media_plan, Mapping) else []:
        if not isinstance(section, Mapping):
            continue
        section_id = str(section.get("section_id", ""))
        for asset in section.get("assets", []) if isinstance(section.get("assets"), list) else []:
            if isinstance(asset, Mapping) and asset.get("asset_id"):
                result[str(asset.get("asset_id"))] = section_id
    return result


def _artifact_uri(asset_id: str, source_uri: object) -> str:
    return f"assets/media/{asset_id}/{Path(str(source_uri)).name}"


def build_runtime_media_delivery(
    production_report: Mapping[str, Any],
    registry: Mapping[str, Any],
    asset_media_plan: Mapping[str, Any],
    project_root: Path,
) -> tuple[dict[str, Any], dict[str, Path]]:
    entries = _entry_index(registry)
    sections = _section_index(asset_media_plan)
    bindings: list[dict[str, Any]] = []
    artifacts: dict[str, Path] = {}
    for result in production_report.get("assets", []) if isinstance(production_report, Mapping) else []:
        if not isinstance(result, Mapping) or result.get("status") not in {"produced", "partial"}:
            continue
        asset_id = str(result.get("asset_id", ""))
        entry = entries.get(asset_id, {})
        variants: list[dict[str, Any]] = []
        for variant in result.get("variants", []) if isinstance(result.get("variants"), list) else []:
            if not isinstance(variant, Mapping) or variant.get("status") != "produced" or not variant.get("uri"):
                continue
            source = Path(str(variant["uri"]))
            if not source.is_absolute():
                source = project_root / source
            if not source.is_file():
                continue
            final_uri = _artifact_uri(asset_id, source)
            artifacts[final_uri] = source
            item = dict(variant)
            item["uri"] = final_uri
            variants.append(item)
        poster_uri = entry.get("poster_uri")
        final_poster = None
        if poster_uri:
            poster_source = Path(str(poster_uri))
            if not poster_source.is_absolute():
                poster_source = project_root / poster_source
            if poster_source.is_file():
                final_poster = f"assets/media/{asset_id}/poster{poster_source.suffix.lower()}"
                artifacts[final_poster] = poster_source
        semantics = entry.get("semantics", {}) if isinstance(entry.get("semantics"), Mapping) else {}
        bindings.append({
            "asset_id": asset_id,
            "section_id": sections.get(asset_id, ""),
            "media_type": str(result.get("media_type", entry.get("media_type", "image"))),
            "variants": variants,
            "poster_uri": final_poster,
            "alt": str(semantics.get("alt") or ""),
            "caption": str(semantics.get("caption") or ""),
            "decorative": bool(semantics.get("decorative", False)),
            "status": "ready" if variants else "fallback-only" if final_poster else "unavailable",
        })
    ready = [item for item in bindings if item["status"] in {"ready", "fallback-only"}]
    return {
        "version": "1.0",
        "status": "ready" if ready else "blocked",
        "selection_policy": {
            "images": "native-picture-srcset",
            "video": "poster-first-native-sources",
            "model_3d": "capability-and-network-tier-lod",
            "save_data_prefers_poster": True,
            "reduced_motion_prefers_poster": True,
        },
        "bindings": bindings,
    }, artifacts


def _image_markup(binding: Mapping[str, Any]) -> str:
    variants = [v for v in binding.get("variants", []) if isinstance(v, Mapping)]
    by_format: dict[str, list[Mapping[str, Any]]] = {}
    for variant in variants:
        by_format.setdefault(str(variant.get("format", "")), []).append(variant)
    sources: list[str] = []
    for fmt, mime in (("avif", "image/avif"), ("webp", "image/webp")):
        group = sorted(by_format.get(fmt, []), key=lambda v: int(v.get("width", 0) or 0))
        if group:
            srcset = ", ".join(f"{_esc(v['uri'])} {int(v.get('width', 0) or 0)}w" for v in group)
            sources.append(f'<source type="{mime}" srcset="{srcset}" sizes="(max-width:760px) 100vw, 50vw">')
    fallback = sorted(by_format.get("webp", []) or variants, key=lambda v: int(v.get("width", 0) or 0))
    src = fallback[-1].get("uri", "") if fallback else ""
    alt = "" if binding.get("decorative") else str(binding.get("alt", ""))
    return '<picture data-cie-responsive-picture>' + "".join(sources) + f'<img src="{_esc(src)}" alt="{_esc(alt)}" loading="lazy" decoding="async"></picture>'


def _video_markup(binding: Mapping[str, Any]) -> str:
    poster = f' poster="{_esc(binding.get("poster_uri"))}"' if binding.get("poster_uri") else ""
    sources = []
    for variant in binding.get("variants", []) if isinstance(binding.get("variants"), list) else []:
        if not isinstance(variant, Mapping):
            continue
        fmt = str(variant.get("format", ""))
        mime = "video/webm" if fmt == "webm" else "video/mp4" if fmt == "mp4" else ""
        sources.append(f'<source src="{_esc(variant.get("uri", ""))}" type="{mime}">')
    return f'<video data-cie-responsive-video playsinline muted preload="metadata"{poster}>' + "".join(sources) + "</video>"


def _model_markup(binding: Mapping[str, Any]) -> str:
    variants = [v for v in binding.get("variants", []) if isinstance(v, Mapping)]
    attrs = []
    for variant in variants:
        lod = str(variant.get("lod", "high"))
        attrs.append(f'data-cie-model-{_esc(lod)}="{_esc(variant.get("uri", ""))}"')
    poster = binding.get("poster_uri")
    image = f'<img src="{_esc(poster)}" alt="{_esc(binding.get("alt", ""))}" loading="lazy" decoding="async">' if poster else ""
    return f'<div data-cie-responsive-model {" ".join(attrs)}>{image}<span class="cie-media__model-status" aria-live="polite"></span></div>'


def render_runtime_media_markup(binding: Mapping[str, Any]) -> str:
    media_type = str(binding.get("media_type", "image"))
    if media_type == "image": content = _image_markup(binding)
    elif media_type == "video": content = _video_markup(binding)
    elif media_type == "model-3d": content = _model_markup(binding)
    elif media_type == "svg":
        variants = [v for v in binding.get("variants", []) if isinstance(v, Mapping)]
        src = variants[0].get("uri", "") if variants else ""
        content = f'<img src="{_esc(src)}" alt="{_esc(binding.get("alt", ""))}" loading="lazy" decoding="async">'
    else: return ""
    caption = f'<figcaption>{_esc(binding.get("caption"))}</figcaption>' if binding.get("caption") else ""
    return f'<figure class="cie-runtime-media cie-runtime-media--{_esc(media_type)}" data-cie-runtime-media="{_esc(binding.get("asset_id", ""))}">{content}{caption}</figure>'


def bind_runtime_media_document(document: str, delivery: Mapping[str, Any]) -> str:
    result = document
    for binding in delivery.get("bindings", []) if isinstance(delivery, Mapping) else []:
        if not isinstance(binding, Mapping) or binding.get("status") not in {"ready", "fallback-only"}:
            continue
        section_id = str(binding.get("section_id", ""))
        if not section_id:
            continue
        markup = render_runtime_media_markup(binding)
        pattern = re.compile(rf'(<section\b[^>]*\bid="{re.escape(section_id)}"[^>]*>.*?)(</section>)', re.S)
        result, count = pattern.subn(lambda match: match.group(1) + markup + match.group(2), result, count=1)
        if count == 0:
            continue
    return result


def render_runtime_media_css(delivery: Mapping[str, Any]) -> str:
    if delivery.get("status") != "ready": return ""
    return """
.cie-runtime-media{margin:1.25rem 0;overflow:hidden;border-radius:var(--radius-md);background:var(--color-surface)}
.cie-runtime-media :is(img,video,picture){display:block;inline-size:100%;max-inline-size:100%}.cie-runtime-media img,.cie-runtime-media video{block-size:auto;object-fit:cover}
.cie-runtime-media figcaption{padding:.65rem .85rem;color:var(--color-muted);font-size:.875rem}
[data-cie-responsive-model]{position:relative;min-block-size:12rem;background:var(--color-surface);display:grid;place-items:center}[data-cie-responsive-model] img{inline-size:100%}.cie-media__model-status{position:absolute;inset:auto .75rem .75rem;background:var(--color-bg);padding:.35rem .55rem;border-radius:999px;font-size:.75rem}
@media (max-width:760px){.cie-runtime-media{margin-inline:calc(var(--page-gutter)*-.25)}}
""".strip()


def render_runtime_media_js(delivery: Mapping[str, Any]) -> str:
    if delivery.get("status") != "ready": return ""
    payload = json.dumps(delivery.get("selection_policy", {}), ensure_ascii=False, separators=(",", ":"))
    return f'''const RUOS_CIE_MEDIA_POLICY={payload};
const cieConnection=navigator.connection||navigator.mozConnection||navigator.webkitConnection;
const cieSaveData=Boolean(cieConnection&&cieConnection.saveData);
const cieEffectiveType=String(cieConnection&&cieConnection.effectiveType||'4g');
const cieReducedMedia=matchMedia('(prefers-reduced-motion: reduce)').matches;
for(const video of document.querySelectorAll('[data-cie-responsive-video]')){{if(cieSaveData||cieReducedMedia){{video.preload='none';video.removeAttribute('autoplay');}}}}
for(const model of document.querySelectorAll('[data-cie-responsive-model]')){{let lod='high';if(cieSaveData||/2g/.test(cieEffectiveType))lod='poster';else if(/3g/.test(cieEffectiveType)||innerWidth<900)lod='medium';const uri=model.dataset[`cieModel${{lod[0].toUpperCase()+lod.slice(1)}}`]||model.dataset.cieModelMedium||model.dataset.cieModelHigh||'';model.dataset.cieSelectedLod=lod;model.dataset.cieSelectedSource=uri;const status=model.querySelector('.cie-media__model-status');if(status)status.textContent=uri?`LOD: ${{lod}}`:'';}}
'''
