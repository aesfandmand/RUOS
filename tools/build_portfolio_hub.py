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

    # ── samples: two placeholder samples per final service ────────────
    items, n = [], 0
    for key, _, _ in FAMILIES:
        for s in by_family[key]:
            for k in (1, 2):
                n += 1
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
                items.append(item)
    if view:
        items.sort(key=lambda i: i["service"] != view["slug"])

    # ── hero slides: pinned samples for this view, or one per family ──
    if view:
        pinned = [view] * 3 + [s for s in by_family[view["family"]] if s is not view][:2]
    else:
        pinned = [by_family[k][0] for k, _, _ in FAMILIES[:5]]
    slides = []
    for i, s in enumerate(pinned, start=1):
        slides.append({
            "title": f"نمونه‌کار {s['name']}" + (f" {fa(i)}" if view and s is view else ""),
            "service": s["name"],
            "client": "صنعت مشتری",
            "city": "شهر",
            "year": "سال",
            "role": "نقش ما",
            "label": "جایگاه ویدئو (Remotion)" if s["video"] or i == 1 else "جایگاه عکس",
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
        "title": f"نمونه کار {name}" if view else "نمونه کارهای شرکت تبلیغاتی چتر قرمز",
        "lead": LOREM,
        "primary": {"label": "دریافت رزومه و مدارک", "href": "#lead"},
        "share": {"label": "کپی لینک همین صفحه", "done": "لینک کپی شد"},
        "rail_label": "نمونه‌های منتخب",
        "slides": slides,
        "slides_total": fa(len(slides), 2),
    }})

    blocks.append({"block": "portfolio-grid", "anchor": "samples", "data": {
        "eyebrow": "نمونه‌ها",
        "title": f"نمونه‌های {name}" if view else "نمونهٔ همان کاری را می‌خواهید؟",
        "aside": LOREM,
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
            "alt": f"نمونه کارهای {fam} چتر قرمز",
            "body": LOREM, "placeholder": True,
            "links": [{"label": s["name"], "href": f"{VIEW_BASE}{s['slug']}/"} for s in svc[:4]],
            "href": f"{VIEW_BASE}{svc[0]['slug']}/",
            "cta": f"همهٔ نمونه‌های {fam}",
        })
    blocks.append({"block": "portfolio-accordion", "anchor": "areas", "data": {
        "eyebrow": "سایر کارها",
        "title": "همین مشتری‌ها، کارهای دیگری هم از ما گرفته‌اند",
        "lead": LOREM,
        "panels": panels,
    }})

    blocks.append({"block": "golden-line", "anchor": "golden", "data": {
        "eyebrow": "حرف حساب",
        "line": "جملهٔ طلایی صفحه، در مرحلهٔ متن نوشته می‌شود",
        "support": LOREM,
    }})

    blocks.append({"block": "editorial-split", "anchor": "stakes", "data": {
        "eyebrow": "هزینهٔ انتخاب بدون نمونه",
        "title": "پیمانکاری که نمونهٔ مشابه ندارد، چقدر برایتان تمام می‌شود؟",
        "body": [LOREM, LOREM],
        "image": {"label": "جایگاه عکس",
                  "alt": "پشت صحنهٔ آماده‌سازی غرفهٔ نمایشگاه با مهلت تنگ، کارگاه چتر قرمز"},
    }})

    blocks.append({"block": "numbered-features", "anchor": "steps", "data": {
        "eyebrow": "سه قدم",
        "title": "از دیدن نمونه تا شروع کار",
        "lead": LOREM,
        "icon": "icon-process",
        "items": [
            {"index": "۰۱", "title": "نمونهٔ همان کار را ببینید", "body": LOREM, "placeholder": True, "icon": "icon-portfolio"},
            {"index": "۰۲", "title": "رزومه و مدارک را بگیرید", "body": LOREM, "placeholder": True, "icon": "icon-datasheet"},
            {"index": "۰۳", "title": "بریف کار را بفرستید", "body": LOREM, "placeholder": True, "icon": "icon-rfq"},
        ],
    }})

    blocks.append({"block": "compare-cards", "anchor": "beyond", "data": {
        "eyebrow": "فراتر از نمونه‌کار",
        "title": "پروژه‌های شهری و سازه‌ها صفحهٔ خودشان را دارند",
        "lead": LOREM,
        "icon": "icon-related",
        "items": [
            {"index": "۰۱", "title": "پروژه‌های شهری و مشارکتی", "body": LOREM, "placeholder": True,
             "icon": "icon-projects", "cta": {"label": "دیدن پروژه‌ها", "href": "/projects/"}},
            {"index": "۰۲", "title": "سازه‌های تبلیغاتی", "body": LOREM, "placeholder": True,
             "icon": "icon-structures", "cta": {"label": "دیدن سازه‌ها", "href": "/structures/"}},
            {"index": "۰۳", "title": "همهٔ خدمات", "body": LOREM, "placeholder": True,
             "icon": "icon-services-nav", "cta": {"label": "دیدن خدمات", "href": "/services/"}},
        ],
    }})

    blocks.append({"block": "faq-section-final", "anchor": "faq", "data": {
        "eyebrow": "پرسش‌های پرتکرار",
        "title": "پیش از تماس، جواب کوتاه را همین‌جا ببینید",
        "lead": "پرسش‌ها در مرحلهٔ متن از پیشنهاد خودکار گوگل ایران برداشته می‌شوند.",
        "questions": [{"q": f"پرسش {fa(i)} از تقاضای واقعی جست‌وجو", "a": LOREM, "placeholder": True}
                      for i in range(1, 6)],
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
        "lead": LOREM,
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

    slug = f"portfolio-{view['slug']}" if view else "portfolio"
    return collections.OrderedDict([
        ("slug", slug), ("lang", "fa"), ("direction", "rtl"),
        ("title", f"نمونه کار {name} | چتر قرمز" if view else "نمونه کارهای شرکت تبلیغاتی چتر قرمز"),
        ("description", "نمونه‌کار با نام پروژه، شهر، سال و نقش ما؛ بر اساس خدمت."),
        ("canonical", f"https://chatreghermez.com{VIEW_BASE}{view['slug']}/" if view
         else "https://chatreghermez.com/portfolio/"),
        ("shell", SITE_SHELL_REF), ("nav_section", "/portfolio/"),
        ("schema_item_type", "CreativeWork"), ("schema_area_served", ["اصفهان", "ایران"]),
        ("motion_score", {"declared": "portfolio_hub",
                          "verbs": ["active-card-becomes-hero", "skeleton-to-content",
                                    "horizontal-accordion", "kinetic-oversized-type"],
                          "note": "The full portfolio_hub score. call-card runs `still` so ambient-field stays out (owner, 2026-10-27)."}),
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
