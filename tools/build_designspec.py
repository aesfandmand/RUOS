"""Generate the design-model spec artifact for owner approval.

Everything rendered here is the REAL thing: the real Vazirmatn variable
font already vendored in blocks/_tokens, the real colour tokens from
blocks/_tokens/style.css, the real Phosphor icons the owner approved,
and a real photo from the owner's own archive. No mockups, no
placeholder swatches.
"""
import base64
import re
from pathlib import Path

REPO = Path("/workspace/ruos")
SCRATCH = Path("/tmp/claude-0/-home-user-Chatreghermez/5ee4c798-bb09-50d6-8e84-593dbed048d3/scratchpad")

tokens_css = (REPO / "blocks/_tokens/style.css").read_text(encoding="utf-8")
font_face = re.search(r"@font-face\{[^}]*\}", tokens_css).group(0)

icons = {}
for line in (SCRATCH / "phos_icons.txt").read_text(encoding="utf-8").splitlines():
    name, svg = line.split("|", 1)
    svg = re.sub(r'\swidth="[^"]*"', "", svg)
    svg = re.sub(r'\sheight="[^"]*"', "", svg)
    icons[name] = svg

photo_b64 = base64.b64encode(
    (REPO / "media/structures/STR-002/installation-01.jpg").read_bytes()
).decode("ascii")
photo = f"data:image/jpeg;base64,{photo_b64}"

SWATCHES = [
    ("--white", "#ffffff", "زمینهٔ غالب صفحه", "light"),
    ("--paper", "#fbf8f3", "بخش متناوب / کرم روشن", "light"),
    ("--paper-2", "#f2ede6", "کارت روی کرم / تضاد ملایم", "light"),
    ("--line", "#ded8d1", "خط جداکننده و حاشیهٔ کارت", "light"),
    ("--muted", "#68646a", "متن ثانویه", "dark"),
    ("--ink-soft", "#29282b", "نوار ذغالی تأکیدی", "dark"),
    ("--ink", "#171719", "متن اصلی و تیتر", "dark"),
    ("--red-soft", "#fff0f3", "پس‌زمینهٔ نشان قرمز", "light"),
    ("--red", "#da1e49", "دکمهٔ اصلی و لهجهٔ برند", "dark"),
    ("--red-deep", "#b9123a", "حالت هاور / فشرده", "dark"),
]

TYPE_SCALE = [
    ("تیتر صفحه (h1)", "clamp(2.1rem, 3vw, 3.3rem)", "900", "بیلبورد افقی ۶×۱۲"),
    ("تیتر بخش (h2)", "clamp(1.6rem, 2.6vw, 2.4rem)", "900", "کنار این سازه چه خدماتی لازم دارید؟"),
    ("تیتر کارت (h3)", "1.05rem", "800", "برایت‌بورد افقی ۵×۳"),
    ("متن بدنه", "0.92rem", "400", "ابعاد، محل نصب و شرایط پروژه را بگویید تا بررسی فنی آماده شود."),
    ("برچسب / ریز‌متن", "0.72rem", "700", "محیط شهری (بیرون) · ۶×۱۲ متر"),
]

RHYTHM = [
    ("هیرو", "سفید + عکس واقعی", "white"),
    ("مشخصات فنی", "سفید", "white"),
    ("گالری نصب", "کرم روشن", "paper"),
    ("خدمات مرتبط", "ذغالی (یک‌بار در صفحه)", "ink"),
    ("پرسش‌های پرتکرار", "سفید", "white"),
    ("دعوت به اقدام", "قرمز (فقط بستن صفحه)", "red"),
]

LIBS_HAVE = [
    ("Vazirmatn", "فونت متغیر فارسی (۱۰۰–۹۰۰)", "SIL OFL", "سلف‌هاست، بدون CDN"),
    ("Phosphor Icons", "خانوادهٔ آیکون — تأیید شما", "MIT", "۱۰ آیکون به‌صورت اسپرایت درون‌خطی"),
    ("Motion", "انیمیشن ورود و اسکرول", "MIT", "۷۱KB، فقط animate/scroll/inView/stagger"),
    ("Swiper", "کاروسل + افکت Coverflow سه‌بعدی", "MIT", "۸۸KB، فقط ماژول‌های لازم"),
    ("GSAP + ScrollTrigger", "روایت اسکرول پیشرفته", "رایگان تجاری", "۱۱۳KB، هنوز در صفحه‌ای استفاده نشده"),
]

