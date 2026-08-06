from __future__ import annotations

from .models import PageSpec


_STYLES = r'''
/* RUOS creative choreography: converts the base component stack into a paced visual story. */
body.ruos-choreographed{--chapter-line:color-mix(in srgb,var(--color-accent) 44%,transparent)}
.ruos-hero-meta{display:flex;flex-wrap:wrap;gap:.6rem;margin-top:1.5rem}.ruos-hero-meta span{padding:.45rem .7rem;border:1px solid rgba(255,255,255,.18);border-radius:999px;color:#d9d5dd;font-size:.72rem;font-weight:800;backdrop-filter:blur(8px)}
.ruos-orbit-label{position:absolute;display:grid;place-items:center;width:7rem;aspect-ratio:1;border-radius:50%;border:1px solid rgba(255,255,255,.16);font-size:.72rem;font-weight:900;text-align:center;color:#fff;background:rgba(255,255,255,.035)}.ruos-orbit-label--one{inset:3% auto auto 2%}.ruos-orbit-label--two{inset:auto 0 5% auto}.ruos-orbit-label--three{inset:36% auto auto -8%}
#story .ruos-section__grid{grid-template-columns:minmax(3rem,8rem) minmax(0,.9fr) minmax(18rem,.55fr);align-items:start}#story .ruos-section__content{padding-top:8vh}#story .ruos-story-aside{position:sticky;top:calc(var(--header-height) + 2rem);align-self:start;border-inline-start:2px solid var(--chapter-line);padding:1rem 1.5rem 1.5rem;font-family:var(--font-display);font-size:clamp(1.4rem,2.6vw,2.8rem);line-height:1.25}#story .ruos-story-aside small{display:block;margin-top:1rem;color:var(--color-muted);font-family:var(--font-body);font-size:.75rem;font-weight:800}
#knowledge .ruos-items{background:transparent;border:0;box-shadow:none;overflow:visible;gap:0;margin-inline:-4vw}#knowledge .ruos-item{min-height:62vh;border:1px solid var(--color-line);border-radius:0;background:var(--color-surface);display:flex;flex-direction:column;justify-content:space-between;padding:clamp(1.5rem,4vw,4rem);transition:transform .45s var(--ease-emphasis),background .45s var(--ease-emphasis)}#knowledge .ruos-item:nth-child(2){transform:translateY(9vh)}#knowledge .ruos-item:nth-child(3){transform:translateY(-4vh)}#knowledge .ruos-item:hover{transform:translateY(-1rem);background:color-mix(in srgb,var(--color-surface) 82%,var(--color-accent))}#knowledge .ruos-item h3{margin:auto 0 1rem;font-size:clamp(1.5rem,3vw,3.2rem);max-width:9ch}#knowledge .ruos-item p{max-width:30ch;font-size:1rem}
.ruos-route-ribbon{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:2rem;border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.13)}.ruos-route-ribbon span{padding:.8rem;background:rgba(0,0,0,.16);text-align:center;font-size:.75rem;font-weight:850;color:#ded9e2}
#conversion::before{content:'به آسمان سلام کن';position:absolute;inset:auto -2vw -4vw;font-family:var(--font-display);font-size:clamp(5rem,18vw,19rem);font-weight:950;line-height:.7;color:color-mix(in srgb,var(--color-accent-ink) 10%,transparent);white-space:nowrap;pointer-events:none}#conversion .ruos-section__content{max-width:58rem}#conversion h2{max-width:10ch}
.ruos-nav a[aria-current="true"]{background:var(--color-surface);color:var(--color-accent)}
@media (max-width:900px){#story .ruos-section__grid{grid-template-columns:3rem minmax(0,1fr)}#story .ruos-story-aside{grid-column:2;position:relative;top:auto;margin-top:2rem}#knowledge .ruos-items{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:1rem;margin-inline:0;padding:0 1rem 2rem;scrollbar-width:none}#knowledge .ruos-item{flex:0 0 84vw;min-height:32rem;scroll-snap-align:center;border-radius:var(--radius-md)}#knowledge .ruos-item:nth-child(n){transform:none}.ruos-route-ribbon{grid-template-columns:repeat(2,1fr)}.ruos-orbit-label{width:5rem}.ruos-orbit-label--three{display:none}}
@media (prefers-reduced-motion:reduce){#knowledge .ruos-item,#knowledge .ruos-item:hover{transform:none;transition:none}}
'''

_RUNTIME = r'''
const creativeRoot=document.body;creativeRoot.classList.add('ruos-choreographed');
const chapterLinks=[...document.querySelectorAll('.ruos-nav a[href^="#"]')];
const chapterMap=new Map(chapterLinks.map(link=>[link.getAttribute('href').slice(1),link]));
const chapterObserver=new IntersectionObserver(entries=>{for(const entry of entries){if(!entry.isIntersecting)continue;for(const link of chapterLinks)link.removeAttribute('aria-current');const active=chapterMap.get(entry.target.id);if(active)active.setAttribute('aria-current','true');}},{rootMargin:'-35% 0px -55%',threshold:0});
for(const section of document.querySelectorAll('main>section[id]'))chapterObserver.observe(section);
if(!matchMedia('(prefers-reduced-motion: reduce)').matches){const art=document.querySelector('.ruos-hero-art');if(art){window.addEventListener('pointermove',event=>{const x=(event.clientX/innerWidth-.5)*10;const y=(event.clientY/innerHeight-.5)*10;art.style.transform=`translate3d(${x}px,${y}px,0) rotate(${x*.15}deg)`;},{passive:true});}}
'''


def _inject_once(source: str, needle: str, replacement: str) -> str:
    if replacement in source or needle not in source:
        return source
    return source.replace(needle, replacement, 1)


def choreograph_page(page: PageSpec, html: str, css: str, runtime: str) -> tuple[str, str, str]:
    """Add page-specific visual pacing without weakening semantic output.

    The layer is deterministic, progressively enhanced and deliberately leaves
    the base renderer usable when a marker is absent.
    """
    if page.slug != "structures":
        return html, css, runtime

    html = _inject_once(html, "<body>", '<body class="ruos-choreographed">')
    html = _inject_once(
        html,
        '<div class="ruos-hero-art" aria-hidden="true">',
        '<div class="ruos-hero-meta" aria-label="مسیرهای اصلی صفحه"><span>شناخت سازه</span><span>مقایسه کارکرد</span><span>انتخاب مسیر تجاری</span></div><div class="ruos-hero-art" aria-hidden="true"><b class="ruos-orbit-label ruos-orbit-label--one">دید و تردد</b><b class="ruos-orbit-label ruos-orbit-label--two">نور و فضا</b><b class="ruos-orbit-label ruos-orbit-label--three">هدف و بودجه</b>',
    )
    html = _inject_once(
        html,
        '</div></section><section id="knowledge"',
        '</div><aside class="ruos-story-aside">سازه فقط یک قاب نیست؛ نقطه‌ای است که مهندسی، شهر و تصمیم تجاری به هم می‌رسند.<small>اصل تصمیم: کارکرد پیش از فرم</small></aside></div></section><section id="knowledge"',
    )
    html = _inject_once(
        html,
        '<div class="ruos-decision-console"',
        '<div class="ruos-route-ribbon" aria-label="مسیرهای تجاری"><span>خرید ایندور</span><span>خرید اوتدور</span><span>اجاره رسانه</span><span>سرمایه‌گذاری</span></div><div class="ruos-decision-console"',
    )
    return html, css + "\n" + _STYLES, runtime + "\n" + _RUNTIME
