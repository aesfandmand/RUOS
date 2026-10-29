#!/usr/bin/env python3
"""Compose the Portfolio hub page spec (and one service-view example).

    python3 tools/build_portfolio_hub.py            # writes both drafts
    python3 tools/build_portfolio_hub.py --view logo-design

Structure follows pages/drafts/portfolio.skeleton.md (stage 3, approved by
the owner 2026-10-27). What is real here:
  * the six families and their order, from the service-landing registry
  * the 52 indexable final-service landings and their slugs, from the v5
    target sitemap -- the portfolio is filtered at the final service, never
    at the family name (owner, 2026-10-27)
  * the image ALT text pattern for every slot (owner: real photos go in at
    WordPress time; the build reserves each slot and writes its ALT)
What is a tagged placeholder (`"placeholder": true`), waiting on stage 4:
  * every body sentence, the FAQ answers, and each sample's title/industry/
    city/year -- the owner's real samples replace these in WordPress.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ruos.architecture_registry import load_services  # noqa: E402
from ruos.site_shell import SITE_SHELL_REF  # noqa: E402

# Persian lorem ipsum, the filler Iranian design templates ship with: it
# reads as text at the right density and rhythm, where Latin filler makes an
# RTL page look unfinished. Still tagged `"placeholder": true` everywhere.
LOREM = ("لورم ایپسوم متن ساختگی با تولید سادگی نامفهوم از صنعت چاپ و با استفاده از "
         "طراحان گرافیک است؛ چاپگرها و متون بلکه روزنامه و مجله در ستون و سطرآنچنان "
         "که لازم است و برای شرایط فعلی تکنولوژی مورد نیاز.")
DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
VIEW_BASE = "/portfolio/service/"
# Editorial review dates (ru-senior-seo §5-ب.14): stated, not derived.
REVIEWED_ISO = "2026-10-28"
REVIEWED_FA = "۷ آبان ۱۴۰۵"
NEXT_REVIEW_FA = "۷ بهمن ۱۴۰۵"

# Family order and icons as the services hub uses them.
FAMILIES = [
    ("ooh", "تبلیغات محیطی", "icon-fam-outdoor"),
    ("digital", "دیجیتال مارکتینگ", "icon-fam-digital"),
    ("graphic", "طراحی گرافیک", "icon-fam-graphic"),
    ("print", "چاپ و تولید", "icon-fam-print"),
    ("photo", "عکاسی و فیلم‌برداری", "icon-fam-photo"),
    ("consult", "مشاوره", "icon-fam-consult"),
]
FAMILY_KEY = {fa: key for key, fa, _ in FAMILIES}

# Registry id -> slug, from 11-projects/red-umbrella/registries/
# chatreghermez-sitemap-v5-target-predeploy.xml. OOH-002's URL is still
# PENDING_AUDIT in the entity registry; its slug here is a working one.
SLUGS = {
    "OOH-002": "media-rental",
    "WEB-002": "corporate-web-design", "WEB-003": "ecommerce-web-design",
    "WEB-004": "custom-web-design", "WEB-005": "wordpress-web-design",
    "WEB-006": "website-redesign", "WEB-007": "landing-page-design", "WEB-008": "ui-ux-design",
    "SEO-002": "ecommerce-seo", "SEO-003": "local-seo", "SEO-004": "technical-seo",
    "SEO-005": "seo-consulting",
    "SUP-001": "website-support", "SUP-002": "wordpress-support",
    "SUP-003": "website-speed-optimization", "SUP-004": "website-troubleshooting",
    "SOC-002": "instagram-management", "SOC-003": "instagram-content-production",
    "SOC-004": "reels-production",
    "GD-001": "logo-design", "GD-002": "visual-identity-design", "GD-003": "stationery-design",
    "GD-004": "business-card-design", "GD-007": "catalog-design", "GD-008": "brochure-design",
    "GD-009": "banner-design", "GD-010": "website-banner-design", "GD-011": "billboard-design",
    "GD-012": "poster-design", "GD-013": "lightbox-design", "GD-014": "exhibition-stand-design",
    "GD-015": "exhibition-backlight-design", "GD-016": "packaging-design", "GD-017": "label-design",
    "PRN-002": "banner-printing", "PRN-003": "vinyl-printing", "PRN-004": "backlit-printing",
    "PRN-005": "lightbox-fabric-printing", "PRN-008": "catalog-printing",
    "PRN-009": "brochure-printing", "PRN-010": "stationery-printing",
    "PRN-011": "business-card-printing",
    "PF-001": "industrial-photography", "PF-002": "advertising-photography",
    "PF-003": "product-photography", "PF-004": "advertising-video-production",
    "PF-005": "industrial-video-production",
    "CON-001": "advertising-consulting", "CON-004": "marketing-consulting",
    "CON-005": "marketing-strategy", "CON-007": "business-consulting",
    "CON-008": "business-systemization",
}
# Services whose samples are moving pictures: the card and hero slot is a
# video (Remotion cover or the film itself), not a still.
VIDEO = {"SOC-004", "PF-004", "PF-005"}
ROLES = {
    "ooh": ["طراحی", "چاپ", "نصب و اکران"],
    "digital": ["طراحی", "پیاده‌سازی", "محتوا"],
    "graphic": ["ایده", "طراحی", "آماده‌سازی چاپ"],
    "print": ["آماده‌سازی فایل", "چاپ", "تحویل"],
    "photo": ["کارگردانی", "تصویربرداری", "تدوین"],
    "consult": ["تشخیص", "برنامه", "همراهی اجرا"],
}


# Preview-only photography: the owner's real samples, taken from the agency's
# Telegram samples group on 2026-10-28 (media/portfolio-demo/). The owner
# uploads the finals in WordPress; until then these make the draft read as
# the launched page it will be (owner's design benchmark rule, 2026-10-27).
# Mapped by what each picture shows, to the final service it is a sample of.
DEMO_MEDIA = "media/portfolio-demo"
def _r(prefix: str, *nums: int) -> list[str]:
    return [f"{prefix}-{n:02d}.jpg" for n in nums]
DEMO = {
    "logo-design": _r("logo", 1, 9, 7, 11, 4, 12),
    "visual-identity-design": _r("identity", 3, 1, 2, 4, 5, 6),
    "stationery-design": _r("identity", 7, 9, 10) + _r("stationery", 2, 3, 5),
    "business-card-design": _r("business-card", 2, 7, 3, 1, 6, 12),
    "catalog-design": _r("catalogue", 4, 9, 11, 3, 10, 12),
    "brochure-design": _r("catalogue", 6, 7, 8, 5),
    "poster-design": _r("flyer", 8, 7, 2, 1),
    "banner-design": _r("banner", 6, 7, 8, 9),
    "billboard-design": _r("straboard", 5, 8, 1, 10, 3, 6),
    "lightbox-design": _r("lightbox-h", 1, 2) + _r("lightbox-v", 6, 2, 9, 3),
    "packaging-design": _r("packaging", 4, 9, 5, 2, 8, 10),
    "label-design": _r("label", 1, 4, 2, 5),
    "instagram-content-production": _r("instagram", 5, 1, 3, 4, 8, 2),
    "website-banner-design": _r("website", 7, 8, 9),
}
# The agency's own red service graphics stand in as family covers.
FAMILY_COVER = {
    "ooh": "straboard-08.jpg", "digital": "website-06.jpg", "graphic": "identity-07.jpg",
    "print": "catalogue-10.jpg", "photo": "website-04.jpg", "consult": "website-02.jpg",
}


# ── Stage-4 copy (ru-content, 2026-10-28) ─────────────────────────────────
# Persona 3 (vendor scout). Every fact below is from the owner-approved
# introduction (ru-content owner-voice §9, §13): licence 1392 from the
# Isfahan Ershad directorate, first investment project Fooladshahr 1395,
# Tehran workshop + large-format print shop + sales office, Isfahan
# large-format print shop + investment office + agency, projects in Kirkuk
# and Sulaymaniyah. No number here is invented.
FAMILY_COPY = {
    "ooh": "از طراحی بیلبورد و استرابورد تا چاپ و نصب. سازه‌ها را در کارگاه خودمان در تهران می‌سازیم و از سال ۱۳۹۵ با شهرداری‌ها پروژهٔ شهری اجرا کرده‌ایم.",
    "digital": "سایت و اینستاگرام شما باید بعد از تحویل هم کار کنند، نه فقط روز رونمایی زیبا باشند.",
    "graphic": "از لوگو و هویت بصری تا کاتالوگ و بسته‌بندی. برند شما باید روی کاغذ و روی گوشی یکی دیده شود.",
    "print": "چاپ لارج‌فرمت در دو چاپخانهٔ خودمان در تهران و اصفهان؛ کار شما بدون واسطه چاپ می‌شود.",
    "photo": "عکس و فیلمی که پشت کاتالوگ و سایت شما می‌ایستد؛ از عکاسی محصول تا فیلم صنعتی.",
    "consult": "پیش از اینکه بودجه‌تان خرج شود، روشن می‌کنیم کدام کار لازم است و کدام نه.",
}
FAQ = [
    ("رزومه و مدارک چتر قرمز را چطور بگیرم؟",
     "فرم پایین همین صفحه را پر کنید یا تماس بگیرید. رزومهٔ شرکت و مدارک فعالیت را برایتان می‌فرستیم؛ چتر قرمز از سال ۱۳۹۲ با مجوز ادارهٔ کل فرهنگ و ارشاد اسلامی استان اصفهان در تبلیغات محیطی کار می‌کند."),
    ("نمونهٔ کاری شبیه کار ما دارید؟",
     "در بخش نمونه‌ها اول حوزهٔ کار و بعد خدمت را انتخاب کنید. اگر نمونهٔ همان صنعت را پیدا نکردید، در فرم بنویسید چه کاری دارید؛ نزدیک‌ترین نمونه‌ها را جدا برایتان می‌فرستیم."),
    ("قیمت تقریبی کار چقدر است؟",
     "قیمت ثابت نداریم. قیمت به اندازهٔ کار، زمان تحویل و آنچه از قبل دارید بستگی دارد، پس برای کار مشخص برآورد را پس از دیدن شرح کار می‌فرستیم. عدد سرِدستی نمی‌دهیم."),
    ("انجام کار چقدر طول می‌کشد؟",
     "به نوع کار بستگی دارد و طراحی یک لوگو با ساخت یک سازه زمان یکسانی ندارد. زمان دقیق را همراه برآورد هزینه اعلام می‌کنیم. اگر مهلت ثابتی مثل نمایشگاه دارید، همان را در فرم بنویسید."),
    ("فقط در اصفهان کار می‌کنید؟",
     "نه. در اصفهان چاپخانهٔ لارج‌فرمت، دفتر مدیریت سرمایه‌گذاری و آژانس داریم و در تهران کارگاه ساخت سازه، چاپخانه و دفتر فروش. پروژه در شهرهای دیگر و خارج از ایران، مثل کرکوک و سلیمانیه در عراق، هم اجرا کرده‌ایم."),
]
# One line per carousel card, about that service, not its family: a
# billboard card must not read like a catalogue card (publish gate,
# extraction test, 2026-10-28). No claims, no numbers.
FEATURED_COPY = {
    "billboard-design": "بیلبورد را از پشت فرمان و در چند ثانیه می‌بینند؛ طرح باید از همان فاصله خوانده شود.",
    "stationery-design": "سربرگ، کارت ویزیت و پاکت با یک زبان؛ تا نامهٔ شما پیش از خوانده‌شدن معرفی‌تان کند.",
    "packaging-design": "بسته‌بندی در قفسه چند ثانیه فرصت دارد؛ باید محصول را بفروشد، نه فقط بپوشاند.",
    "instagram-content-production": "پستی که برای مخاطب شما ساخته شده، نه برای پر کردن صفحه.",
    "catalog-design": "کاتالوگی که کارشناس خرید بتواند در جلسه ورق بزند و مشخصات را زود پیدا کند.",
    "lightbox-design": "لایت‌باکس شب هم کار می‌کند؛ طرحش باید با نور پشت آن هم خوانا بماند.",
    "logo-design": "لوگویی که روی سربرگ، تابلو و صفحهٔ گوشی یکی دیده شود.",
}
FEATURED = [  # the 3D carousel: one strong picture per area
    ("billboard-design", "straboard-06.jpg"), ("stationery-design", "identity-07.jpg"),
    ("packaging-design", "packaging-04.jpg"), ("instagram-content-production", "instagram-05.jpg"),
    ("catalog-design", "catalogue-09.jpg"), ("lightbox-design", "lightbox-h-01.jpg"),
    ("logo-design", "logo-07.jpg"),
]


def fa(n: int, width: int = 0) -> str:
    return str(n).rjust(width, "0").translate(DIGITS)


def alt_for(name: str) -> str:
    """The owner's ALT pattern. Braces are the fields WordPress fills in."""
    return f"{name} برای {{نام پروژه یا صنعت مشتری}}، {{شهر}}، {{سال}} — نمونه کار {name} چتر قرمز"