LIBS_PROPOSE = [
    ("Lenis", "اسکرول نرم و لغزان",
     "همان حسی که در نمونه‌های Awwwards می‌بینید؛ ۱۰KB، MIT. بدون آن، اسکرول همان اسکرول پیش‌فرض مرورگر است."),
    ("GSAP SplitText", "انیمیشن حرف‌به‌حرف تیتر",
     "افزونهٔ خود GSAP که از ۲۰۲۴ رایگان شد — همین حالا مجوزش را داریم، فقط باید به باندل اضافه شود."),
]

LOCKED = [
    ("هیچ آمار یا ادعای ساختگی", "هر عدد، مشخصه و پاسخ باید از رجیستری واقعی بیاید. اگر داده نبود، بخش ساخته نمی‌شود — با متن جعلی پُر نمی‌شود."),
    ("عکس واقعی یا دیاگرام صادق", "سازه‌ای که عکس واقعی ندارد، دیاگرام ابعاد CSS می‌گیرد؛ نه عکس استوک، نه تصویر تولیدشده."),
    ("اعتبار عکس", "عکس‌های آرشیو دیده‌شو با برچسب «نمونه نصب واقعی» می‌آیند، نه به‌عنوان نمونه‌کار چتر قرمز."),
    ("ناوبری واقعی", "هر لینک هدر، فوتر و نوار پایین به مسیر واقعی می‌رود، نه لنگر درون‌صفحه‌ای."),
    ("مگامنوی یکسان", "کارت خانواده‌های سازه در همهٔ صفحات دقیقاً یکی است — با تست قفل شده."),
    ("نوار پایین موبایل", "همیشه ثابت و چسبیده به پایین ویوپورت."),
]


def swatch(token, hexv, use, text):
    color = "#fff" if text == "dark" else "#171719"
    border = "border:1px solid var(--line);" if text == "light" else ""
    return f"""<div class="swatch">
      <div class="swatch-chip" style="background:{hexv};color:{color};{border}">{hexv}</div>
      <code>{token}</code>
      <span>{use}</span>
    </div>"""


def type_row(label, size, weight, sample):
    return f"""<div class="type-row">
      <div class="type-meta"><strong>{label}</strong><code>{size} · {weight}</code></div>
      <div class="type-sample" style="font-size:{size};font-weight:{weight}">{sample}</div>
    </div>"""


RHYTHM_BG = {
    "white": ("var(--white)", "var(--ink)", "border:1px solid var(--line);"),
    "paper": ("var(--paper)", "var(--ink)", "border:1px solid var(--line);"),
    "ink": ("var(--ink-soft)", "#fff", ""),
    "red": ("var(--red)", "#fff", ""),
}


def rhythm_row(name, desc, kind):
    bg, fg, extra = RHYTHM_BG[kind]
    return f"""<div class="rhythm-row" style="background:{bg};color:{fg};{extra}">
      <strong>{name}</strong><span>{desc}</span>
    </div>"""


def lib_row(name, what, license_, note):
    return f"""<tr><td><strong>{name}</strong></td><td>{what}</td><td><code>{license_}</code></td><td class="muted-cell">{note}</td></tr>"""


def propose_card(name, what, why):
    return f"""<div class="propose-card">
      <div class="propose-head"><strong>{name}</strong><span>{what}</span></div>
      <p>{why}</p>
    </div>"""


def locked_row(title, body):
    return f"""<li><strong>{title}</strong><span>{body}</span></li>"""


