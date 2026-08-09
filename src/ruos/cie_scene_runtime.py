from __future__ import annotations

import json
from typing import Any, Mapping


def render_scene_runtime(contract: Mapping[str, Any]) -> str:
    sections=contract.get("sections",[]) if isinstance(contract,Mapping) else []
    payload={}
    if isinstance(sections,list):
        for item in sections:
            if not isinstance(item,Mapping): continue
            section_id=str(item.get("section_id","")).strip(); scene=item.get("scene_orchestration",{})
            if section_id and isinstance(scene,Mapping): payload[section_id]=scene
    encoded=json.dumps(payload,ensure_ascii=False,separators=(",",":"))
    return f'''\nconst RUOS_CIE_SCENES={encoded};
const cieSceneReduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
function cieSceneProgress(section){{const r=section.getBoundingClientRect();const span=Math.max(1,r.height+innerHeight);return Math.max(0,Math.min(1,(innerHeight-r.top)/span));}}
function cieApplyScene(section,plan,progress){{const scenes=Array.isArray(plan.scenes)?plan.scenes:[];let active=scenes[0];for(const scene of scenes){{const range=scene.range||[0,1];if(progress>=Number(range[0])&&progress<=Number(range[1])){{active=scene;break;}}}}if(!active)return;section.dataset.cieScene=String(active.id||'scene');section.dataset.cieState=String(active.state||'state');section.style.setProperty('--cie-scene-progress',String(progress));const cta=section.querySelector('[data-cie-cta]');if(cta)cta.dataset.cieSceneVisible=String((active.actions||[]).includes('reveal-cta')||(active.actions||[]).includes('reveal-next-action'));if(cieSceneReduced)section.style.setProperty('--cie-scene-motion','0');else section.style.setProperty('--cie-scene-motion',String(progress));}}
const cieSceneSections=[];for(const [id,plan] of Object.entries(RUOS_CIE_SCENES)){{const section=document.getElementById(id);if(section){{cieSceneSections.push([section,plan]);cieApplyScene(section,plan,0);}}}}
let cieSceneTick=false;function cieUpdateScenes(){{cieSceneTick=false;for(const [section,plan] of cieSceneSections)cieApplyScene(section,plan,cieSceneProgress(section));}}
addEventListener('scroll',()=>{{if(!cieSceneTick){{cieSceneTick=true;requestAnimationFrame(cieUpdateScenes);}}}},{{passive:true}});addEventListener('resize',cieUpdateScenes,{{passive:true}});cieUpdateScenes();
'''.strip()