def final_services() -> list[dict]:
    rows = []
    for s in load_services():
        if s.id not in SLUGS:
            continue
        rows.append({"id": s.id, "name": s.name, "family": FAMILY_KEY[s.family],
                     "slug": SLUGS[s.id], "video": s.id in VIDEO})
    missing = set(SLUGS) - {r["id"] for r in rows}
    if missing:
        raise SystemExit(f"registry no longer has: {sorted(missing)}")
    return rows


def build(view: dict | None, services: list[dict]) -> dict:
    by_family = collections.defaultdict(list)
    for s in services:
        by_family[s["family"]].append(s)

    # ── samples: the owner's real pictures where the preview has them,
    #    otherwise two reserved slots per final service ────────────────
    items = []
    for key, _, _ in FAMILIES:
        for s in by_family[key]:
            pics = DEMO.get(s["slug"]) or [None, None]
            for k, pic in enumerate(pics, start=1):
                item = {
                    "family": key, "service": s["slug"], "service_label": s["name"],
                    "code": f"RU-{s['id']}-{k:02d}",
                    "title": f"نمونه‌کار {s['name']}",
                    "meta": "صنعت مشتری · شهر · سال",
                    "roles": [{"value": r} for r in ROLES[key]],
                    "href": f"/portfolio/{s['slug']}-{k:02d}/",
                    "label": "جایگاه ویدئو" if s["video"] else "جایگاه عکس",
                    "alt": alt_for(s["name"]),
                    "placeholder": True,
                }
                if pic:
                    item["src"] = f"assets/{pic}"
                items.append(item)
    # Pictured samples lead, and on a service view that service leads.
    items.sort(key=lambda i: ((view is not None and i["service"] != view["slug"]), "src" not in i))
    if not view:
        # interleave services so the hub's first screens show range, not one service
        pictured = [i for i in items if "src" in i]
        rest = [i for i in items if "src" not in i]
        buckets = collections.OrderedDict()
        for i in pictured:
            buckets.setdefault(i["service"], []).append(i)
        mixed = []
        while any(buckets.values()):
            for b in buckets.values():
                if b:
                    mixed.append(b.pop(0))
        # The hub carries only pictured samples. Empty reserved slots live on
        # each service view, where the owner fills them; on the hub they were
        # most of the HTML weight and said nothing (ru-senior-seo checklist 21).
        items = mixed
    # HTML budget (180KB, critic "performance"): the static page carries a
    # bounded set; WordPress paginates the full archive server-side. The hub
    # keeps two pictured samples per service; a service view keeps every slot
    # of its own service and one pictured sample of each other service.
    per_service: dict[str, int] = collections.Counter()
    bounded = []
    for i in items:
        own = view is not None and i["service"] == view["slug"]
        cap = 99 if own else (2 if view is None else 1)
        if not own and "src" not in i:
            continue
        if per_service[i["service"]] < cap:
            per_service[i["service"]] += 1
            bounded.append(i)
    items = bounded

    # ── hero slides: pinned pictured samples ────────────────────────────
    if view and DEMO.get(view["slug"]):
        pins = [(view, p) for p in DEMO[view["slug"]][:5]]
    else:
        pins = [(next(x for x in services if x["slug"] == slug), DEMO[slug][0]) for slug in
                ("billboard-design", "stationery-design", "packaging-design",
                 "instagram-content-production", "lightbox-design")]
    slides = []
    for i, (s, pic) in enumerate(pins, start=1):
        slides.append({
            "title": f"نمونه‌کار {s['name']}" + (f" {fa(i)}" if view else ""),
            "service": s["name"],
            "client": "صنعت مشتری",
            "city": "شهر",
            "year": "سال",
            "role": "نقش ما",
            "src": f"assets/{pic}", "thumb": f"assets/{pic}",
            "eager": "1" if i == 1 else "",
            "label": "جایگاه عکس",
            "alt": alt_for(s["name"]),
            "placeholder": True,
        })

    name = view["name"] if view else None
    crumb = [{"label": "خانه", "href": "/"}]
    if view:
        crumb.append({"label": "نمونه‌کارها", "href": "/portfolio/"})
    blocks = []

    blocks.append({"block": "portfolio-hero", "anchor": "top", "data": {
        "breadcrumb": crumb,
        "crumb_current": name or "نمونه‌کارها",
        "eyebrow": "نمونه‌کار · " + (dict((k, f) for k, f, _ in FAMILIES)[view["family"]] if view else "چتر قرمز"),
        "title": f"نمونه کار {name}" if view else "نمونه کارهای شرکت تبلیغاتی چتر قرمز؛ از لوگو تا بیلبورد",
        "lead": (f"نمونه کارهای {name} چتر قرمز، یک‌جا. کنار هر نمونه نوشته‌ایم برای چه صنعتی "
                 "و در چه سالی انجام شده است. برای تصمیم یا استعلام، لینک همین صفحه کافی است." if view else
                 "دنبال نمونهٔ دقیقاً همین کار هستید؟ اینجا نمونه‌کارهای چتر قرمز "
                 "را بر اساس خدمت چیده‌ایم و کنار هر نمونه نوشته‌ایم برای چه صنعتی بوده و سهم ما در آن چه بوده است. "
                 "خدمت موردنظرتان را انتخاب کنید، ببینید یا برای تصمیم‌گیرنده بفرستید."),
        "primary": {"label": "دریافت رزومه و مدارک", "href": "#lead"},
        "share": {"label": "کپی لینک همین صفحه", "done": "لینک کپی شد"},
        "rail_label": "نمونه‌های منتخب",
        "slides": slides,
        "slides_total": fa(len(slides), 2),
    }})

    blocks.append({"block": "portfolio-grid", "anchor": "samples", "data": {
        "eyebrow": "نمونه‌ها",
        "title": f"نمونه‌های {name}" if view else "نمونهٔ همان کاری را می‌خواهید؟",
        "aside": ("اول حوزهٔ کار را انتخاب کنید، بعد خدمت را. شمار نمونه‌ها همان لحظه عوض می‌شود "
                  "و نشانی صفحه هم با انتخاب شما تغییر می‌کند تا همان را بفرستید."),
        "family_label": "حوزهٔ کار",
        "service_label": "خدمت",
        "all_label": "همه",
        "families": [{"value": k, "label": f, "icon": ic} for k, f, ic in FAMILIES],
        "services": [{"value": s["slug"], "label": s["name"], "family": s["family"],
                      "href": f"{VIEW_BASE}{s['slug']}/"} for s in services],
        "items": items,
        "items_total": fa(len(items)),
        "count_word": "نمونه",
        "more_label": "نمونه‌های بیشتر",
        "empty_text": "برای این خدمت هنوز نمونه‌ای منتشر نشده است.",
        "view_base": VIEW_BASE,
        "hub_href": "/portfolio/",
        "initial_service": view["slug"] if view else "",
    }})

    panels = []
    for n_, (key, fam, icon) in enumerate(FAMILIES, start=1):
        svc = by_family[key]
        panels.append({
            "index": fa(n_, 2),
            "title": fam, "icon": icon, "label": "جایگاه عکس",
            "src": f"assets/{FAMILY_COVER[key]}",
            "alt": f"نمونه کارهای {fam} چتر قرمز",
            "body": FAMILY_COPY[key],
            "links": [{"label": s["name"], "href": f"{VIEW_BASE}{s['slug']}/"} for s in svc[:4]],
            "href": f"{VIEW_BASE}{svc[0]['slug']}/",
            "cta": f"همهٔ نمونه‌های {fam}",
        })
    blocks.append({"block": "portfolio-accordion", "anchor": "areas", "data": {
        "eyebrow": "سایر کارها",
        "title": "نمونهٔ کار دیگری هم لازم دارید؟",
        "lead": "اگر نمونهٔ کار دیگری هم لازم دارید، از همین‌جا به همان بخش بروید.",
        "panels": panels,
    }})

    blocks.append({"block": "golden-line", "anchor": "golden", "data": {
        "eyebrow": "حرف حساب",
        "line": "اول نمونهٔ همان کار را ببینید، بعد تصمیم بگیرید.",
        "support": "صفحه‌ای که پر از ادعاست به کار جلسهٔ شما نمی‌آید. نمونهٔ نام‌دار می‌آید.",
    }})

    blocks.append({"block": "editorial-split", "anchor": "stakes", "data": {
        "eyebrow": "هزینهٔ انتخاب بدون نمونه",
        "title": "پیمانکاری که نمونهٔ مشابه ندارد، چقدر برایتان تمام می‌شود؟",
        "body": [
            "مدیر می‌پرسد: «نمونهٔ همین کار را دارند؟» و جوابی نیست. پیمانکار با چند عکس بی‌نام انتخاب "
            "می‌شود و کار، سه هفته مانده به نمایشگاه، به دوباره‌کاری می‌افتد.",
            "هزینهٔ این انتخاب فقط پول نیست. فرصت کمپین از دست می‌رود و پرسش‌ها به سمت کسی برمی‌گردد که "
            "پیمانکار را معرفی کرده بود؛ یعنی خود شما. برای همین کنار هر نمونهٔ این صفحه نوشته‌ایم برای چه کسی، کی و با چه سهمی از ما انجام شده است.",
        ],
        "image": {"label": "جایگاه عکس", "src": "assets/lightbox-v-02.jpg",
                  "alt": "لایت‌باکس تبلیغاتی نصب‌شده در خیابان، نمونه کار چتر قرمز"},
    }})

    blocks.append({"block": "numbered-features", "anchor": "steps", "data": {
        "eyebrow": "سه قدم",
        "title": "از دیدن نمونه تا شروع کار",
        "lead": "سه قدم، و هیچ‌کدام تماس اجباری ندارد.",
        "icon": "icon-process",
        "items": [
            {"index": "۰۱", "title": "نمونهٔ همان کار را ببینید", "body": "خدمت را از فیلتر انتخاب کنید و لینک همان نما را ببینید یا برای تصمیم‌گیرنده بفرستید.", "icon": "icon-portfolio"},
            {"index": "۰۲", "title": "رزومه و مدارک را بگیرید", "body": "نام و شماره را در فرم پایین بگذارید تا رزومهٔ شرکت و مدارک را برایتان بفرستیم.", "icon": "icon-datasheet"},
            {"index": "۰۳", "title": "شرح کار را بفرستید", "body": "هر وقت تصمیم گرفته شد، شرح کار را بفرستید تا زمان و هزینه را برآورد کنیم.", "icon": "icon-rfq"},
        ],
    }})

    blocks.append({"block": "compare-cards", "anchor": "beyond", "data": {
        "eyebrow": "فراتر از نمونه‌کار",
        "title": "دنبال پروژهٔ شهری یا سازهٔ تبلیغاتی هستید؟",
        "lead": ("نمونه‌کار اینجا یعنی کاری که برای یک کسب‌وکار یا سازمان طراحی یا تولید کرده‌ایم. "
                 "پروژه‌های سرمایه‌گذاری شهری و سازه‌های تبلیغاتی جای جداگانه دارند."),
        "icon": "icon-related",
        "items": [
            {"index": "۰۱", "title": "پروژه‌های شهری و مشارکتی", "body": "پروژه‌های مشارکتی با شهرداری‌ها، از فولادشهر در سال ۱۳۹۵ به بعد، با نوع قرارداد، شهر و مدت بهره‌برداری.",
             "icon": "icon-projects", "cta": {"label": "دیدن پروژه‌ها", "href": "/projects/"}},
            {"index": "۰۲", "title": "سازه‌های تبلیغاتی", "body": "بیلبورد، استرابورد، لایت‌باکس و دیگر سازه‌هایی که در کارگاه خودمان در تهران ساخته می‌شوند، با ابعاد و مشخصات فنی.",
             "icon": "icon-structures", "cta": {"label": "دیدن سازه‌ها", "href": "/structures/"}},
            {"index": "۰۳", "title": "همهٔ خدمات", "body": "شش حوزهٔ خدمت چتر قرمز، از تبلیغات محیطی تا مشاوره، و اینکه هر کار در کدام حوزه می‌نشیند.",
             "icon": "icon-services-nav", "cta": {"label": "دیدن خدمات", "href": "/services/"}},
        ],
    }})

    # ── facts at a glance (ru-senior-seo §5-ب.7–8): every row is from the
    #    owner-approved introduction (owner-voice §9, §13); none is invented.
    blocks.append({"block": "spec-table", "anchor": "facts", "data": {
        "eyebrow": "چتر قرمز در یک نگاه",
        "title": "چتر قرمز کیست و از کجا کار می‌کند؟",
        "lead": "پیش از تماس، همین چند سطر را ببینید؛ برای فرستادن به تصمیم‌گیرنده هم کافی است.",
        "columns": [{"value": "چتر قرمز"}],
        "rows": [
            {"label": "شروع فعالیت", "values": [{"value": "سال ۱۳۹۲، با مجوز ادارهٔ کل فرهنگ و ارشاد اسلامی استان اصفهان"}]},
            {"label": "واحدهای تهران", "values": [{"value": "کارگاه ساخت سازه‌های تبلیغاتی، چاپخانهٔ لارج‌فرمت، دفتر فروش"}]},
            {"label": "واحدهای اصفهان", "values": [{"value": "چاپخانهٔ لارج‌فرمت، دفتر مدیریت سرمایه‌گذاری، آژانس تبلیغاتی"}]},
            {"label": "حوزه‌های خدمت", "values": [{"value": f"شش حوزه و {fa(len(services))} خدمت؛ از تبلیغات محیطی تا مشاوره"}]},
            {"label": "پروژه بیرون از ایران", "values": [{"value": "کرکوک و سلیمانیه در عراق، از بیلبورد عرشهٔ پل تا بیلبورد تک‌پایه"}]},
        ],
        "footnote": f"آخرین بازبینی این صفحه: {REVIEWED_FA} · بازبینی بعدی: {NEXT_REVIEW_FA}",
    }})

    blocks.append({"block": "faq-section-final", "anchor": "faq", "data": {
        "eyebrow": "پرسش‌های پرتکرار",
        "title": "پیش از تماس، جواب کوتاه را همین‌جا ببینید",
        "lead": "پرسش‌هایی که کارشناس‌ها و مدیران پیش از استعلام می‌پرسند؛ هر جواب جداگانه کامل است.",
        "questions": [{"q": q, "a": a} for q, a in FAQ],
    }})

    blocks.append({"block": "call-card", "anchor": "call", "data": {
        "eyebrow": "سریع‌ترین راه",
        "title": "برای دریافت رزومه، تماس بگیرید",
        "number": {"display": "۰۹۱۳ ۳۳۵ ۳۴۳۲", "href": "tel:+989133353432",
                   "aria": "تماس با چتر قرمز، ۰۹۱۳ ۳۳۵ ۳۴۳۲"},
        "note": "اگر دستمان بند بود، همان روز برمی‌گردیم.",
        "still": "1",
    }})
    blocks.append({"block": "site-type", "anchor": "type", "data": {}})
    blocks.append({"block": "page-cursor", "anchor": "cursor", "data": {"states": [
        {"selector": "[data-block=\"portfolio-hero\"] .pf-stage-frame", "state": "drag", "label": "بکشید"},
        {"selector": "[data-block=\"portfolio-hero\"] .pf-slide.is-video", "state": "play", "label": ""},
        {"selector": "[data-block=\"portfolio-grid\"] .pf-card", "state": "view", "label": "ببینید"},
        {"selector": "[data-block=\"portfolio-accordion\"] .pfa-panel", "state": "drag", "label": "باز کنید"},
        {"selector": "[data-block=\"faq-section-final\"] summary", "state": "open", "label": "+"},
        {"selector": "[data-block=\"lead-form\"] .primary-button", "state": "send", "label": ""},
    ]}})
    blocks.append({"block": "lead-form", "anchor": "lead", "data": {
        "eyebrow": "قدم بعدی",
        "title": "رزومه و مدارک را برایتان بفرستیم",
        "lead": "نام، شماره و کاری که دنبال نمونه‌اش هستید را بنویسید. همین کافی است؛ بقیه را ما پیگیری می‌کنیم.",
        "icon": "icon-rfq",
        "fields": [
            {"name": "name", "label": "اسم و نام مجموعه", "type": "text", "inputmode": "text",
             "autocomplete": "organization", "placeholder": "مثلاً رضا محمدی، صنایع فلزی آریا", "icon": "icon-user"},
            {"name": "phone", "label": "شماره تماس", "type": "tel", "inputmode": "tel",
             "autocomplete": "tel", "placeholder": "۰۹۱۳۱۲۳۴۵۶۷", "icon": "icon-phone"},
            {"name": "subject", "label": "نمونهٔ چه کاری را می‌خواهید؟", "type": "text", "inputmode": "text",
             "autocomplete": "off", "placeholder": name or "مثلاً طراحی لوگو", "icon": "icon-portfolio"},
        ],
        "submit": "بفرستید",
    }})

    # ── the 3D carousel of selected work (owner, 2026-10-28) ─────────────
    by_slug = {x["slug"]: x for x in services}
    blocks.append({"block": "service-coverflow", "anchor": "featured", "data": {
        "eyebrow": "کارهای منتخب",
        "title": "کدام کار به کار شما نزدیک‌تر است؟",
        "lead": "کارت‌ها را بکشید. هر کارت یک نمونهٔ واقعی است و به نمای همان خدمت می‌رود.",
        "prev_label": "نمونهٔ قبلی", "next_label": "نمونهٔ بعدی",
        "items": [{
            "kicker": by_slug[sl]["name"],
            "title": f"نمونه‌کار {by_slug[sl]['name']}",
            "body": FEATURED_COPY[sl],
            "points": [{"value": r} for r in ROLES[by_slug[sl]["family"]]],
            "src": f"assets/{pic}", "label": "جایگاه عکس", "alt": alt_for(by_slug[sl]["name"]),
            "href": f"{VIEW_BASE}{sl}/", "link_label": f"نمونه‌های {by_slug[sl]['name']}",
            "index": fa(k, 2),
        } for k, (sl, pic) in enumerate(FEATURED, start=1)],
    }})
    # facts sits right after the catalogue: the composer allows no third
    # light surface in a row anywhere else, and after the samples is where a
    # scout writing a vendor note needs it (2026-10-28).
    order = ["top", "featured", "samples", "facts", "golden", "stakes", "areas", "steps", "beyond",
             "faq", "call", "type", "cursor", "lead"]
    blocks.sort(key=lambda bl: order.index(bl["anchor"]))
    for bl in blocks:
        if bl["block"] == "page-cursor":
            bl["data"]["states"][0:0] = [{"selector": "[data-block=\"service-coverflow\"] .service-cf-card",
                                          "state": "drag", "label": "بکشید"}]
            bl["data"]["states"] = [st for st in bl["data"]["states"] if st["state"] != "play"][:6]

    slug = f"portfolio-{view['slug']}" if view else "portfolio"
    return collections.OrderedDict([
        ("slug", slug), ("lang", "fa"), ("direction", "rtl"),
        ("title", f"نمونه کار {name} | چتر قرمز" if view else "نمونه کارهای شرکت تبلیغاتی چتر قرمز | از لوگو تا بیلبورد"),
        ("description", (f"نمونه کارهای {name} چتر قرمز، با صنعت مشتری و سهم ما در هر کار. لینک را ببینید، برای تصمیم‌گیرنده بفرستید یا رزومه و مدارک را بگیرید."
                         if view else "نمونه کارهای چتر قرمز در شش حوزه، از طراحی لوگو تا بیلبورد؛ کنار هر نمونه صنعت مشتری و سهم ما آمده است. خدمت موردنظرتان را ببینید و لینکش را بفرستید.")),
        ("canonical", f"https://chatreghermez.com{VIEW_BASE}{view['slug']}/" if view
         else "https://chatreghermez.com/portfolio/"),
        ("shell", SITE_SHELL_REF), ("nav_section", "/portfolio/"),
        ("media", DEMO_MEDIA),
        ("schema_item_type", "CreativeWork"), ("schema_area_served", ["اصفهان", "ایران"]),
        # ── SEO pack (ru-senior-seo, pages/drafts/portfolio.seo.md) ───────
        ("page_type", "CollectionPage"),
        ("robots", "index, follow, max-image-preview:large"),
        ("date_published", REVIEWED_ISO), ("date_modified", REVIEWED_ISO),
        ("breadcrumb", [{"name": "خانه", "url": "https://chatreghermez.com/"},
                        {"name": "نمونه‌کارها", "url": "https://chatreghermez.com/portfolio/"}]
         + ([{"name": name, "url": f"https://chatreghermez.com{VIEW_BASE}{view['slug']}/"}] if view else [])),
        ("og", {"type": "website", "site_name": "چتر قرمز",
                "image": "https://chatreghermez.com/media/og/portfolio-1200x630.jpg",
                "image_alt": f"نمونه کارهای {name} چتر قرمز" if view else "نمونه کارهای چتر قرمز، از لوگو تا بیلبورد"}),
        ("motion_score", {"declared": "portfolio_hub",
                          "verbs": ["active-card-becomes-hero", "skeleton-to-content", "perspective-drag",
                                    "kinetic-oversized-type", "horizontal-accordion"],
                          "note": "The full portfolio_hub score, plus perspective-drag for the selected-work 3D carousel: a second heavy verb, an exception to §21 rule 4 the owner chose on 2026-10-28. call-card runs `still` so ambient-field stays out (owner, 2026-10-27)."}),
        ("blocks", blocks),
    ])


def main(argv: list[str]) -> None:
    services = final_services()
    out = ROOT / "pages" / "drafts"
    view_slug = argv[argv.index("--view") + 1] if "--view" in argv else "logo-design"
    view = next(s for s in services if s["slug"] == view_slug)
    for spec in (build(None, services), build(view, services)):
        path = out / f"{spec['slug']}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tagged = json.dumps(spec, ensure_ascii=False).count('"placeholder": true')
        print(f"{path.relative_to(ROOT)}: {len(spec['blocks'])} blocks, {tagged} tagged placeholders")
    print(f"final services: {len(services)}")


if __name__ == "__main__":
    main(sys.argv[1:])
