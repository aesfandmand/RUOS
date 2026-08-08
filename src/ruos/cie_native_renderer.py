from __future__ import annotations

import html
import json
from typing import Any, Mapping

from .component_resolver import ComponentPlan
from .models import PageSpec, SectionSpec
from .render import render_css, render_runtime
from .visual_dna import VisualDNA


class CIEContractRenderError(ValueError):
    """Raised when a ready implementation contract cannot drive native rendering."""


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _section_contracts(contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if contract.get("status") != "ready":
        raise CIEContractRenderError("UI implementation contract must be ready")
    sections = contract.get("sections", [])
    if not isinstance(sections, list):
        raise CIEContractRenderError("UI implementation sections must be a list")
    indexed: dict[str, Mapping[str, Any]] = {}
    for item in sections:
        if not isinstance(item, Mapping):
            raise CIEContractRenderError("Every UI implementation section must be an object")
        section_id = str(item.get("section_id", "")).strip()
        if not section_id or section_id in indexed:
            raise CIEContractRenderError("UI implementation section ids must be unique")
        indexed[section_id] = item
    return indexed


def _items(section: SectionSpec) -> str:
    if not section.items:
        return ""
    rendered: list[str] = []
    for index, item in enumerate(section.items, start=1):
        rendered.append(
            '<article class="ruos-item cie-native-item" data-cie-item>'
            f'<span class="ruos-item__index" aria-hidden="true">{index:02d}</span>'
            f'<h3>{_esc(item.get("title", ""))}</h3>'
            f'<p>{_esc(item.get("body", ""))}</p>'
            '</article>'
        )
    return '<div class="ruos-items cie-native-collection" data-cie-collection>' + "".join(rendered) + "</div>"


def _hero_art() -> str:
    return (
        '<div class="ruos-hero-art cie-native-hero-art" data-cie-asset-slot="hero-art" aria-hidden="true">'
        '<i></i><i></i><i></i><span></span>'
        '</div>'
    )


def _decision_console(section: SectionSpec) -> str:
    if section.kind != "interaction":
        return ""
    return (
        '<div class="ruos-decision-console cie-native-console" role="group" '
        'aria-label="مسیرهای انتخاب سازه" data-cie-interaction-surface>'
        '<button type="button" data-choice="indoor">فضای داخلی</button>'
        '<button type="button" data-choice="outdoor">فضای شهری</button>'
        '<button type="button" data-choice="digital">نمایش دیجیتال</button>'
        '<output aria-live="polite">یک مسیر را انتخاب کنید تا زمینه تصمیم روشن شود.</output>'
        '</div>'
    )


def _industrial_layers(section: SectionSpec, spec: Mapping[str, Any]) -> str:
    evidence = {str(item) for item in spec.get("evidence", [])}
    if "industrial-product-provider-required" not in evidence:
        return ""
    return (
        '<div class="cie-structure-anatomy" data-cie-industrial-anatomy aria-label="لایه‌های اطلاعات سازه">'
        '<button type="button" data-cie-hotspot="structure" aria-pressed="false">سازه</button>'
        '<button type="button" data-cie-hotspot="foundation" aria-pressed="false">فونداسیون</button>'
        '<button type="button" data-cie-hotspot="lighting" aria-pressed="false">نورپردازی</button>'
        '<button type="button" data-cie-hotspot="placement" aria-pressed="false">جانمایی</button>'
        f'<output data-cie-hotspot-output aria-live="polite">{_esc(section.title)}</output>'
        '</div>'
    )


def _cta(section: SectionSpec) -> str:
    if not (section.cta_label and section.cta_href):
        return ""
    return (
        f'<a class="ruos-cta cie-native-cta" href="{_esc(section.cta_href)}" data-cie-cta>'
        f'<span>{_esc(section.cta_label)}</span><span aria-hidden="true">↙</span></a>'
    )


def _section_markup(section: SectionSpec, component: Any, spec: Mapping[str, Any], index: int) -> str:
    dom = spec.get("dom", {}) if isinstance(spec.get("dom"), Mapping) else {}
    interaction = spec.get("interaction_hooks", {}) if isinstance(spec.get("interaction_hooks"), Mapping) else {}
    motion = spec.get("motion_hooks", {}) if isinstance(spec.get("motion_hooks"), Mapping) else {}
    responsive = spec.get("responsive", {}) if isinstance(spec.get("responsive"), Mapping) else {}
    css = spec.get("css", {}) if isinstance(spec.get("css"), Mapping) else {}
    heading_meta = dom.get("heading", {}) if isinstance(dom.get("heading"), Mapping) else {}
    heading_level = str(heading_meta.get("semantic_level", "h2"))
    if heading_level not in {"h1", "h2", "h3"}:
        heading_level = "h2"
    variant = str(component.variant)
    attributes = {
        "id": section.id,
        "class": f"ruos-section ruos-section--{section.kind} ruos-component ruos-component--{component.family} ruos-component--{variant} cie-native-section",
        "data-section-kind": section.kind,
        "data-component-id": component.id,
        "data-component-family": component.family,
        "data-component-variant": variant,
        "data-component-density": component.density,
        "data-component-emphasis": component.emphasis,
        "data-cie-contract": "native",
        "data-cie-section": section.id,
        "data-cie-variant": variant,
        "data-cie-layout": css.get("layout", "flow"),
        "data-cie-surface": css.get("surface", "default"),
        "data-cie-interaction": interaction.get("mode", "none"),
        "data-cie-motion": motion.get("effect", "none") if motion.get("enabled") else "none",
        "data-cie-touch-min": responsive.get("touch_targets_min_px", 44),
    }
    attrs = " ".join(f'{key}="{_esc(value)}"' for key, value in attributes.items())
    eyebrow = f'<p class="ruos-eyebrow">{_esc(section.eyebrow)}</p>' if section.eyebrow else ""
    body = f'<div class="ruos-copy" data-cie-content><p>{_esc(section.body)}</p></div>' if section.body else ""
    art = _hero_art() if component.family == "hero" else ""
    section_items = _items(section)
    console = _decision_console(section)
    industrial = _industrial_layers(section, spec)
    cta = _cta(section)
    return (
        f'<section {attrs}>'
        '<div class="ruos-shell ruos-section__grid cie-native-stage" data-cie-stage>'
        f'<div class="ruos-section__marker" aria-hidden="true">{index:02d}</div>'
        '<div class="ruos-section__content">'
        f'{eyebrow}<{heading_level}>{_esc(section.title)}</{heading_level}>{body}{section_items}{console}{industrial}{cta}'
        '</div>'
        f'{art}'
        '</div></section>'
    )


def render_document_from_contract(page: PageSpec, components: ComponentPlan, contract: Mapping[str, Any]) -> str:
    section_specs = _section_contracts(contract)
    missing = [section.id for section in page.sections if section.id not in section_specs]
    if missing:
        raise CIEContractRenderError("Implementation contract missing sections: " + ", ".join(missing))
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page.title,
        "description": page.description,
        "inLanguage": page.lang,
        "isPartOf": {"@type": "WebSite", "name": page.brand},
    }
    body = "".join(
        _section_markup(section, components.for_section(section.id), section_specs[section.id], index)
        for index, section in enumerate(page.sections, start=1)
    )
    nav = "".join(
        f'<a href="#{_esc(section.id)}">{_esc(section.eyebrow or section.title)}</a>'
        for section in page.sections
    )
    return f'''<!doctype html>
<html lang="{_esc(page.lang)}" dir="{_esc(page.direction)}" data-visual-profile="{_esc(page.visual_profile)}" data-cie-renderer="native-contract">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#17161B">
<title>{_esc(page.title)}</title>
<meta name="description" content="{_esc(page.description)}">
<link rel="stylesheet" href="assets/styles.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip-link" href="#main">پرش به محتوای اصلی</a>
<div class="ruos-progress" aria-hidden="true"><span></span></div>
<header class="ruos-header">
  <div class="ruos-shell ruos-header__inner">
    <a class="ruos-brand" href="#hero" aria-label="{_esc(page.brand)}، صفحه اصلی"><i aria-hidden="true"></i><strong>{_esc(page.brand)}</strong></a>
    <nav class="ruos-nav" aria-label="بخش‌های صفحه">{nav}</nav>
    <a class="ruos-header__cta" href="#conversion">گفت‌وگو</a>
  </div>
</header>
<main id="main" data-cie-native-main>{body}</main>
<nav class="ruos-bottom-nav" aria-label="ناوبری موبایل">
  <a href="#hero">شروع</a><a href="#knowledge">سازه‌ها</a><a href="#interaction">انتخاب</a><a href="#conversion">تماس</a>
</nav>
<script src="assets/runtime.js" defer></script>
</body>
</html>'''


