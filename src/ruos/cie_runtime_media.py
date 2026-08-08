from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from .cie_camera_choreography import render_camera_choreography_runtime
from .cie_mesh_state import render_mesh_state_runtime
from .cie_webgl_runtime import render_model_viewer, render_webgl_css, render_webgl_runtime
from .models import PageSpec
from .qa import evaluate


def _esc(value: object) -> str: return html.escape(str(value), quote=True)
def _entry_index(registry: Mapping[str, Any]) -> tuple[dict[tuple[str, str], Mapping[str, Any]], dict[str, Mapping[str, Any]]]:
    scoped: dict[tuple[str, str], Mapping[str, Any]] = {}; fallback: dict[str, Mapping[str, Any]] = {}
    for item in registry.get("entries", []) if isinstance(registry, Mapping) else []:
        if not isinstance(item, Mapping) or not item.get("asset_id"): continue
        asset_id=str(item.get("asset_id")); section_id=str(item.get("section_id", "")); scoped[(section_id,asset_id)]=item; fallback.setdefault(asset_id,item)
    return scoped,fallback
def _section_index(asset_media_plan: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for section in asset_media_plan.get("sections", []) if isinstance(asset_media_plan, Mapping) else []:
        if not isinstance(section, Mapping): continue
        for asset in section.get("assets", []) if isinstance(section.get("assets"), list) else []:
            if isinstance(asset, Mapping) and asset.get("asset_id"): result[str(asset.get("asset_id"))] = str(section.get("section_id", ""))
    return result
def _artifact_uri(asset_id: str, source_uri: object, section_id: str="") -> str:
    scope=f"{section_id}/{asset_id}" if section_id else asset_id
    return f"assets/media/{scope}/{Path(str(source_uri)).name}"


def build_runtime_media_delivery(production_report: Mapping[str, Any], registry: Mapping[str, Any], asset_media_plan: Mapping[str, Any], project_root: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    scoped_entries,entries=_entry_index(registry); sections=_section_index(asset_media_plan); bindings=[]; artifacts:dict[str,Path]={}
    for result in production_report.get("assets", []) if isinstance(production_report, Mapping) else []:
        if not isinstance(result, Mapping) or result.get("status") not in {"produced","partial"}: continue
        asset_id=str(result.get("asset_id","")); section_id=str(result.get("section_id") or sections.get(asset_id,"")); entry=scoped_entries.get((section_id,asset_id),entries.get(asset_id,{})); variants=[]
        for variant in result.get("variants", []) if isinstance(result.get("variants"), list) else []:
            if not isinstance(variant, Mapping) or variant.get("status")!="produced" or not variant.get("uri"): continue
            source=Path(str(variant["uri"])); source=source if source.is_absolute() else project_root/source
            if not source.is_file(): continue
            final_uri=_artifact_uri(asset_id,source,section_id); artifacts[final_uri]=source; item=dict(variant); item["uri"]=final_uri; variants.append(item)
        poster_uri=entry.get("poster_uri"); final_poster=None
        if poster_uri:
            poster=Path(str(poster_uri)); poster=poster if poster.is_absolute() else project_root/poster
            if poster.is_file(): final_poster=_artifact_uri(asset_id,f"poster{poster.suffix.lower()}",section_id); artifacts[final_poster]=poster
        semantics=entry.get("semantics",{}) if isinstance(entry.get("semantics"),Mapping) else {}; hotspots=[dict(item) for item in entry.get("hotspots",[]) if isinstance(item,Mapping)] if isinstance(entry.get("hotspots"),list) else []
        bindings.append({"asset_id":asset_id,"section_id":section_id,"media_type":str(result.get("media_type",entry.get("media_type","image"))),"variants":variants,"poster_uri":final_poster,"alt":str(semantics.get("alt") or ""),"caption":str(semantics.get("caption") or ""),"decorative":bool(semantics.get("decorative",False)),"hotspots":hotspots,"status":"ready" if variants else "fallback-only" if final_poster else "unavailable"})
    ready=[item for item in bindings if item["status"] in {"ready","fallback-only"}]
    return {"version":"1.3","status":"ready" if ready else "blocked","selection_policy":{"images":"native-picture-srcset","video":"poster-first-native-sources","model_3d":"progressive-model-viewer-webgl","save_data_prefers_poster":True,"reduced_motion_prefers_poster":True,"hotspot_state_sync":True,"camera_choreography":True,"mesh_state_sync":True},"bindings":bindings},artifacts


def _image_markup(binding: Mapping[str, Any]) -> str:
    variants=[v for v in binding.get("variants",[]) if isinstance(v,Mapping)]; groups:dict[str,list[Mapping[str,Any]]]={}
    for variant in variants: groups.setdefault(str(variant.get("format","")),[]).append(variant)
    sources=[]
    for fmt,mime in (("avif","image/avif"),("webp","image/webp")):
        group=sorted(groups.get(fmt,[]),key=lambda v:int(v.get("width",0) or 0))
        if group:
            srcset=", ".join(f"{_esc(v['uri'])} {int(v.get('width',0) or 0)}w" for v in group); sources.append(f'<source type="{mime}" srcset="{srcset}" sizes="(max-width:760px) 100vw, 50vw">')
    fallback=sorted(groups.get("webp",[]) or variants,key=lambda v:int(v.get("width",0) or 0)); src=fallback[-1].get("uri","") if fallback else ""; alt="" if binding.get("decorative") else str(binding.get("alt",""))
    return '<picture data-cie-responsive-picture>'+"".join(sources)+f'<img src="{_esc(src)}" alt="{_esc(alt)}" loading="lazy" decoding="async"></picture>'

def _video_markup(binding: Mapping[str, Any]) -> str:
    poster=f' poster="{_esc(binding.get("poster_uri"))}"' if binding.get("poster_uri") else ""; sources=[]
    for variant in binding.get("variants",[]) if isinstance(binding.get("variants"),list) else []:
        if not isinstance(variant,Mapping): continue
        fmt=str(variant.get("format","")); mime="video/webm" if fmt=="webm" else "video/mp4" if fmt=="mp4" else ""; sources.append(f'<source src="{_esc(variant.get("uri",""))}" type="{mime}">')
    return f'<video data-cie-responsive-video playsinline muted preload="metadata"{poster}>'+"".join(sources)+"</video>"

def render_runtime_media_markup(binding: Mapping[str, Any]) -> str:
    media_type=str(binding.get("media_type","image"))
    if media_type=="image": content=_image_markup(binding)
    elif media_type=="video": content=_video_markup(binding)
    elif media_type=="model-3d": content=render_model_viewer(binding)
    elif media_type=="svg":
        variants=[v for v in binding.get("variants",[]) if isinstance(v,Mapping)]; src=variants[0].get("uri","") if variants else ""; content=f'<img src="{_esc(src)}" alt="{_esc(binding.get("alt",""))}" loading="lazy" decoding="async">'
    else: return ""
    caption=f'<figcaption>{_esc(binding.get("caption"))}</figcaption>' if binding.get("caption") else ""
    return f'<figure class="cie-runtime-media cie-runtime-media--{_esc(media_type)}" data-cie-runtime-media="{_esc(binding.get("asset_id",""))}">{content}{caption}</figure>'

def bind_runtime_media_document(document: str, delivery: Mapping[str, Any]) -> str:
    result=document
    for binding in delivery.get("bindings",[]) if isinstance(delivery,Mapping) else []:
        if not isinstance(binding,Mapping) or binding.get("status") not in {"ready","fallback-only"}: continue
        section_id=str(binding.get("section_id","")); markup=render_runtime_media_markup(binding)
        if not section_id or not markup: continue
        pattern=re.compile(rf'(<section\b[^>]*\bid="{re.escape(section_id)}"[^>]*>.*?)(</section>)',re.S); result,_=pattern.subn(lambda m:m.group(1)+markup+m.group(2),result,count=1)
    return result

def render_runtime_media_css(delivery: Mapping[str, Any]) -> str:
    if delivery.get("status")!="ready": return ""
    base=""".cie-runtime-media{margin:1.25rem 0;overflow:hidden;border-radius:var(--radius-md);background:var(--color-surface)}.cie-runtime-media :is(img,video,picture){display:block;inline-size:100%;max-inline-size:100%}.cie-runtime-media img,.cie-runtime-media video{block-size:auto;object-fit:cover}.cie-runtime-media figcaption{padding:.65rem .85rem;color:var(--color-muted);font-size:.875rem}@media (max-width:760px){.cie-runtime-media{margin-inline:calc(var(--page-gutter)*-.25)}}"""
    return base+"\n"+render_webgl_css()

def render_runtime_media_js(delivery: Mapping[str, Any]) -> str:
    if delivery.get("status")!="ready": return ""
    payload=json.dumps(delivery.get("selection_policy",{}),ensure_ascii=False,separators=(",",":")); native=f'''const RUOS_CIE_MEDIA_POLICY={payload};\nconst cieConnection=navigator.connection||navigator.mozConnection||navigator.webkitConnection;\nconst cieSaveData=Boolean(cieConnection&&cieConnection.saveData);\nconst cieReducedMedia=matchMedia('(prefers-reduced-motion: reduce)').matches;\nfor(const video of document.querySelectorAll('[data-cie-responsive-video]')){{if(cieSaveData||cieReducedMedia){{video.preload='none';video.removeAttribute('autoplay');}}}}\n'''
    return native+"\n"+render_webgl_runtime(delivery.get("selection_policy",{}))+"\n"+render_camera_choreography_runtime(delivery.get("camera_choreography",{}))+"\n"+render_mesh_state_runtime(delivery.get("mesh_state_plan",{}))


def apply_runtime_media_delivery(output_dir: Path,page: PageSpec,delivery: Mapping[str, Any],artifacts: Mapping[str, Path],implementation_contract: Mapping[str, Any],strict: bool=True,post_lod_gate: Mapping[str, Any] | None=None) -> tuple[Path,...]:
    for relative,source in artifacts.items():
        target=output_dir/relative; target.parent.mkdir(parents=True,exist_ok=True)
        if source.resolve()!=target.resolve(): shutil.copy2(source,target)
    index=output_dir/"index.html"; styles=output_dir/"assets/styles.css"; runtime=output_dir/"assets/runtime.js"
    html_text=bind_runtime_media_document(index.read_text(encoding="utf-8"),delivery); css_text=styles.read_text(encoding="utf-8").rstrip()+"\n\n"+render_runtime_media_css(delivery)+"\n"; js_text=runtime.read_text(encoding="utf-8").rstrip()+"\n\n"+render_runtime_media_js(delivery)+"\n"
    index.write_text(html_text,encoding="utf-8"); styles.write_text(css_text,encoding="utf-8"); runtime.write_text(js_text,encoding="utf-8")
    contract_path=output_dir/"assets/cie-implementation-contract.json"; contract_path.write_text(json.dumps(implementation_contract,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    gates=evaluate(page,html_text,css_text,js_text); rejected=[gate for gate in gates if not gate.passed]
    if strict and rejected: raise ValueError("CIE runtime media binding QA blocked: "+"; ".join(f"{gate.gate}: {', '.join(gate.failures)}" for gate in rejected))
    qa_path=output_dir/"qa-report.json"; qa_path.write_text(json.dumps([asdict(gate) for gate in gates],ensure_ascii=False,indent=2),encoding="utf-8")
    manifest_path=output_dir/"build-manifest.json"; manifest=json.loads(manifest_path.read_text(encoding="utf-8")); tracked=[path for path in output_dir.rglob("*") if path.is_file() and path.name not in {".ruos-build","build-manifest.json"}]; sha={str(path.relative_to(output_dir)).replace("\\","/"):hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked}
    manifest["files"]=sorted(sha); manifest["sha256"]=sha; manifest["artifacts"]={**dict(manifest.get("artifacts",{})),**sha}; manifest["gates"]=[asdict(gate) for gate in gates]; manifest["cie_runtime_media"]={"status":delivery.get("status"),"version":delivery.get("version"),"binding_count":len(delivery.get("bindings",[])),"webgl_runtime":"progressive-model-viewer","hotspot_state_sync":True,"camera_choreography":delivery.get("camera_choreography",{}).get("status","not-applicable"),"mesh_state_plan":delivery.get("mesh_state_plan",{}).get("status","not-applicable")}; manifest["cie_post_lod_qa"]=dict(post_lod_gate or {"status":"not-applicable","runtime_delivery_blocking":True,"sections":[]}); manifest["build_id"]=hashlib.sha256(json.dumps(sha,sort_keys=True,separators=(",",":")).encode("utf-8")).hexdigest()[:16]
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8"); (output_dir/".ruos-build").write_text(str(manifest["build_id"])+"\n",encoding="utf-8")
    return tuple(output_dir/relative for relative in sorted(sha))+(manifest_path,)
