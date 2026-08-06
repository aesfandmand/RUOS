from __future__ import annotations

from .models import PageSpec


_STYLES = r'''
/* Structures visual checkpoint: a paced industrial story, not a card stack. */
body.ruos-choreographed{--chapter-line:color-mix(in srgb,var(--color-accent) 44%,transparent);--steel:#a8adb6;--signal:#ff5a36;--night:#0d0e12}
.ruos-hero-meta{display:flex;flex-wrap:wrap;gap:.6rem;margin-top:1.5rem}.ruos-hero-meta span{padding:.45rem .7rem;border:1px solid rgba(255,255,255,.18);border-radius:999px;color:#d9d5dd;font-size:.72rem;font-weight:800;backdrop-filter:blur(8px)}
.ruos-hero-kicker{display:grid;grid-template-columns:auto 1fr;gap:1rem;align-items:center;margin:0 0 1.25rem;color:#d8d3dc;font-size:.78rem;font-weight:850}.ruos-hero-kicker::before{content:'';width:4rem;height:1px;background:var(--color-accent)}
.ruos-hero-stat{position:absolute;inset:auto 4% 4% auto;display:grid;gap:.2rem;padding:1rem 1.15rem;border:1px solid rgba(255,255,255,.14);background:rgba(9,10,14,.52);backdrop-filter:blur(12px);border-radius:1rem;color:#fff;z-index:3}.ruos-hero-stat strong{font-family:var(--font-display);font-size:2rem;line-height:1}.ruos-hero-stat span{font-size:.7rem;color:#c9c5cd}
.ruos-orbit-label{position:absolute;display:grid;place-items:center;width:7rem;aspect-ratio:1;border-radius:50%;border:1px solid rgba(255,255,255,.16);font-size:.72rem;font-weight:900;text-align:center;color:#fff;background:rgba(255,255,255,.035)}.ruos-orbit-label--one{inset:3% auto auto 2%}.ruos-orbit-label--two{inset:auto 0 5% auto}.ruos-orbit-label--three{inset:36% auto auto -8%}
.ruos-scroll-cue{position:absolute;inset:auto auto 2rem 50%;translate:-50% 0;display:grid;justify-items:center;gap:.55rem;color:#aaa4b0;font-size:.68rem;font-weight:800;letter-spacing:.04em}.ruos-scroll-cue::after{content:'';width:1px;height:3rem;background:linear-gradient(var(--color-accent),transparent);animation:ruos-pulse 1.8s ease-in-out infinite}@keyframes ruos-pulse{50%{transform:scaleY(.55);opacity:.5}}
#hero{isolation:isolate;background:radial-gradient(circle at 72% 44%,rgba(210,30,43,.17),transparent 32%),linear-gradient(145deg,#111218 0%,#08090c 100%)}#hero::before{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px);background-size:7vw 7vw;mask-image:linear-gradient(to bottom,#000,transparent 82%);pointer-events:none}#hero .ruos-section__content{max-width:60rem}#hero h2{text-wrap:balance}
#story{background:linear-gradient(180deg,var(--color-surface),color-mix(in srgb,var(--color-surface) 84%,var(--color-bg)))}#story .ruos-section__grid{grid-template-columns:minmax(3rem,8rem) minmax(0,.9fr) minmax(18rem,.55fr);align-items:start}#story .ruos-section__content{padding-top:8vh}#story .ruos-story-aside{position:sticky;top:calc(var(--header-height) + 2rem);align-self:start;border-inline-start:2px solid var(--chapter-line);padding:1rem 1.5rem 1.5rem;font-family:var(--font-display);font-size:clamp(1.4rem,2.6vw,2.8rem);line-height:1.25}#story .ruos-story-aside small{display:block;margin-top:1rem;color:var(--color-muted);font-family:var(--font-body);font-size:.75rem;font-weight:800}#story .ruos-story-rail{grid-column:2/-1;display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:5rem;background:var(--color-line);border:1px solid var(--color-line)}#story .ruos-story-rail span{min-height:9rem;padding:1.2rem;background:var(--color-bg);display:flex;align-items:flex-end;font-weight:900;position:relative}#story .ruos-story-rail span::before{content:attr(data-step);position:absolute;inset:1rem auto auto 1rem;color:var(--color-accent);font-size:.7rem}
#knowledge{padding-block:calc(var(--header-height) + 7rem);background:var(--night);color:#fff}#knowledge .ruos-copy{color:#bbb7c1}#knowledge .ruos-items{background:transparent;border:0;box-shadow:none;overflow:visible;gap:1.25rem;margin-inline:-4vw}#knowledge .ruos-item{min-height:68vh;border:1px solid rgba(255,255,255,.12);border-radius:1.25rem;background:linear-gradient(155deg,rgba(255,255,255,.08),rgba(255,255,255,.025));display:flex;flex-direction:column;justify-content:space-between;padding:clamp(1.5rem,4vw,4rem);transition:transform .45s var(--ease-emphasis),background .45s var(--ease-emphasis),border-color .45s var(--ease-emphasis);overflow:hidden}#knowledge .ruos-item::after{content:'';position:absolute;inset:auto -20% -30% auto;width:14rem;aspect-ratio:1;border:2rem solid color-mix(in srgb,var(--color-accent) 28%,transparent);border-radius:50%;filter:blur(.2px)}#knowledge .ruos-item:nth-child(2){transform:translateY(9vh)}#knowledge .ruos-item:nth-child(3){transform:translateY(-4vh)}#knowledge .ruos-item:hover{transform:translateY(-1rem);background:linear-gradient(155deg,rgba(210,30,43,.22),rgba(255,255,255,.04));border-color:rgba(255,255,255,.28)}#knowledge .ruos-item h3{margin:auto 0 1rem;font-size:clamp(1.5rem,3vw,3.2rem);max-width:9ch;position:relative;z-index:2}#knowledge .ruos-item p{max-width:30ch;font-size:1rem;position:relative;z-index:2}#knowledge .ruos-item__index{position:relative;z-index:2}
#interaction{background:linear-gradient(135deg,#111218,#17141b);color:#fff}#interaction .ruos-copy{color:#c9c5cd}.ruos-route-ribbon{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;margin-top:2rem;border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.13)}.ruos-route-ribbon span{padding:.8rem;background:rgba(0,0,0,.16);text-align:center;font-size:.75rem;font-weight:850;color:#ded9e2}.ruos-decision-console{position:relative}.ruos-decision-console::before{content:'فضا را انتخاب کنید';position:absolute;inset:-2.25rem 0 auto;color:#8f8996;font-size:.7rem;font-weight:850}.ruos-decision-console output{font-size:1.05rem;line-height:1.9;border:1px solid rgba(255,255,255,.1)}
#conversion{min-height:92svh}#conversion::before{content:'به آسمان سلام کن';position:absolute;inset:auto -2vw -4vw;font-family:var(--font-display);font-size:clamp(5rem,18vw,19rem);font-weight:950;line-height:.7;color:color-mix(in srgb,var(--color-accent-ink) 10%,transparent);white-space:nowrap;pointer-events:none}#conversion .ruos-section__content{max-width:58rem}#conversion h2{max-width:10ch}.ruos-proof-strip{display:flex;flex-wrap:wrap;gap:.65rem;margin-top:2rem}.ruos-proof-strip span{padding:.55rem .75rem;border:1px solid color-mix(in srgb,var(--color-accent-ink) 28%,transparent);border-radius:999px;font-size:.75rem;font-weight:900}
.ruos-nav a[aria-current="true"]{background:var(--color-surface);color:var(--color-accent)}
@media (max-width:900px){.ruos-scroll-cue{display:none}.ruos-hero-stat{position:relative;inset:auto;margin-top:1rem;width:max-content}.ruos-component--cinematic-orbit .ruos-section__grid{grid-template-columns:3rem minmax(0,1fr)}.ruos-hero-art{grid-column:2;max-width:24rem;margin-inline:auto}#story .ruos-section__grid{grid-template-columns:3rem minmax(0,1fr)}#story .ruos-story-aside{grid-column:2;position:relative;top:auto;margin-top:2rem}#story .ruos-story-rail{grid-column:2;grid-template-columns:repeat(2,1fr);margin-top:2rem}#knowledge .ruos-items{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;gap:1rem;margin-inline:0;padding:0 1rem 2rem;scrollbar-width:none}#knowledge .ruos-item{flex:0 0 84vw;min-height:32rem;scroll-snap-align:center;border-radius:var(--radius-md)}#knowledge .ruos-item:nth-child(n){transform:none}.ruos-route-ribbon{grid-template-columns:repeat(2,1fr)}.ruos-orbit-label{width:5rem}.ruos-orbit-label--three{display:none}}
@media (prefers-reduced-motion:reduce){#knowledge .ruos-item,#knowledge .ruos-item:hover{transform:none;transition:none}.ruos-scroll-cue::after{animation:none}}
'''

