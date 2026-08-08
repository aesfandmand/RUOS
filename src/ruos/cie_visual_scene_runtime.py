from __future__ import annotations

import json
from typing import Any, Mapping


def _sections(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw = contract.get("sections", [])
    if not isinstance(raw, list): return {}
    return {str(item.get("section_id")): item for item in raw if isinstance(item, Mapping) and item.get("section_id")}


def render_visual_scene_css(contract: Mapping[str, Any]) -> str:
    if not _sections(contract): return ""
    return r'''
/* CIE visual scene composition + asset media adapter */
[data-cie-visual-layer]{transition:opacity .42s cubic-bezier(.22,.61,.36,1),transform .42s cubic-bezier(.22,.61,.36,1);transform-origin:center}
[data-cie-visual-stage]{position:relative;isolation:isolate}
[data-cie-camera]{transform-origin:center;will-change:transform}
[data-cie-scene-visible="false"]{opacity:0;visibility:hidden;pointer-events:none}
[data-cie-scene-visible="true"]{opacity:1;visibility:visible}
[data-cie-visual-layer][data-cie-priority="decorative"]{pointer-events:none}
[data-cie-media-slot]{display:block;position:relative;overflow:hidden}
[data-cie-media-type="model-3d"]{contain:layout paint;min-block-size:12rem}
[data-cie-webgl="eligible"]::after{content:"";position:absolute;inset:0;pointer-events:none}
[data-cie-media-fallback="poster-image"]{background:linear-gradient(145deg,color-mix(in srgb,currentColor 5%,transparent),transparent)}
@media (max-width:760px){[data-cie-camera]{transform:none!important}[data-cie-visual-layer]{transition-duration:.2s}[data-cie-webgl="eligible"]{transform:none!important}}
@media (prefers-reduced-motion:reduce){[data-cie-camera],[data-cie-visual-layer]{transform:none!important;transition:none!important}[data-cie-scene-visible]{visibility:visible}[data-cie-webgl="eligible"]{transform:none!important}}
'''.strip() + "\n"


def render_visual_scene_runtime(contract: Mapping[str, Any]) -> str:
    sections = _sections(contract)
    payload: dict[str, Any] = {}
    for section_id, section in sections.items():
        composition = section.get("visual_scene_composition", {}) if isinstance(section.get("visual_scene_composition"), Mapping) else {}
        payload[section_id] = composition
    asset_plan = contract.get("asset_media_plan", {}) if isinstance(contract.get("asset_media_plan"), Mapping) else {}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    encoded_assets = json.dumps(asset_plan, ensure_ascii=False, separators=(",", ":"))
    return f'''
/* compatibility: contract.experience.pattern==='cinematic-scroll-stage' now delegates continuous transforms to visual scene composition */
const RUOS_CIE_VISUAL_SCENES={encoded};
const RUOS_CIE_SCENES=RUOS_CIE_VISUAL_SCENES;
const RUOS_CIE_ASSET_MEDIA={encoded_assets};
const cieSceneProgress=(section)=>{{const r=section.getBoundingClientRect();const total=Math.max(1,r.height+innerHeight);return Math.max(0,Math.min(1,(innerHeight-r.top)/total));}};
const cieVisualReduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
const cieVisualMobile=matchMedia('(max-width: 760px)').matches;
const cieWebGLCapable=(()=>{{try{{const canvas=document.createElement('canvas');return !!(canvas.getContext('webgl2')||canvas.getContext('webgl'));}}catch(_error){{return false;}}}})();
for(const sectionPlan of (RUOS_CIE_ASSET_MEDIA.sections||[])){{
  const section=document.getElementById(sectionPlan.section_id); if(!section) continue;
  section.dataset.cieAssetMedia='planned';
  for(const asset of (sectionPlan.assets||[])){{
    let slot=section.querySelector(`[data-cie-visual-layer="${{asset.asset_id}}"]`);
    if(!slot){{slot=document.createElement('span');slot.hidden=true;slot.dataset.cieVisualLayer=asset.asset_id;section.appendChild(slot);}}
    slot.dataset.cieMediaSlot=asset.asset_id; slot.dataset.cieMediaType=asset.media_type||'image';
    slot.dataset.cieMediaFallback=(cieVisualMobile||cieVisualReduce)?(asset.mobile_fallback||asset.reduced_motion_fallback||'static'):'none';
    const eligible=!!asset.webgl?.eligible; slot.dataset.cieWebgl=eligible?'eligible':'none';
    if(eligible){{slot.dataset.cieWebglState=(!cieVisualMobile&&!cieVisualReduce&&cieWebGLCapable)?'ready-for-source':'fallback';}}
    slot.dataset.cieLoading=asset.loading||'lazy';
  }}
}}
for(const [sectionId,composition] of Object.entries(RUOS_CIE_VISUAL_SCENES)){{
  const section=document.getElementById(sectionId); if(!section||!composition||!Array.isArray(composition.scenes)) continue;
  section.dataset.cieVisualComposition='active';
  section.dataset.cieVisualProgress=String(cieSceneProgress(section));
  const ensureLayer=(id,role,priority)=>{{
    let layer=section.querySelector(`[data-cie-visual-layer="${{id}}"]`);
    if(!layer){{layer=document.createElement('span');layer.hidden=true;layer.dataset.cieVisualLayer=id;layer.dataset.cieRole=role||'';layer.dataset.ciePriority=priority||'';layer.dataset.cieSceneVisible='false';section.appendChild(layer);}}
    return layer;
  }};
  for(const scene of composition.scenes) for(const layer of (scene.layers||[])) ensureLayer(layer.id,layer.role,layer.priority);
  const apply=()=>{{
    section.dataset.cieVisualProgress=String(cieSceneProgress(section));
    const activeState=section.dataset.cieState||composition.scenes[0]?.state;
    const scene=composition.scenes.find(item=>item.state===activeState)||composition.scenes[0]; if(!scene)return;
    section.dataset.cieVisualScene=scene.scene_id||'';
    const camera=scene.camera||{{}};
    const cameraTarget=section.querySelector('[data-cie-depth-layer]')||section.querySelector('[data-cie-stage]');
    if(cameraTarget&&!cieVisualReduce&&!cieVisualMobile){{cameraTarget.dataset.cieCamera='true';cameraTarget.style.transform=`translate3d(${{Number(camera.x||0)*24}}px,${{Number(camera.y||0)*24}}px,0) scale(${{Number(camera.z||1)}}) rotate(${{Number(camera.rotate||0)}}deg)`;}}
    for(const node of section.querySelectorAll('[data-cie-visual-layer]')){{node.hidden=true;node.dataset.cieSceneVisible='false';node.style.opacity='0';}}
    for(const layer of (scene.layers||[])){{const node=ensureLayer(layer.id,layer.role,layer.priority);node.hidden=false;node.dataset.cieSceneVisible='true';node.style.opacity=String(layer.opacity??1);if(!cieVisualReduce&&!cieVisualMobile)node.style.transform=`translateY(${{Number(layer.translate_y||0)}}px) scale(${{Number(layer.scale||1)}})`;}}
  }};
  apply();
  new MutationObserver(apply).observe(section,{{attributes:true,attributeFilter:['data-cie-state','data-cie-scene']}});
}}
'''.strip() + "\n"
