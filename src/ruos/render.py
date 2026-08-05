from __future__ import annotations

import html
import json
from collections.abc import Iterable

from .component_resolver import ComponentPlan, ComponentSpec
from .models import PageSpec, SectionSpec
from .visual_dna import VisualDNA


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _render_items(items: Iterable[dict[str, object]]) -> str:
    rendered: list[str] = []
    for index, item in enumerate(items, start=1):
        rendered.append(
            '<article class="ruos-item">'
            f'<span class="ruos-item__index" aria-hidden="true">{index:02d}</span>'
            f'<h3>{_esc(item.get("title", ""))}</h3>'
            f'<p>{_esc(item.get("body", ""))}</p>'
            '</article>'
        )
    return "".join(rendered)


def _component_attributes(component: ComponentSpec) -> str:
    values = {
        "data-component-id": component.id,
        "data-component-family": component.family,
        "data-component-variant": component.variant,
        "data-component-density": component.density,
        "data-component-emphasis": component.emphasis,
        "data-component-capabilities": " ".join(component.capabilities),
        **{f"data-component-{key.replace('_', '-')}": value for key, value in component.attributes.items()},
    }
    return " ".join(f'{key}="{_esc(value)}"' for key, value in sorted(values.items()))


def render_section(section: SectionSpec, component: ComponentSpec, index: int) -> str:
    classes = (
        f"ruos-section ruos-section--{_esc(section.kind)} "
        f"ruos-component ruos-component--{_esc(component.family)} "
        f"ruos-component--{_esc(component.variant)}"
    )
    eyebrow = f'<p class="ruos-eyebrow">{_esc(section.eyebrow)}</p>' if section.eyebrow else ""
    body = f'<div class="ruos-copy"><p>{_esc(section.body)}</p></div>' if section.body else ""
    items = f'<div class="ruos-items">{_render_items(section.items)}</div>' if section.items else ""
    cta = ""
    if section.cta_label and section.cta_href:
        cta = (
            f'<a class="ruos-cta" href="{_esc(section.cta_href)}">'
            f'<span>{_esc(section.cta_label)}</span><span aria-hidden="true">↙</span></a>'
        )
    art = ""
    if component.family == "hero":
        art = (
            '<div class="ruos-hero-art" aria-hidden="true">'
            '<i></i><i></i><i></i><span></span>'
            '</div>'
        )
    console = ""
    if component.variant == "decision-console":
        console = (
            '<div class="ruos-decision-console" role="group" aria-label="مسیرهای انتخاب سازه">'
            '<button type="button" data-choice="indoor">فضای داخلی</button>'
            '<button type="button" data-choice="outdoor">فضای شهری</button>'
            '<button type="button" data-choice="digital">نمایش دیجیتال</button>'
            '<output aria-live="polite">یک مسیر را انتخاب کنید تا زمینه تصمیم روشن شود.</output>'
            '</div>'
        )
    return (
        f'<section id="{_esc(section.id)}" class="{classes}" '
        f'data-section-kind="{_esc(section.kind)}" {_component_attributes(component)}>'
        '<div class="ruos-shell ruos-section__grid">'
        f'<div class="ruos-section__marker" aria-hidden="true">{index:02d}</div>'
        f'<div class="ruos-section__content">{eyebrow}<h2>{_esc(section.title)}</h2>{body}{items}{console}{cta}</div>'
        f'{art}'
        '</div></section>'
    )


def render_document(page: PageSpec, components: ComponentPlan) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page.title,
        "description": page.description,
        "inLanguage": page.lang,
        "isPartOf": {"@type": "WebSite", "name": page.brand},
    }
    body = "".join(
        render_section(section, components.for_section(section.id), index)
        for index, section in enumerate(page.sections, start=1)
    )
    nav = "".join(
        f'<a href="#{_esc(section.id)}">{_esc(section.eyebrow or section.title)}</a>'
        for section in page.sections
    )
    return f'''<!doctype html>
<html lang="{_esc(page.lang)}" dir="{_esc(page.direction)}" data-visual-profile="{_esc(page.visual_profile)}">
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
<main id="main">{body}</main>
<nav class="ruos-bottom-nav" aria-label="ناوبری موبایل">
  <a href="#hero">شروع</a><a href="#knowledge">سازه‌ها</a><a href="#interaction">انتخاب</a><a href="#conversion">تماس</a>
</nav>
<script src="assets/runtime.js" defer></script>
</body>
</html>'''