_RUNTIME = r'''
const creativeRoot=document.body;creativeRoot.classList.add('ruos-choreographed');
const chapterLinks=[...document.querySelectorAll('.ruos-nav a[href^="#"]')];
const chapterMap=new Map(chapterLinks.map(link=>[link.getAttribute('href').slice(1),link]));
const chapterObserver=new IntersectionObserver(entries=>{for(const entry of entries){if(!entry.isIntersecting)continue;for(const link of chapterLinks)link.removeAttribute('aria-current');const active=chapterMap.get(entry.target.id);if(active)active.setAttribute('aria-current','true');}},{rootMargin:'-35% 0px -55%',threshold:0});
for(const section of document.querySelectorAll('main>section[id]'))chapterObserver.observe(section);
if(!matchMedia('(prefers-reduced-motion: reduce)').matches){const art=document.querySelector('.ruos-hero-art');if(art){window.addEventListener('pointermove',event=>{const x=(event.clientX/innerWidth-.5)*10;const y=(event.clientY/innerHeight-.5)*10;art.style.transform=`translate3d(${x}px,${y}px,0) rotate(${x*.15}deg)`;},{passive:true});}}
const decisionCopy={indoor:'برای فضای داخلی، فاصله دید، نور محیط و هماهنگی با معماری را مبنا قرار دهید. مسیر مناسب معمولاً خرید ایندور و طراحی اختصاصی است.',outdoor:'برای فضای شهری، باد، فونداسیون، زاویه دید، مجوز و نگهداری تعیین‌کننده‌اند. ابتدا مکان و مدل بهره‌برداری را بررسی کنید.',digital:'برای نمایش دیجیتال، برق، مدیریت محتوا، شدت نور و سرویس دوره‌ای بخشی از خود سازه‌اند؛ فقط نمایشگر را مقایسه نکنید.'};
for(const button of document.querySelectorAll('.ruos-decision-console button[data-choice]'))button.addEventListener('click',()=>{const group=button.closest('.ruos-decision-console');for(const item of group.querySelectorAll('button'))item.setAttribute('aria-pressed',String(item===button));group.querySelector('output').textContent=decisionCopy[button.dataset.choice]||'';});
'''