def render_css_from_contract(dna: VisualDNA, contract: Mapping[str, Any]) -> str:
    _section_contracts(contract)
    base = render_css(dna)
    native = r'''
/* CIE native contract-driven renderer */
.cie-native-section{container-type:inline-size}
.cie-native-section :is(a,button,[role="button"]){min-inline-size:44px;min-block-size:44px}
.cie-native-stage{isolation:isolate}
.cie-structure-anatomy{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin-top:var(--space-4)}
.cie-structure-anatomy button{border:1px solid var(--color-line);background:var(--color-surface);color:var(--color-ink);padding:.8rem;border-radius:var(--radius-sm);cursor:pointer}
.cie-structure-anatomy button[aria-pressed="true"]{background:var(--color-accent);color:var(--color-accent-ink);border-color:var(--color-accent)}
.cie-structure-anatomy output{grid-column:1/-1;padding:1rem;border-inline-start:3px solid var(--color-accent);color:var(--color-muted)}
@container (max-width:46rem){.cie-structure-anatomy{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (max-width:760px){.cie-structure-anatomy{grid-template-columns:1fr 1fr}.cie-native-stage{min-width:0}}
@media (prefers-reduced-motion:reduce){.cie-native-section,.cie-native-section *{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important}}
'''.strip()
    return base.rstrip() + "\n\n" + native + "\n"


