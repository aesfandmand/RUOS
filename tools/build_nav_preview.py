"""Build a standalone preview of the locked navigation, and nothing else.

    python3 tools/build_nav_preview.py [output.html]

Renders the real site-header (desktop mega-menu + mobile glass drawer) and
the real bottom-nav from the block library into one self-contained file --
fonts, scripts and the logo inlined -- so it opens over file:// and can be
handed to the owner for review.

Behind the page it paints a saturated dark backdrop. That is deliberate and
temporary: on the real white-dominant site the glass is nearly invisible and
reads as broken when it is in fact correct, so the glass has to be judged
against something vivid. It is a measuring rig, not a design.

The two filler content blocks exist only to give the fixed header and bottom
nav something to scroll over. No page is built or modified.
"""
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ruos.block_page import render_page
from ruos.block_registry import load_library
from ruos.structure_detail_spec import _real_shell

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "nav-preview.html"

library = load_library()
shell = _real_shell()

spec = {
    "slug": "nav-preview",
    "lang": "fa",
    "direction": "rtl",
    "title": "پیش‌نمایش مگامنو و نوار پایین — چتر قرمز",
    "description": "پیش‌نمایش مستقل مگامنو (دسکتاپ و موبایل) و نوار پایین موبایل، بدون هیچ صفحه محتوایی.",
    "shell": shell,
    "blocks": [
        {
            "block": "structure-hero",
            "id": "preview-anchor",
            "data": {
                "eyebrow": "پیش‌نمایش",
                "title": "این یک صفحهٔ واقعی نیست — فقط پیش‌نمایش مگامنو و نوار پایین.",
                "lead": "برای مرور مگامنو دسکتاپ روی «سازه‌ها و تابلوها» هاور کنید؛ در موبایل ☰ را بزنید.",
                "diagram": {
                    "ratio": "5 / 10", "width_label": "۵ متر", "height_label": "۱۰ متر",
                    "aria_label": "نمودار آزمایشی",
                },
            },
        },
        {
            "block": "review-gate",
            "id": "preview-end",
            "data": {
                "eyebrow": "پایان پیش‌نمایش",
                "title": "این هم پایین صفحه — نوار پایین موبایل باید همچنان ثابت روی صفحه باشد.",
                "body": "این متن فقط برای آزمایش اسکرول است.",
                "primary": {"label": "درخواست بررسی"},
            },
        },
    ],
}

page = render_page(spec, library)

logo = (ROOT / "blocks" / "site-header" / "assets" / "logo.png").read_bytes()
logo_uri = "data:image/png;base64," + base64.b64encode(logo).decode("ascii")

# TEMPORARY, preview-only: a saturated dark backdrop behind the page, so the
# glass on the drawer and the notch in the bottom bar can actually be judged.
# The real site is white-dominant — this is a measuring rig, not a design.
filler = """
<style>
html{background:#080a16}
body{background:transparent}
.pv-bg{position:fixed;inset:0;z-index:-1;overflow:hidden;background:#080a16}
.pv-bg:before,.pv-bg:after{content:"";position:absolute;inset:-25%}
.pv-bg:before{background:
  radial-gradient(48% 34% at 18% 16%,#4b1bd6cc,#0000 70%),
  radial-gradient(42% 30% at 84% 26%,#d61b5ccc,#0000 70%),
  radial-gradient(52% 38% at 62% 74%,#0e7be8bf,#0000 70%),
  radial-gradient(38% 28% at 22% 88%,#12b98ba6,#0000 70%);}
.pv-bg:after{background:
  repeating-linear-gradient(58deg,#ffffff14 0 2px,#0000 2px 26px),
  repeating-linear-gradient(-31deg,#ffffff0f 0 2px,#0000 2px 38px);}
.pv-copy{max-width:760px;margin:0 auto;padding:110px 24px 220px;font-family:Vazirmatn,sans-serif}
.pv-copy h1{font-size:1.7rem;font-weight:900;color:#fff;margin:0}
.pv-copy p{color:#ffffffbf;line-height:2;font-size:.95rem}
.pv-tiles{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:34px 0}
.pv-tiles div{height:150px;border-radius:20px;border:1px solid #ffffff24}
.pv-tiles div:nth-child(1){background:linear-gradient(140deg,#ff2d6f,#ffbf3d)}
.pv-tiles div:nth-child(2){background:linear-gradient(140deg,#12e0c4,#0b63ff)}
.pv-tiles div:nth-child(3){background:linear-gradient(140deg,#8b2dff,#ff2d6f)}
.pv-tiles div:nth-child(4){background:linear-gradient(140deg,#ffd23d,#12b98b)}
</style>
<div class="pv-bg"></div>
<div class="pv-copy">
<h1>پیش‌نمایش ناوبری</h1>
<p>این پس‌زمینهٔ تیره و پررنگ <strong>موقتی</strong> است و فقط برای سنجش کیفیت گلس گذاشته شده — سایت واقعی سفیدغالب است. منو را با ☰ باز کنید و ببینید پشت آن چقدر پیداست؛ در نوار پایین هم روی آیکون‌ها بزنید تا حفرهٔ نوار و حرکت حباب دیده شود.</p>
<div class="pv-tiles"><div></div><div></div><div></div><div></div></div>
<p>برای آزمودن نوار پایین روی پس‌زمینهٔ رنگی، کمی اسکرول کنید.</p>
<div style="height:900px"></div>
<div class="pv-tiles"><div></div><div></div><div></div><div></div></div>
<p>پایان اسکرول آزمایشی.</p>
</div>
"""

html = page.html
html = html.replace('<link rel="stylesheet" href="assets/styles.css">',
                     f"<style>{page.css}</style>")
# _foundation/behavior.js always imports motion.min.mjs, so the script must
# stay a module regardless of which script tag render_page chose.
motion_path = ROOT / "blocks" / "_foundation" / "assets" / "motion.min.mjs"
motion_uri = "data:text/javascript;base64," + base64.b64encode(motion_path.read_bytes()).decode("ascii")
script = page.script.replace('"./motion.min.mjs"', f'"{motion_uri}"')
html = html.replace('<script type="module" src="assets/behavior.js"></script>',
                     f'<script type="module">{script}</script>')
html = html.replace('<script src="assets/behavior.js" defer></script>',
                     f'<script type="module">{script}</script>')
html = html.replace('src="assets/logo.png"', f'src="{logo_uri}"')
html = html.replace('<main id="main">', f'<main id="main">{filler}')

OUT.write_text(html, encoding="utf-8")
print("wrote", OUT, len(html), "bytes")
