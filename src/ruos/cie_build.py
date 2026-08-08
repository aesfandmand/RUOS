from __future__ import annotations

import json
from pathlib import Path

from .cie_asset_media import build_asset_media_plan
from .cie_asset_registry import build_asset_source_registry
from .cie_director import build_creative_director_plan
from .cie_experience_patterns import build_experience_pattern_plan
from .cie_gate import build_creative_blueprint
from .cie_implementation import build_ui_implementation_contract
from .cie_providers import ProviderContext, run_provider_pipeline
from .cie_scene_orchestrator import build_scene_orchestration_plan
from .cie_visual_scene_composer import build_visual_scene_composition
from .compiler import BuildRejected, compile_page
from .component_resolver import resolve_components
from .content_composer import compose_content
from .creative_intelligence import build_creative_intelligence
from .models import BuildContext, BuildResult, PageSpec
from .motion_composer import compose_motion
from .pattern_resolver import resolve_patterns


def generate_cie_blueprint(page: PageSpec) -> dict[str, object]:
    content=compose_content(page); intelligence=build_creative_intelligence(page,content); components=resolve_components(page); patterns=resolve_patterns(page,components); motion=compose_motion(patterns,components)
    blueprint=build_creative_blueprint(page,content,intelligence,patterns,motion)
    references=tuple({"name":str(item.get("reference","")),"url":str(item.get("source_url","")),"principle":str(item.get("observed_principle",""))} for item in blueprint.get("reference_translation",[]) if isinstance(item,dict))
    provider_pipeline=run_provider_pipeline(ProviderContext(page=page,content=content,intelligence=intelligence,patterns=patterns,motion=motion,references=references)); blueprint["provider_pipeline"]=provider_pipeline
    creative_director=build_creative_director_plan(page=page,content=content,intelligence=intelligence,patterns=patterns,motion=motion,provider_pipeline=provider_pipeline); blueprint["creative_director"]=creative_director
    experience_patterns=build_experience_pattern_plan(page,creative_director); blueprint["experience_patterns"]=experience_patterns
    scene_orchestration=build_scene_orchestration_plan(page,experience_patterns); blueprint["scene_orchestration"]=scene_orchestration
    visual_scene_composition=build_visual_scene_composition(page,scene_orchestration); blueprint["visual_scene_composition"]=visual_scene_composition
    asset_media_plan=build_asset_media_plan(page,visual_scene_composition); blueprint["asset_media_plan"]=asset_media_plan
    asset_source_registry=build_asset_source_registry(asset_media_plan); blueprint["asset_source_registry"]=asset_source_registry
    implementation=build_ui_implementation_contract(page=page,components=components,creative_director=creative_director,experience_patterns=experience_patterns,scene_orchestration=scene_orchestration,visual_scene_composition=visual_scene_composition)
    implementation["asset_media_plan"]=asset_media_plan
    implementation["asset_source_registry_ref"]={"status":asset_source_registry.get("status","blocked"),"version":asset_source_registry.get("version","1.0"),"artifact":"creative-blueprint.json#asset_source_registry"}
    implementation.setdefault("global_contract",{})["asset_media_progressive_enhancement_required"]=True
    blueprint["ui_implementation_contract"]=implementation
    return blueprint


def write_cie_blueprint(page: PageSpec, output_root: Path) -> Path:
    blueprint=generate_cie_blueprint(page); output=output_root/page.slug/"creative-blueprint.json"; output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(blueprint,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8"); return output


def compile_page_with_cie(page: PageSpec, context: BuildContext) -> BuildResult:
    blueprint=generate_cie_blueprint(page); gate=blueprint["gate"]; status=str(gate.get("status","blocked"))
    if status=="blocked":
        failed=", ".join(str(item) for item in gate.get("failed_rules",[])) or "unknown CIE gate failure"; report=blueprint.get("gate_report",{}); remediation="; ".join(str(item) for item in report.get("remediation_actions",[])); detail=f"CIE pre-build gate blocked: {failed}"
        if remediation: detail+=f"; remediation: {remediation}"
        raise BuildRejected(detail)
    provider_pipeline=blueprint.get("provider_pipeline",{})
    if not isinstance(provider_pipeline,dict) or provider_pipeline.get("synthesis",{}).get("status")!="ready": raise BuildRejected("CIE provider pipeline is not ready for synthesis")
    director=blueprint.get("creative_director",{})
    if not isinstance(director,dict) or director.get("status")!="ready": raise BuildRejected("CIE Creative Director did not produce executable section decisions")
    experience=blueprint.get("experience_patterns",{})
    if not isinstance(experience,dict) or experience.get("status")!="ready": raise BuildRejected("CIE Experience Pattern Engine did not resolve every section")
    scenes=blueprint.get("scene_orchestration",{})
    if not isinstance(scenes,dict) or scenes.get("status")!="ready": raise BuildRejected("CIE Scene Orchestration Engine did not resolve every section")
    visual=blueprint.get("visual_scene_composition",{})
    if not isinstance(visual,dict) or visual.get("status")!="ready": raise BuildRejected("CIE Visual Scene Composition Engine did not resolve every section")
    assets=blueprint.get("asset_media_plan",{})
    if not isinstance(assets,dict) or assets.get("status")!="ready": raise BuildRejected("CIE Asset Media Engine did not resolve every section")
    registry=blueprint.get("asset_source_registry",{})
    if not isinstance(registry,dict) or registry.get("status")!="ready": raise BuildRejected("CIE Asset Source Registry is incomplete")
    implementation=blueprint.get("ui_implementation_contract",{})
    if not isinstance(implementation,dict) or implementation.get("status")!="ready": raise BuildRejected("CIE UI implementation contract is incomplete")
    result=compile_page(page,context,implementation_contract=implementation)
    blueprint["renderer"]={"status":"native-contract-driven","target_artifacts":["index.html","assets/styles.css","assets/runtime.js","assets/cie-implementation-contract.json"],"post_render_qa":"passed" if all(item.passed for item in result.gates) else "failed","legacy_adapter_required":False,"experience_pattern_engine":"applied","scene_orchestration_engine":"applied","visual_scene_composition_engine":"applied","asset_media_engine":"applied","asset_source_registry":"applied","webgl_mode":"progressive-enhancement"}
    blueprint_path=result.output_dir/"creative-blueprint.json"; blueprint_path.write_text(json.dumps(blueprint,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8")
    return BuildResult(page=result.page,output_dir=result.output_dir,files=result.files+(blueprint_path,),gates=result.gates)