html = f"""<title>مدل طراحی چتر قرمز · نسخهٔ ۱ برای تأیید</title>
<style>
{font_face}
:root {{
  --red:#da1e49; --red-deep:#b9123a; --red-soft:#fff0f3;
  --ink:#171719; --ink-soft:#29282b; --paper:#fbf8f3; --paper-2:#f2ede6;
  --white:#fff; --muted:#68646a; --line:#ded8d1;
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--white); color:var(--ink);
  font-family:Vazirmatn,Tahoma,Arial,sans-serif; font-size:16px; line-height:1.85;
  -webkit-font-smoothing:antialiased;
}}
.shell {{ max-width:1000px; margin:0 auto; padding:0 24px; }}

/* ── hero ── */
.spec-hero {{ padding:86px 0 62px; border-bottom:1px solid var(--line); }}
.eyebrow {{
  color:var(--red); font-size:.74rem; font-weight:800; letter-spacing:.05em;
  margin:0 0 14px; display:flex; align-items:center; gap:9px;
}}
.eyebrow:before {{ content:""; background:var(--red); width:7px; height:7px; display:inline-block; }}
h1 {{ font-size:clamp(2rem,3.4vw,3rem); font-weight:900; letter-spacing:-.04em; line-height:1.2; margin:0; text-wrap:balance; }}
h1 .soft {{ color:var(--muted); }}
.spec-hero p {{ color:var(--muted); max-width:62ch; margin:20px 0 0; font-size:.95rem; }}

/* ── sections ── */
section {{ padding:74px 0; border-bottom:1px solid var(--line); }}
section.on-paper {{ background:var(--paper); }}
h2 {{ font-size:clamp(1.5rem,2.4vw,2.1rem); font-weight:900; letter-spacing:-.03em; margin:0 0 10px; text-wrap:balance; }}
h2 .soft {{ color:var(--muted); }}
.lead {{ color:var(--muted); max-width:60ch; margin:0 0 40px; font-size:.9rem; }}

/* ── colour ── */
.swatch-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:14px; }}
.swatch {{ display:flex; flex-direction:column; gap:7px; }}
.swatch-chip {{
  height:78px; border-radius:14px; display:flex; align-items:flex-end; padding:12px;
  font-size:.72rem; font-weight:800; font-variant-numeric:tabular-nums; direction:ltr;
}}
.swatch code {{ font-size:.72rem; color:var(--ink); font-weight:800; direction:ltr; text-align:right; }}
.swatch span {{ font-size:.72rem; color:var(--muted); }}

/* ── type ── */
.type-row {{ display:grid; grid-template-columns:200px 1fr; gap:26px; align-items:baseline; padding:20px 0; border-bottom:1px solid var(--line); }}
.type-row:last-child {{ border-bottom:0; }}
.type-meta {{ display:flex; flex-direction:column; gap:3px; }}
.type-meta strong {{ font-size:.8rem; font-weight:800; }}
.type-meta code {{ font-size:.68rem; color:var(--muted); direction:ltr; }}
.type-sample {{ line-height:1.35; }}

.twotone {{ background:var(--paper-2); border-radius:16px; padding:34px; margin-top:30px; }}
.twotone p {{ margin:0 0 6px; font-size:.76rem; color:var(--muted); font-weight:800; }}
.twotone .demo {{ font-size:clamp(1.3rem,2.2vw,1.9rem); font-weight:900; letter-spacing:-.03em; line-height:1.4; }}

/* ── rhythm ── */
.rhythm {{ display:flex; flex-direction:column; gap:8px; }}
.rhythm-row {{ border-radius:13px; padding:18px 22px; display:flex; justify-content:space-between; align-items:center; gap:16px; }}
.rhythm-row strong {{ font-size:.9rem; font-weight:800; }}
.rhythm-row span {{ font-size:.76rem; opacity:.78; }}

/* ── components ── */
.comp-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:20px; }}
.demo-card {{ background:var(--white); border:1px solid var(--line); border-radius:18px; overflow:hidden; }}
.demo-card img {{ width:100%; aspect-ratio:16/10; object-fit:cover; display:block; }}
.demo-card-body {{ padding:20px; }}
.demo-card h3 {{ margin:0; font-size:1.02rem; font-weight:900; }}
.demo-card p {{ margin:7px 0 0; color:var(--muted); font-size:.78rem; }}
.pill-row {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
.pill {{ background:var(--paper-2); border-radius:999px; padding:5px 13px; font-size:.7rem; font-weight:700; color:var(--ink); }}

.svc-card {{ background:var(--white); border:1px solid var(--line); border-radius:16px; padding:18px 20px; display:flex; align-items:center; gap:14px; }}
.svc-card svg {{ width:38px; height:38px; padding:9px; border-radius:10px; background:var(--red-soft); color:var(--red); flex:none; }}
.svc-card strong {{ display:block; font-size:.88rem; font-weight:800; }}
.svc-card span {{ display:block; color:var(--muted); font-size:.72rem; }}

.btn-row {{ display:flex; flex-wrap:wrap; gap:14px; align-items:center; margin-top:8px; }}
.btn-primary {{
  background:var(--red); color:#fff; border:0; border-radius:13px; min-height:54px;
  padding:0 22px; font-family:inherit; font-size:.8rem; font-weight:900;
  display:inline-flex; align-items:center; gap:26px; cursor:pointer;
}}
.btn-primary:hover {{ background:var(--red-deep); }}
.btn-primary i {{ font-style:normal; }}
.btn-ghost {{
  background:var(--white); color:var(--ink); border:1px solid var(--line); border-radius:13px;
  min-height:54px; padding:0 22px; font-family:inherit; font-size:.8rem; font-weight:800;
  display:inline-flex; align-items:center; cursor:pointer;
}}
.btn-ghost:hover {{ border-color:var(--red); color:var(--red); }}
.btn-circle {{
  width:48px; height:48px; border-radius:50%; background:var(--white);
  border:1px solid var(--line); display:inline-flex; align-items:center; justify-content:center; cursor:pointer;
}}
.btn-circle svg {{ width:16px; height:16px; }}
.btn-circle:hover {{ background:var(--red); border-color:var(--red); color:#fff; }}

.icon-strip {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:6px; }}
.icon-tile {{
  width:72px; height:72px; border-radius:14px; background:var(--white); border:1px solid var(--line);
  display:flex; align-items:center; justify-content:center; color:var(--ink);
}}
.icon-tile svg {{ width:26px; height:26px; }}

/* ── tables / lists ── */
table {{ width:100%; border-collapse:collapse; font-size:.82rem; }}
th, td {{ text-align:right; padding:13px 12px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ font-size:.72rem; color:var(--muted); font-weight:800; }}
td code {{ direction:ltr; font-size:.72rem; }}
.muted-cell {{ color:var(--muted); }}

.propose-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:18px; }}
.propose-card {{ background:var(--white); border:1px solid var(--line); border-right:3px solid var(--red); border-radius:14px; padding:22px; }}
.propose-head {{ display:flex; flex-direction:column; gap:2px; margin-bottom:10px; }}
.propose-head strong {{ font-size:.95rem; font-weight:900; }}
.propose-head span {{ font-size:.74rem; color:var(--red); font-weight:800; }}
.propose-card p {{ margin:0; font-size:.8rem; color:var(--muted); }}

ul.locked {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:2px; }}
ul.locked li {{ display:grid; grid-template-columns:230px 1fr; gap:20px; padding:16px 0; border-bottom:1px solid var(--line); }}
ul.locked li:last-child {{ border-bottom:0; }}
ul.locked strong {{ font-size:.85rem; font-weight:800; }}
ul.locked span {{ font-size:.8rem; color:var(--muted); }}

.ask {{ background:var(--ink); color:#fff; border-radius:20px; padding:44px; margin:0 0 90px; }}
.ask h2 {{ color:#fff; margin-bottom:14px; }}
.ask p {{ color:#ffffffb0; font-size:.88rem; margin:0 0 8px; max-width:62ch; }}
.ask ol {{ color:#ffffffd0; font-size:.86rem; padding-right:20px; margin:18px 0 0; }}
.ask ol li {{ margin-bottom:8px; }}

@media (width<=760px) {{
  .type-row {{ grid-template-columns:1fr; gap:8px; }}
  ul.locked li {{ grid-template-columns:1fr; gap:5px; }}
  .rhythm-row {{ flex-direction:column; align-items:flex-start; gap:4px; }}
  .ask {{ padding:30px; }}
  section {{ padding:52px 0; }}
}}
</style>

<div dir="rtl" lang="fa">

<div class="spec-hero">
  <div class="shell">
    <p class="eyebrow">مدل طراحی · نسخهٔ ۱ · منتظر تأیید شما</p>
    <h1>یک زبان طراحی، <span class="soft">یک‌بار تأیید شود و دیگر برنگردیم.</span></h1>
    <p>این سند از همهٔ نمونه‌هایی که فرستادید و همهٔ بازخوردهای این گفتگو ساخته شده. هرچه اینجا می‌بینید واقعی رندر شده — فونت واقعی، توکن رنگ واقعی از مخزن، آیکون Phosphor که تأیید کردید، و عکس واقعی از آرشیو خودتان. بعد از تأیید شما، این‌ها به قانون ماشین‌خوان تبدیل می‌شوند تا موتور نتواند از آن تخطی کند.</p>
  </div>
</div>

<section>
  <div class="shell">
    <h2>۱. پالت رنگ <span class="soft">— سفید غالب، قرمز و ذغالی برای ترکیب، کرم برای تضاد کارت</span></h2>
    <p class="lead">یک تصحیح صادقانه: پالت از اول درست بود، اشتباه من در «کاربرد» بود — بخش‌های کامل را ذغالی کردم درحالی‌که شما گفته بودید برای تضاد زمینه و کارت از کرم/طوسی استفاده کنم. آن اشتباه در این مدل اصلاح شده.</p>
    <div class="swatch-grid">
      {''.join(swatch(*s) for s in SWATCHES)}
    </div>
  </div>
</section>

<section class="on-paper">
  <div class="shell">
    <h2>۲. تایپوگرافی <span class="soft">— وزیرمتن، مقیاس ثابت</span></h2>
    <p class="lead">فونت متغیر وزیرمتن (وزن ۱۰۰ تا ۹۰۰) که همین حالا سلف‌هاست شده و به CDN وابسته نیست.</p>
    {''.join(type_row(*t) for t in TYPE_SCALE)}
    <div class="twotone">
      <p>امضای تیتر — الگوی دو-تُنه (از نمونهٔ Xurya که فرستادید)</p>
      <div class="demo">کنار این سازه <span style="color:var(--muted)">چه خدماتی لازم دارید؟</span></div>
      <div class="demo">مشخصات فنی <span style="color:var(--muted)">بیلبورد افقی ۶×۱۲</span></div>
    </div>
  </div>
</section>

<section>
  <div class="shell">
    <h2>۳. ریتم بخش‌ها <span class="soft">— کجا سفید، کجا کرم، کجا ذغالی</span></h2>
    <p class="lead">قانون: سفید پیش‌فرض است. کرم برای تنفس بین بخش‌ها. ذغالی حداکثر یک‌بار در صفحه برای تأکید. قرمز فقط برای بستن صفحه با دعوت به اقدام.</p>
    <div class="rhythm">
      {''.join(rhythm_row(*r) for r in RHYTHM)}
    </div>
  </div>
</section>

<section class="on-paper">
  <div class="shell">
    <h2>۴. کارت‌ها <span class="soft">— عکس کامل، گوشهٔ گرد، چیپ مشخصات</span></h2>
    <p class="lead">از نمونه‌های کارت که فرستادید: عکس تمام‌عرض، تیتر، ریز‌متن، و چیپ‌های مشخصات واقعی از رجیستری.</p>
    <div class="comp-grid">
      <div class="demo-card">
        <img src="{photo}" alt="نمونه نصب واقعی بیلبورد افقی">
        <div class="demo-card-body">
          <h3>بیلبورد افقی ۶×۱۲</h3>
          <p>محیط شهری (بیرون) — نمونه نصب واقعی، آرشیو دیده‌شو</p>
          <div class="pill-row">
            <span class="pill">۶×۱۲ متر</span>
            <span class="pill">افقی</span>
            <span class="pill">یک یا دو رو</span>
          </div>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;gap:14px;">
        <div class="svc-card">{icons['wrench']}<div><strong>طراحی بیلبورد</strong><span>محیطی</span></div></div>
        <div class="svc-card">{icons['file-text']}<div><strong>چاپ بنر</strong><span>لارج‌فرمت</span></div></div>
        <div class="svc-card">{icons['map-pin']}<div><strong>Media Planning</strong><span>برنامه‌ریزی</span></div></div>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="shell">
    <h2>۵. دکمه و آیکون <span class="soft">— Phosphor، تأییدشدهٔ شما</span></h2>
    <p class="lead">سه نوع دکمه، بیشتر نه. آیکون‌ها همه از یک خانواده (Phosphor regular) تا هیچ‌جای سایت آیکون غریبه نبینید.</p>
    <div class="btn-row">
      <button class="btn-primary"><span>درخواست بررسی فنی و قیمت</span><i>←</i></button>
      <button class="btn-ghost">دیدن همهٔ سازه‌ها</button>
      <button class="btn-circle">{icons['caret-right']}</button>
      <button class="btn-circle">{icons['caret-left']}</button>
    </div>
    <div class="icon-strip">
      {''.join(f'<div class="icon-tile">{svg}</div>' for svg in icons.values())}
    </div>
  </div>
</section>

<section class="on-paper">
  <div class="shell">
    <h2>۶. کتابخانه‌ها <span class="soft">— چه داریم، چه پیشنهاد می‌کنم</span></h2>
    <p class="lead">همه واقعی، وندورشده در مخزن، بدون وابستگی به CDN (که در این محیط بلاک است). مجوز هرکدام مستقل بررسی شده.</p>
    <table>
      <thead><tr><th>کتابخانه</th><th>کارکرد</th><th>مجوز</th><th>وضعیت</th></tr></thead>
      <tbody>{''.join(lib_row(*l) for l in LIBS_HAVE)}</tbody>
    </table>
    <h3 style="margin:38px 0 6px;font-size:1rem;font-weight:900;">پیشنهاد افزودن — فقط این دو، و دلیلش</h3>
    <p class="lead" style="margin-bottom:20px;">این‌ها را لازم می‌دانم؛ بقیهٔ چیزهایی که قبلاً مطرح شد (Tailwind، Animate.css، Bootstrap، HTML5 Boilerplate) با معماری این پروژه در تضادند یا با چیزی که داریم تکراری‌اند.</p>
    <div class="propose-grid">
      {''.join(propose_card(*p) for p in LIBS_PROPOSE)}
    </div>
  </div>
</section>

<section>
  <div class="shell">
    <h2>۷. قوانین قفل‌شده <span class="soft">— چیزهایی که هرگز تغییر نمی‌کنند</span></h2>
    <p class="lead">این‌ها با تست خودکار در مخزن قفل می‌شوند تا هیچ صفحه‌ای نتواند نقضشان کند.</p>
    <ul class="locked">{''.join(locked_row(*x) for x in LOCKED)}</ul>
  </div>
</section>

<div class="shell">
  <div class="ask">
    <h2>چه چیزی را تأیید می‌کنید؟</h2>
    <p>اگر این مدل درست است، بگویید «تأیید» تا مرحلهٔ بعد را شروع کنم. اگر جایی با منطق شما نمی‌خواند، همان‌جا را بگویید — بهتر است الان اصلاح شود تا بعد از ساخت ده صفحه.</p>
    <ol>
      <li>پالت و کاربردش (سفید غالب، کرم برای تضاد، ذغالی یک‌بار، قرمز فقط CTA)</li>
      <li>مقیاس تایپوگرافی و امضای تیتر دو-تُنه</li>
      <li>ریتم بخش‌ها</li>
      <li>الگوی کارت، دکمه و آیکون</li>
      <li>افزودن Lenis و GSAP SplitText — یا رد کردنشان</li>
    </ol>
    <p style="margin-top:22px;">بعد از تأیید: این مدل را به توکن و قانون ماشین‌خوان در مخزن تبدیل می‌کنم (به‌همراه تست) تا موتور نتواند از آن عقب برگردد؛ بعد سراغ طراحی صفحه می‌رویم و از آن به بعد فقط تکمیل و بهبود، نه ادیت فرسایشی.</p>
  </div>
</div>

</div>
"""

out = SCRATCH / "design-model-v1.html"
out.write_text(html, encoding="utf-8")
print(f"{out}: {len(html.encode('utf-8'))} bytes")
