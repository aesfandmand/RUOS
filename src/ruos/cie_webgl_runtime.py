from __future__ import annotations

import html
import json
from typing import Any, Mapping

MODEL_VIEWER_MODULE = "https://ajax.googleapis.com/ajax/libs/model-viewer/4.0.0/model-viewer.min.js"


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_model_viewer(binding: Mapping[str, Any]) -> str:
    variants = [item for item in binding.get("variants", []) if isinstance(item, Mapping)]
    by_lod = {str(item.get("lod", "high")): str(item.get("uri", "")) for item in variants if item.get("uri")}
    default_src = by_lod.get("medium") or by_lod.get("high") or ""
    poster = str(binding.get("poster_uri") or "")
    hotspots = [item for item in binding.get("hotspots", []) if isinstance(item, Mapping)]
    hotspot_markup: list[str] = []
    for index, spot in enumerate(hotspots, start=1):
        spot_id = str(spot.get("id") or spot.get("entity") or f"hotspot-{index}")
        label = str(spot.get("label") or spot.get("entity") or spot_id)
        position = str(spot.get("position") or "0m 0m 0m")
        normal = str(spot.get("normal") or "0m 1m 0m")
        state = str(spot.get("state") or spot_id)
        hotspot_markup.append(
            f'<button class="cie-model-hotspot" slot="hotspot-{_esc(spot_id)}" '
            f'data-position="{_esc(position)}" data-normal="{_esc(normal)}" '
            f'data-cie-model-hotspot="{_esc(spot_id)}" data-cie-state-target="{_esc(state)}" '
            f'aria-label="{_esc(label)}"><span>{_esc(label)}</span></button>'
        )
    attrs = [
        'data-cie-model-viewer',
        f'data-cie-model-high="{_esc(by_lod.get("high", ""))}"',
        f'data-cie-model-medium="{_esc(by_lod.get("medium", ""))}"',
        f'data-cie-model-poster="{_esc(poster)}"',
        'camera-controls',
        'interaction-prompt="none"',
        'shadow-intensity="0.65"',
        'environment-image="neutral"',
        'loading="lazy"',
        'reveal="interaction"',
    ]
    if default_src:
        attrs.append(f'src="{_esc(default_src)}"')
    if poster:
        attrs.append(f'poster="{_esc(poster)}"')
    fallback = f'<img class="cie-model-fallback" src="{_esc(poster)}" alt="{_esc(binding.get("alt", ""))}">' if poster else '<span class="cie-model-fallback" aria-hidden="true"></span>'
    return f'<model-viewer {" ".join(attrs)}>{"".join(hotspot_markup)}{fallback}</model-viewer>'


def render_webgl_css() -> str:
    return """
[data-cie-model-viewer]{display:block;inline-size:100%;min-block-size:22rem;background:var(--color-surface);--poster-color:transparent}
.cie-model-hotspot{appearance:none;border:1px solid color-mix(in srgb,var(--color-accent) 55%,white);background:var(--color-bg);color:var(--color-ink);border-radius:999px;min-inline-size:44px;min-block-size:44px;padding:.45rem .65rem;box-shadow:0 8px 24px rgb(0 0 0/.18);cursor:pointer}
.cie-model-hotspot[aria-pressed="true"]{background:var(--color-accent);color:var(--color-accent-ink)}
.cie-model-hotspot span{white-space:nowrap;font-size:.78rem}.cie-model-fallback{display:block;inline-size:100%;block-size:auto;object-fit:cover}
@media (max-width:760px){[data-cie-model-viewer]{min-block-size:17rem}}
@media (prefers-reduced-motion:reduce){[data-cie-model-viewer]{pointer-events:none}.cie-model-hotspot{pointer-events:auto}}
""".strip()


def render_webgl_runtime(selection_policy: Mapping[str, Any] | None = None) -> str:
    policy = json.dumps(dict(selection_policy or {}), ensure_ascii=False, separators=(",", ":"))
    return f'''const RUOS_CIE_WEBGL_POLICY={policy};
const cieWebGLCanvas=document.createElement('canvas');
const cieWebGLCapable=Boolean(cieWebGLCanvas.getContext('webgl2')||cieWebGLCanvas.getContext('webgl'));
const cieConn=navigator.connection||navigator.mozConnection||navigator.webkitConnection;
const cieSaveDataWebGL=Boolean(cieConn&&cieConn.saveData);
const cieEffectiveWebGL=String(cieConn&&cieConn.effectiveType||'4g');
const cieReducedWebGL=matchMedia('(prefers-reduced-motion: reduce)').matches;
const cieModelViewers=[...document.querySelectorAll('[data-cie-model-viewer]')];
async function cieEnsureModelViewer(){{
  if(!cieModelViewers.length||!cieWebGLCapable||cieSaveDataWebGL)return false;
  if(customElements.get('model-viewer'))return true;
  try{{await import('{MODEL_VIEWER_MODULE}');return Boolean(customElements.get('model-viewer'));}}catch(error){{console.warn('RUOS CIE model-viewer unavailable',error);return false;}}
}}
function cieSelectModelSource(viewer){{
  let lod='high';
  if(cieSaveDataWebGL||/2g/.test(cieEffectiveWebGL)||!cieWebGLCapable)lod='poster';
  else if(/3g/.test(cieEffectiveWebGL)||innerWidth<900)lod='medium';
  const source=lod==='high'?viewer.dataset.cieModelHigh:lod==='medium'?(viewer.dataset.cieModelMedium||viewer.dataset.cieModelHigh):'';
  if(source&&viewer.getAttribute('src')!==source)viewer.setAttribute('src',source);
  viewer.dataset.cieSelectedLod=lod;viewer.dataset.cieWebgl=source?'active':'fallback';
  if(cieReducedWebGL)viewer.removeAttribute('auto-rotate');
}}
function cieSyncHotspots(viewer){{
  const section=viewer.closest('[data-cie-section]');
  for(const button of viewer.querySelectorAll('[data-cie-model-hotspot]')){{
    button.addEventListener('click',()=>{{
      for(const peer of viewer.querySelectorAll('[data-cie-model-hotspot]'))peer.setAttribute('aria-pressed','false');
      button.setAttribute('aria-pressed','true');
      const next=button.dataset.cieStateTarget||button.dataset.cieModelHotspot||'';
      if(section){{section.dataset.cieState=next;section.dispatchEvent(new CustomEvent('cie:hotspot-change',{{bubbles:true,detail:{{state:next,hotspot:button.dataset.cieModelHotspot}}}}));}}
    }});
  }}
  if(!section)return;
  const sync=()=>{{const state=section.dataset.cieState||'';for(const button of viewer.querySelectorAll('[data-cie-model-hotspot]'))button.setAttribute('aria-pressed',String(button.dataset.cieStateTarget===state));}};
  sync();new MutationObserver(sync).observe(section,{{attributes:true,attributeFilter:['data-cie-state']}});
}}
cieEnsureModelViewer().then(ready=>{{for(const viewer of cieModelViewers){{cieSelectModelSource(viewer);cieSyncHotspots(viewer);if(!ready)viewer.dataset.cieWebgl='fallback';}}}});
addEventListener('resize',()=>{{for(const viewer of cieModelViewers)cieSelectModelSource(viewer);}},{{passive:true}});
'''
