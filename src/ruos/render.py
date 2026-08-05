from __future__ import annotations

import html
import json
from collections.abc import Iterable

from .models import PageSpec, SectionSpec


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _render_items(items: Iterable[dict[str, object]]) -> str:
    rendered: list[str] = []
    for item in items:
        rendered.append(
            '<article class="ruos-item">'
            f'<h3>{_esc(item.get("title", ""))}</h3>'
            f'<p>{_esc(item.get("body", ""))}</p>'
            '</article>'
        )
    return "".join(rendered)


def render_section(section: SectionSpec) -> str:
    classes = f"ruos-section ruos-section--{_esc(section.kind)}"
    eyebrow = f'<p class="ruos-eyebrow">{_esc(section.eyebrow)}</p>' if section.eyebrow else ""
    body = f'<div class="ruos-copy"><p>{_esc(section.body)}</p></div>' if section.body else ""
    items = f'<div class="ruos-items">{_render_items(section.items)}</div>' if section.items else ""
    cta = ""
    if section.cta_label and section.cta_href:
        cta = f'<a class="ruos-cta" href="{_esc(section.cta_href)}">{_esc(section.cta_label)}</a>'
    return (
        f'<section id="{_esc(section.id)}" class="{classes}" data-section-kind="{_esc(section.kind)}">'
        '<div class="ruos-shell">'
        f'{eyebrow}<h2>{_esc(section.title)}</h2>{body}{items}{cta}'
        '</div></section>'
    )


def render_document(page: PageSpec) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page.title,
        "description": page.description,
        "inLanguage": page.lang,
    }
    body = "".join(render_section(section) for section in page.sections)
    return f'''<!doctype html>
<html lang="{_esc(page.lang)}" dir="{_esc(page.direction)}" data-visual-profile="{_esc(page.visual_profile)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(page.title)}</title>
<meta name="description" content="{_esc(page.description)}">
<link rel="stylesheet" href="assets/styles.css">
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
</head>
<body>
<a class="skip-link" href="#main">پرش به محتوای اصلی</a>
<header class="ruos-header"><div class="ruos-shell"><strong>{_esc(page.brand)}</strong></div></header>
<main id="main">{body}</main>
<script src="assets/runtime.js" defer></script>
</body>
</html>'''


def render_css() -> str:
    return '''
:root{--bg:#f4f1ea;--ink:#171717;--accent:#d71920;--line:#cbc5b8;--max:1180px;--space:clamp(1rem,2vw,2rem)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:Tahoma,Arial,sans-serif;line-height:1.9}
.ruos-shell{width:min(calc(100% - 2rem),var(--max));margin-inline:auto}.ruos-header{position:sticky;top:0;z-index:20;padding:1rem 0;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.ruos-section{padding:clamp(4rem,9vw,9rem) 0;border-bottom:1px solid var(--line)}.ruos-section h2{max-width:14ch;font-size:clamp(2rem,6vw,5.6rem);line-height:1.12;margin:.25em 0}.ruos-eyebrow{color:var(--accent);font-weight:700}.ruos-copy{max-width:68ch;font-size:clamp(1rem,1.8vw,1.25rem)}
.ruos-items{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,16rem),1fr));gap:1px;background:var(--line);margin-top:2rem}.ruos-item{background:var(--bg);padding:clamp(1.25rem,3vw,2.5rem)}.ruos-cta{display:inline-flex;margin-top:2rem;padding:.8rem 1.2rem;border:1px solid currentColor;color:inherit;text-decoration:none}.ruos-cta:hover,.ruos-cta:focus-visible{background:var(--accent);color:white;border-color:var(--accent)}
.skip-link{position:fixed;inset-inline-start:1rem;top:-4rem;z-index:99;background:#fff;padding:.75rem}.skip-link:focus{top:1rem}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
'''.strip()


def render_runtime() -> str:
    return '''
const sections=[...document.querySelectorAll('[data-section-kind]')];
const observer=new IntersectionObserver(entries=>{for(const entry of entries){entry.target.toggleAttribute('data-active',entry.isIntersecting)}},{threshold:.2});
sections.forEach(section=>observer.observe(section));
'''.strip()