def render_runtime_from_contract(contract: Mapping[str, Any]) -> str:
    sections = _section_contracts(contract)
    payload = json.dumps(
        {
            key: {
                "interaction": value.get("interaction_hooks", {}),
                "motion": value.get("motion_hooks", {}),
                "responsive": value.get("responsive", {}),
                "qa": value.get("qa_assertions", []),
            }
            for key, value in sections.items()
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    native = f'''
const RUOS_CIE_NATIVE={payload};
for(const [sectionId,contract] of Object.entries(RUOS_CIE_NATIVE)){{
  const section=document.getElementById(sectionId); if(!section) continue;
  section.dataset.cieRuntime='native';
  const min=Math.max(44,Number(contract.responsive.touch_targets_min_px||44));
  section.style.setProperty('--cie-touch-min',`${{min}}px`);
  for(const control of section.querySelectorAll('a,button,[role="button"]')){{control.style.minWidth='var(--cie-touch-min)';control.style.minHeight='var(--cie-touch-min)';}}
}}
for(const anatomy of document.querySelectorAll('[data-cie-industrial-anatomy]')){{
  const output=anatomy.querySelector('[data-cie-hotspot-output]');
  for(const button of anatomy.querySelectorAll('[data-cie-hotspot]')){{
    button.addEventListener('click',()=>{{
      for(const peer of anatomy.querySelectorAll('[data-cie-hotspot]')) peer.setAttribute('aria-pressed','false');
      button.setAttribute('aria-pressed','true');
      if(output) output.textContent=button.textContent||'';
    }});
  }}
}}
'''.strip()
    return render_runtime().rstrip() + "\n\n" + native + "\n"