def render_css(dna: VisualDNA) -> str:
    return (dna.css_variables() + '''
*{box-sizing:border-box}
html{scroll-behavior:smooth;background:var(--color-dark)}
body{margin:0;background:var(--color-bg);color:var(--color-ink);font-family:var(--font-body);font-size:var(--font-size-body);line-height:var(--line-body);-webkit-font-smoothing:antialiased;overflow-x:hidden}
button{font:inherit}a{color:inherit}.ruos-shell{width:min(calc(100% - 3rem),var(--content-max));margin-inline:auto}
.skip-link{position:fixed;inset-inline-start:1rem;top:-5rem;z-index:100;background:var(--color-surface);padding:.75rem 1rem;border-radius:var(--radius-sm)}.skip-link:focus{top:1rem}
.ruos-progress{position:fixed;inset:0 0 auto;height:3px;z-index:100;background:transparent}.ruos-progress span{display:block;width:0;height:100%;background:var(--color-accent)}
.ruos-header{height:var(--header-height);position:fixed;inset:0 0 auto;z-index:50;background:color-mix(in srgb,var(--color-bg) 88%,transparent);backdrop-filter:blur(var(--blur-glass));border-bottom:1px solid color-mix(in srgb,var(--color-line) 75%,transparent)}
.ruos-header__inner{height:100%;display:grid;grid-template-columns:14rem 1fr 8rem;align-items:center;gap:2rem}.ruos-brand{display:flex;align-items:center;gap:.75rem;text-decoration:none}.ruos-brand i{width:1.1rem;height:1.4rem;background:var(--color-accent);border-radius:60% 60% 45% 45%;transform:rotate(12deg);box-shadow:.35rem .2rem 0 color-mix(in srgb,var(--color-accent) 50%,transparent)}
.ruos-nav{display:flex;justify-content:center;gap:.25rem}.ruos-nav a{padding:.55rem .7rem;border-radius:999px;text-decoration:none;font-size:.76rem;font-weight:800;color:var(--color-muted)}.ruos-nav a:hover,.ruos-nav a:focus-visible{background:var(--color-surface);color:var(--color-accent)}
.ruos-header__cta{justify-self:end;text-decoration:none;border:1px solid var(--color-line);padding:.55rem 1rem;border-radius:999px;font-weight:850}
.ruos-section{position:relative;min-height:100svh;padding:calc(var(--header-height) + var(--space-5)) 0 var(--space-6);display:flex;align-items:center;border-bottom:1px solid var(--color-line);overflow:hidden}.ruos-section__grid{position:relative;display:grid;grid-template-columns:minmax(3rem,9rem) minmax(0,1fr);gap:clamp(1.5rem,5vw,6rem)}.ruos-section__marker{font-size:clamp(2rem,5vw,5rem);font-weight:900;color:color-mix(in srgb,var(--color-ink) 12%,transparent);line-height:1}.ruos-section__content{position:relative;z-index:2;max-width:72rem}
.ruos-eyebrow{display:flex;align-items:center;gap:.75rem;color:var(--color-accent);font-size:.76rem;font-weight:900;letter-spacing:.02em;margin:0 0 var(--space-2)}.ruos-eyebrow::before{content:'';width:2rem;height:2px;background:currentColor}
.ruos-section h2{max-width:14ch;font-family:var(--font-display);font-size:clamp(2.6rem,7vw,7.6rem);line-height:var(--line-display);letter-spacing:var(--tracking-display);margin:0}.ruos-copy{max-width:var(--copy-max);margin-top:var(--space-4);font-size:clamp(1rem,1.3vw,1.25rem);color:var(--color-muted)}
.ruos-items{display:grid;grid-template-columns:repeat(var(--component-columns,3),minmax(0,1fr));gap:1px;background:var(--color-line);border:1px solid var(--color-line);border-radius:var(--radius-md);overflow:hidden;margin-top:var(--space-5);box-shadow:var(--shadow-soft)}.ruos-component[data-component-columns="2"]{--component-columns:2}.ruos-component[data-component-columns="3"]{--component-columns:3}.ruos-item{position:relative;background:var(--color-surface);padding:clamp(1.4rem,3vw,2.5rem);min-height:16rem}.ruos-item__index{display:block;color:var(--color-accent);font-weight:900;font-size:.75rem}.ruos-item h3{font-size:clamp(1.25rem,2vw,2rem);margin:2.5rem 0 .75rem}.ruos-item p{color:var(--color-muted);font-size:.9rem;margin:0}
.ruos-cta{display:inline-flex;align-items:center;justify-content:space-between;gap:2rem;min-width:min(100%,18rem);margin-top:var(--space-4);padding:.85rem 1.2rem;border-radius:999px;background:var(--color-accent);color:var(--color-accent-ink);text-decoration:none;font-weight:900;box-shadow:0 1rem 2.5rem color-mix(in srgb,var(--color-accent) 25%,transparent);transition:transform .3s var(--ease-emphasis),box-shadow .3s var(--ease-emphasis)}.ruos-cta:hover,.ruos-cta:focus-visible{transform:translateY(-3px);box-shadow:0 1.4rem 3.2rem color-mix(in srgb,var(--color-accent) 35%,transparent)}
.ruos-component--cinematic-orbit{padding-top:calc(var(--header-height) + var(--space-4));background:var(--color-dark);color:var(--color-dark-ink)}.ruos-component--cinematic-orbit .ruos-section__grid{grid-template-columns:minmax(3rem,7rem) minmax(0,1fr) minmax(18rem,34rem);align-items:center}.ruos-component--cinematic-orbit .ruos-section__marker{color:rgba(255,255,255,.16)}.ruos-component--cinematic-orbit h2{font-size:var(--font-size-display);max-width:11ch}.ruos-component--cinematic-orbit .ruos-copy{color:#C9C5CD}.ruos-hero-art{position:relative;aspect-ratio:1;border-radius:50%;border:1px solid rgba(255,255,255,.14);display:grid;place-items:center}.ruos-hero-art::before,.ruos-hero-art::after,.ruos-hero-art i{content:'';position:absolute;border-radius:50%;border:1px solid rgba(255,255,255,.13)}.ruos-hero-art::before{inset:12%}.ruos-hero-art::after{inset:26%}.ruos-hero-art i:nth-child(1){width:54%;height:18%;background:var(--color-accent);border:0;transform:rotate(-14deg)}.ruos-hero-art i:nth-child(2){width:24%;height:58%;border-width:clamp(.8rem,2vw,1.8rem);border-color:var(--color-gold);transform:rotate(24deg)}.ruos-hero-art i:nth-child(3){inset:38%;background:var(--color-surface);border:0;box-shadow:var(--shadow-lift)}.ruos-hero-art span{width:.9rem;height:.9rem;border-radius:50%;background:var(--color-accent);position:absolute;top:9%;left:31%;box-shadow:0 0 0 .65rem rgba(210,30,43,.18)}
.ruos-component--editorial-statement{background:var(--color-surface)}.ruos-component--editorial-statement .ruos-section__content{max-width:62rem}.ruos-component--knowledge-triptych,.ruos-component--knowledge-grid{background:linear-gradient(160deg,var(--color-bg),var(--color-surface))}
.ruos-component--decision-console{background:var(--color-dark);color:var(--color-dark-ink)}.ruos-component--decision-console .ruos-copy{color:#C9C5CD}.ruos-decision-console{display:grid;grid-template-columns:repeat(3,1fr);gap:.75rem;margin-top:var(--space-5)}.ruos-decision-console button{border:1px solid rgba(255,255,255,.16);background:rgba(255,255,255,.06);color:#fff;padding:1rem;border-radius:var(--radius-sm);cursor:pointer}.ruos-decision-console button:hover,.ruos-decision-console button:focus-visible,.ruos-decision-console button[aria-pressed="true"]{background:var(--color-accent);border-color:var(--color-accent)}.ruos-decision-console output{grid-column:1/-1;min-height:6rem;padding:1.25rem;border-radius:var(--radius-md);background:rgba(255,255,255,.08);color:#D8D4DC}
.ruos-component--closing-stage{background:var(--color-accent);color:var(--color-accent-ink)}.ruos-component--closing-stage .ruos-eyebrow,.ruos-component--closing-stage .ruos-copy{color:var(--color-accent-ink)}.ruos-component--closing-stage .ruos-cta{background:var(--color-dark);color:var(--color-dark-ink)}
.ruos-section[data-active] .ruos-section__content{animation:ruos-rise .8s var(--ease-emphasis) both}.ruos-section[data-active] .ruos-section__marker{animation:ruos-fade .9s var(--ease-emphasis) both}@keyframes ruos-rise{from{opacity:0;transform:translateY(2rem)}to{opacity:1;transform:none}}@keyframes ruos-fade{from{opacity:0;transform:translateX(1rem)}to{opacity:1;transform:none}}
.ruos-bottom-nav{display:none}
@media(max-width:900px){.ruos-shell{width:min(calc(100% - 2rem),var(--content-max))}.ruos-header__inner{grid-template-columns:1fr auto}.ruos-nav{display:none}.ruos-header__cta{font-size:.78rem}.ruos-section{min-height:auto;padding:calc(var(--header-height) + 3.5rem) 0 6.5rem}.ruos-section__grid,.ruos-component--cinematic-orbit .ruos-section__grid{grid-template-columns:1fr;gap:1.5rem}.ruos-section__marker{font-size:1rem;color:var(--color-accent)}.ruos-section h2{font-size:clamp(2.5rem,12vw,5.2rem)}.ruos-component--cinematic-orbit{min-height:100svh}.ruos-component--cinematic-orbit h2{font-size:clamp(3rem,14vw,6rem)}.ruos-hero-art{width:min(82vw,28rem);justify-self:center}.ruos-items,.ruos-decision-console{grid-template-columns:1fr}.ruos-item{min-height:auto}.ruos-bottom-nav{position:fixed;z-index:60;display:grid;grid-template-columns:repeat(4,1fr);inset:auto .75rem max(.75rem,env(safe-area-inset-bottom));padding:.45rem;background:color-mix(in srgb,var(--color-dark) 92%,transparent);backdrop-filter:blur(var(--blur-glass));border:1px solid rgba(255,255,255,.12);border-radius:1.1rem;box-shadow:var(--shadow-lift)}.ruos-bottom-nav a{text-align:center;color:#fff;text-decoration:none;font-size:.68rem;font-weight:800;padding:.6rem .2rem;border-radius:.75rem}.ruos-bottom-nav a:focus-visible{background:var(--color-accent)}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{animation:none!important;transition:none!important}}
''').strip()


