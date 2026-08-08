from __future__ import annotations

import html
import json
import re
from typing import Any, Mapping


class CIERenderAdapterError(ValueError):
    """Raised when a ready UI contract cannot be applied to rendered artifacts."""


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _section_index(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    sections = contract.get("sections", [])
    if contract.get("status") != "ready" or not isinstance(sections, list):
        raise CIERenderAdapterError("CIE UI implementation contract must be ready before rendering")
    result: dict[str, Mapping[str, Any]] = {}
    for section in sections:
        if not isinstance(section, Mapping):
            raise CIERenderAdapterError("CIE section implementation contracts must be objects")
        section_id = str(section.get("section_id", "")).strip()
        if not section_id or section_id in result:
            raise CIERenderAdapterError("CIE section contracts require unique section_id values")
        result[section_id] = section
    return result


def apply_cie_document_contract(html_text: str, contract: Mapping[str, Any]) -> str:
    """Bind CIE section contracts to semantic section roots without replacing source content."""
    sections = _section_index(contract)
    output = html_text
    for section_id, spec in sections.items():
        component = spec.get("component", {}) if isinstance(spec.get("component"), Mapping) else {}
        interaction = spec.get("interaction_hooks", {}) if isinstance(spec.get("interaction_hooks"), Mapping) else {}
        motion = spec.get("motion_hooks", {}) if isinstance(spec.get("motion_hooks"), Mapping) else {}
        responsive = spec.get("responsive", {}) if isinstance(spec.get("responsive"), Mapping) else {}
        attrs = {
            "data-cie-contract": "applied",
            "data-cie-section": section_id,
            "data-cie-variant": component.get("variant", ""),
            "data-cie-interaction": interaction.get("mode", "none"),
            "data-cie-motion": motion.get("effect", "none") if motion.get("enabled") else "none",
            "data-cie-touch-min": responsive.get("touch_targets_min_px", 44),
        }
        encoded = " ".join(f'{key}="{_esc(value)}"' for key, value in attrs.items())
        pattern = re.compile(rf'(<section\s+id="{re.escape(section_id)}"\b)')
        output, count = pattern.subn(rf'\1 {encoded}', output, count=1)
        if count != 1:
            raise CIERenderAdapterError(f"Rendered HTML is missing section '{section_id}' required by CIE")
    output = output.replace("<main id=\"main\">", '<main id="main" data-cie-renderer="implementation-contract">', 1)
    return output


def apply_cie_css_contract(css_text: str, contract: Mapping[str, Any]) -> str:
    sections = _section_index(contract)
    rules: list[str] = [
        "/* CIE implementation contract adapter */",
        '[data-cie-contract="applied"]{container-type:inline-size}',
        '[data-cie-contract="applied"] :is(a,button,[role="button"]){min-inline-size:44px;min-block-size:44px}',
        '@media (prefers-reduced-motion:reduce){[data-cie-contract="applied"],[data-cie-contract="applied"] *{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}}',
    ]
    for section_id, spec in sections.items():
        css = spec.get("css", {}) if isinstance(spec.get("css"), Mapping) else {}
        responsive = spec.get("responsive", {}) if isinstance(spec.get("responsive"), Mapping) else {}
        layout = str(css.get("layout", "flow"))
        surface = str(css.get("surface", "default"))
        rules.append(f'#{section_id}[data-cie-contract="applied"]{{--cie-layout:{json.dumps(layout)};--cie-surface:{json.dumps(surface)};}}')
        if bool(responsive.get("content_parity_required", True)):
            rules.append(f'#{section_id}[data-cie-contract="applied"] [data-desktop-only]{{display:revert}}')
    return css_text.rstrip() + "\n\n" + "\n".join(rules) + "\n"


def apply_cie_runtime_contract(runtime_text: str, contract: Mapping[str, Any]) -> str:
    sections = _section_index(contract)
    runtime_manifest = {
        section_id: {
            "interaction": spec.get("interaction_hooks", {}),
            "motion": spec.get("motion_hooks", {}),
            "responsive": spec.get("responsive", {}),
            "qa": spec.get("qa_assertions", []),
        }
        for section_id, spec in sections.items()
    }
    payload = json.dumps(runtime_manifest, ensure_ascii=False, separators=(",", ":"))
    adapter = f'''
const RUOS_CIE_IMPLEMENTATION={payload};
for(const [sectionId,contract] of Object.entries(RUOS_CIE_IMPLEMENTATION)){{
  const section=document.getElementById(sectionId); if(!section) continue;
  section.dataset.cieRuntime='bound';
  section.style.setProperty('--cie-touch-min',`${{Number(contract.responsive.touch_targets_min_px||44)}}px`);
  for(const control of section.querySelectorAll('a,button,[role="button"]')){{
    control.style.minWidth=`var(--cie-touch-min)`; control.style.minHeight=`var(--cie-touch-min)`;
  }}
  if(contract.interaction.keyboard_required){{
    section.addEventListener('keydown',event=>{{if(event.key==='Enter'||event.key===' ') section.dataset.cieKeyboard='active';}});
  }}
}}
'''.strip()
    return runtime_text.rstrip() + "\n\n" + adapter + "\n"


def apply_cie_render_contract(html_text: str, css_text: str, runtime_text: str, contract: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        apply_cie_document_contract(html_text, contract),
        apply_cie_css_contract(css_text, contract),
        apply_cie_runtime_contract(runtime_text, contract),
    )