def _inject_once(source: str, needle: str, replacement: str) -> str:
    if replacement in source or needle not in source:
        return source
    return source.replace(needle, replacement, 1)


def choreograph_page(page: PageSpec, html: str, css: str, runtime: str) -> tuple[str, str, str]:
    if page.slug != "structures":
        return html, css, runtime

    html = _inject_once(html, "<body>", '<body class="ruos-choreographed">')
    html = _inject_once(
        html,
        '<div class="ruos-hero-art" aria-hidden="true">',
        '<p class="ruos-hero-kicker">از مهندسی تا اثرگذاری شهری</p><div class="ruos-hero-meta" aria-label="مسیرهای اصلی صفحه"><span>شناخت سازه</span><span>مقایسه کارکرد</span><span>انتخاب مسیر تجاری</span></div><div class="ruos-hero-art" aria-hidden="true"><b class="ruos-orbit-label ruos-orbit-label--one">دید و تردد</b><b class="ruos-orbit-label ruos-orbit-label--two">نور و فضا</b><b class="ruos-orbit-label ruos-orbit-label--three">هدف و بودجه</b><div class="ruos-hero-stat"><strong>۳۶۰°</strong><span>تصمیم از همه زاویه‌ها</span></div>',
    )
    html = _inject_once(html, '</div></section><section id="story"', '<div class="ruos-scroll-cue" aria-hidden="true">برای دیدن سازوکار تصمیم اسکرول کنید</div></div></section><section id="story"')
    html = _inject_once(
        html,
        '</div></section><section id="knowledge"',
        '</div><aside class="ruos-story-aside">سازه فقط یک قاب نیست؛ نقطه‌ای است که مهندسی، شهر و تصمیم تجاری به هم می‌رسند.<small>اصل تصمیم: کارکرد پیش از فرم</small></aside><div class="ruos-story-rail" aria-label="چهار لایه تصمیم"><span data-step="01">مکان</span><span data-step="02">زاویه دید</span><span data-step="03">نور و دوام</span><span data-step="04">مدل تجاری</span></div></div></section><section id="knowledge"',
    )
    html = _inject_once(
        html,
        '<div class="ruos-decision-console"',
        '<div class="ruos-route-ribbon" aria-label="مسیرهای تجاری"><span>خرید ایندور</span><span>خرید اوتدور</span><span>اجاره رسانه</span><span>سرمایه‌گذاری</span></div><div class="ruos-decision-console"',
    )
    html = _inject_once(
        html,
        '<a class="ruos-cta" href="/contact">',
        '<div class="ruos-proof-strip" aria-label="مبنای بررسی پروژه"><span>محل و دید</span><span>بودجه و مدل مالی</span><span>اجرا و نگهداری</span></div><a class="ruos-cta" href="/contact">',
    )
    return html, css + "\n" + _STYLES, runtime + "\n" + _RUNTIME