def render_runtime() -> str:
    return '''
const sections=[...document.querySelectorAll('[data-section-kind]')];
const progress=document.querySelector('.ruos-progress span');
const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){entry.target.setAttribute('data-active','');}else{entry.target.removeAttribute('data-active');}}},{threshold:.18,rootMargin:'0px 0px -12%'});
sections.forEach(section=>observer.observe(section));
const updateProgress=()=>{const root=document.documentElement;const max=root.scrollHeight-root.clientHeight;const ratio=max>0?root.scrollTop/max:0;progress.style.width=`${Math.min(100,Math.max(0,ratio*100))}%`;};
updateProgress();addEventListener('scroll',updateProgress,{passive:true});addEventListener('resize',updateProgress);
const decisionCopy={indoor:'برای فضای داخلی، فاصله دید، کنترل نور و هماهنگی با معماری مسیر اصلی تصمیم است.',outdoor:'برای فضای شهری، باد، فونداسیون، زاویه دید و مدل نگهداری باید هم‌زمان سنجیده شوند.',digital:'برای نمایش دیجیتال، زیرساخت برق، روشنایی، مدیریت محتوا و دوام تجهیزات تعیین‌کننده‌اند.'};
document.querySelectorAll('.ruos-decision-console').forEach(console=>{const output=console.querySelector('output');console.querySelectorAll('button').forEach(button=>button.addEventListener('click',()=>{console.querySelectorAll('button').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));output.textContent=decisionCopy[button.dataset.choice]||'';}));});
'''.strip()
