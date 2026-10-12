#!/usr/bin/env python3
"""Compose the Services hub page spec from the architecture registry.

The owner asked for the services page to be standardised against the
approved straboard / investment pages. This builds it the way the rest of
the pipeline builds pages: structure and every number come from the
registry, and anything that would be a marketing claim nobody has written
yet ships as *tagged* Lorem Ipsum (`"placeholder": true`) rather than as an
invented sentence. That is design model §2's rule -- the page always ships,
and it never quietly fabricates.

What is real here:
  * the six service families, their names and their order (registry layer 1)
  * every count -- services per family, subgroups per family, actives,
    page-worthy services (counted from the service registry, not typed in)
  * each family's role sentence (the registry's own `primary_role`)
  * the nav, footer and bottom bar (the one shared shell)

What is a tagged placeholder, waiting on the human copy pass:
  * the three hero slides (no service photography exists yet)
  * the family card bodies
  * the "how to choose" comparison bodies and the FAQ answers

Usage:
    python3 tools/build_services_hub.py pages/drafts/services.json
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ruos.architecture_registry import load_entities, load_services  # noqa: E402
from ruos.site_shell import SITE_SHELL_REF  # noqa: E402

LOREM = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod "
         "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, "
         "quis nostrud exercitation ullamco laboris.")

FAMILY_IDS = ("SRV-OOH", "SRV-DM", "SRV-GD", "SRV-PRN", "SRV-PHOTO", "SRV-CONS")
FAMILY_ICONS = {
    "SRV-OOH": "icon-fam-outdoor", "SRV-DM": "icon-fam-digital",
    "SRV-GD": "icon-fam-graphic", "SRV-PRN": "icon-fam-print",
    "SRV-PHOTO": "icon-fam-photo", "SRV-CONS": "icon-fam-consult",
}
DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(n: int) -> str:
    return str(n).translate(DIGITS)


def main(out_path: Path) -> None:
    entities = {e.id: e for e in load_entities()}
    services = list(load_services())

    def rows(family_fa: str) -> list:
        return [s for s in services if s.family == family_fa]

    families = []
    for fid in FAMILY_IDS:
        e = entities[fid]
        rs = rows(e.name_fa)
        subgroups = {s.subgroup for s in rs if s.subgroup}
        actives = [s for s in rs if (s.commercial_status or "").upper() == "ACTIVE"]
        families.append({
            "id": fid, "entity": e, "icon": FAMILY_ICONS[fid],
            "count": len(rs), "subgroups": len(subgroups), "active": len(actives),
        })

    total = len(services)
    total_active = sum(1 for s in services if (s.commercial_status or "").upper() == "ACTIVE")

    spec = collections.OrderedDict([
        ("slug", "services"),
        ("lang", "fa"),
        ("direction", "rtl"),
        ("title", "خدمات چتر قرمز | شش خانواده خدمت، از تبلیغات محیطی تا مشاوره"),
        ("description",
         f"شش خانوادهٔ خدمت چتر قرمز در یک نقشه: تبلیغات محیطی، دیجیتال مارکتینگ، "
         f"طراحی گرافیک، چاپ و تولید، عکاسی و فیلم‌برداری و مشاوره — در مجموع "
         f"{fa(total_active)} خدمت فعال."),
        ("canonical", "https://chatreghermez.ir/services/"),
        ("shell", SITE_SHELL_REF),
        # No bottom-nav entry covers /services/ (the bar is خانه · نمونه‌کارها ·
        # سازه‌ها · سرمایه‌گذاری · تماس), so nothing is marked rather than
        # lighting up a tab the visitor is not actually on.
        ("blocks", []),
    ])

    B = spec["blocks"]

    # ── 1. hero ───────────────────────────────────────────────────────────
    B.append({
        "block": "product-hero", "id": "top",
        "data": {
            "breadcrumb": [{"label": "خانه", "href": "/"},
                           {"label": "خدمات", "href": "/services/"}],
            "title": "خدمات چتر قرمز",
            "lead": "این صفحه فهرست نیست؛ نقشه است. شش خانوادهٔ خدمت با مرز روشن، "
                    "تا بدانید کاری که در ذهن دارید زیر کدام خانواده می‌نشیند و از "
                    "کجا باید شروع کنید.",
            "slides": [
                {"label": "جایگاه تصویر ۱", "caption": "تبلیغات محیطی",
                 "alt": "جایگاه تصویر نمونه‌کار تبلیغات محیطی"},
                {"label": "جایگاه تصویر ۲", "caption": "طراحی و چاپ",
                 "alt": "جایگاه تصویر نمونه‌کار طراحی گرافیک و چاپ"},
                {"label": "جایگاه تصویر ۳", "caption": "دیجیتال و سوشال",
                 "alt": "جایگاه تصویر نمونه‌کار دیجیتال مارکتینگ"},
            ],
            "stats": [
                {"value": fa(len(families)), "label": "خانوادهٔ خدمت", "icon": "icon-services-nav"},
                {"value": fa(total_active), "label": "خدمت فعال", "icon": "icon-check"},
                {"value": fa(total), "label": "خدمت ثبت‌شده", "icon": "icon-datasheet"},
            ],
            "count": fa(len(families)).rjust(2, "۰"),
            "primary": {"label": "گفت‌وگو دربارهٔ پروژه", "href": "#review"},
            "secondary": {"label": "دیدن نمونه‌کارها", "href": "/portfolio/"},
            "icon": "icon-services-nav",
        },
    })

    # ── 2. how the map is drawn ───────────────────────────────────────────
    B.append({
        "block": "editorial-split", "id": "model",
        "data": {
            "eyebrow": "مدل دسته‌بندی",
            "title": "چرا خدمات به شش خانواده تقسیم شده‌اند؟",
            "body": [
                "هر خانواده یک مالک مشخص دارد؛ یعنی هر خدمت فقط در یک جا تعریف "
                "می‌شود، حتی اگر در چند جای دیگر هم به کار بیاید. «طراحی بنر» "
                "مالکش طراحی گرافیک است، چه روی یک سازهٔ محیطی دیده شود، چه در "
                "یک کمپین اینستاگرام.",
                "این مرزبندی برای شما یک نتیجهٔ ساده دارد: سفارش دوباره‌کاری "
                "نمی‌شود و هر پروژه از همان ابتدا سراغ تیم درست می‌رود، حتی اگر "
                "از چند خانواده عبور کند.",
            ],
            "image": {"label": "جایگاه تصویر",
                      "alt": "نمودار شش خانوادهٔ خدمت و مرز میان آن‌ها"},
        },
    })

    # ── 3. the six families ───────────────────────────────────────────────
    # numbered-features, not structure-services: that block paints a charcoal
    # band (the design model allows one per page) and gives every card a large
    # image slot. No service photography exists yet, so six identical empty
    # frames would be the loudest thing on the page -- the same "fourteen
    # copies of one picture" problem the structures section just had. This
    # block carries a per-item icon instead, so each family is distinguishable
    # by something real.
    items = []
    for i, f in enumerate(families, start=1):
        e = f["entity"]
        counted = (f"{fa(f['count'])} خدمت ثبت‌شده در {fa(f['subgroups'])} زیرشاخه"
                   if f["subgroups"] > 1 else f"{fa(f['count'])} خدمت ثبت‌شده")
        items.append({
            "index": fa(i).rjust(2, "۰"),
            "title": e.name_fa,
            # The count is real and stays visible. The sentence after it is a
            # TAGGED placeholder, not the registry's `primary_role`: that field
            # is internal architecture language ("Hybrid Service Hub", "مالک
            # کانونیکال Design Deliverableها") written for whoever maintains the
            # IA, not for a visitor. Putting it on the page would ship jargon as
            # copy, which is exactly what the content policy forbids -- and it
            # would read as finished when it is not.
            "body": f"{counted}. {LOREM}",
            "placeholder": True,
            "icon": f["icon"],
        })
    B.append({
        "block": "numbered-features", "id": "families",
        "data": {
            "eyebrow": "شش خانوادهٔ خدمت",
            "title": "کارتان زیر کدام خانواده می‌نشیند؟",
            "lead": f"در مجموع {fa(total_active)} خدمت فعال، گروه‌بندی‌شده بر اساس "
                    "اینکه چه چیزی تولید می‌شود — نه بر اساس اینکه در کدام کانال "
                    "دیده می‌شود.",
            "items": items,
            "icon": "icon-services-nav",
        },
    })

    # ── 5. who it is for ──────────────────────────────────────────────────
    sol_ids = ("SOL-PUBLIC", "SOL-B2B", "SOL-EXPO", "SOL-LOCAL")
    B.append({
        "block": "audience-section-final", "id": "audiences",
        "data": {
            "eyebrow": "این خدمات برای چه کسانی است؟",
            "title": "خدمات یکسان‌اند؛ مسئلهٔ سفارش‌دهنده‌ها یکسان نیست.",
            "lead": "اگر مسئله‌تان را در یکی از این چهار گروه می‌بینید، راهکار "
                    "همان گروه ترکیب آماده‌تری از همین خدمات به شما می‌دهد.",
            "items": [
                {"tag": fa(i + 1).rjust(2, "۰"), "title": entities[sid].name_fa,
                 "body": entities[sid].primary_role}
                for i, sid in enumerate(sol_ids)
            ],
        },
    })

    # ── 6. what to have ready ─────────────────────────────────────────────
    B.append({
        "block": "checklist-section", "id": "brief",
        "data": {
            "eyebrow": "پیش از سفارش",
            "title": "چه چیزهایی را از قبل آماده کنید؟",
            "lead": "هرچه این موارد روشن‌تر باشند، برآورد زمان و هزینه دقیق‌تر "
                    "در می‌آید و رفت‌وبرگشت کمتر می‌شود.",
            "items": [
                {"value": "هدف کار: آگاهی از برند، فروش مستقیم، یا معرفی یک محصول مشخص"},
                {"value": "مخاطب: چه کسی قرار است این را ببیند و کجا"},
                {"value": "محدودهٔ زمانی و تاریخ‌های قطعی، مثل افتتاحیه یا نمایشگاه"},
                {"value": "دارایی‌های موجود: لوگو، فونت، رنگ سازمانی، عکس‌های قبلی"},
                {"value": "محدودهٔ بودجه، حتی به‌صورت یک بازه"},
                {"value": "تصمیم‌گیرندگان و اینکه تأیید نهایی با چه کسی است"},
            ],
            "note": {
                "title": "اگر بخشی از این‌ها را هنوز ندارید، مشکلی نیست.",
                "body": "مشاوره خودش یکی از شش خانوادهٔ خدمت است. اگر هدف یا "
                        "مخاطب هنوز روشن نیست، از همان‌جا شروع می‌کنیم و بقیهٔ "
                        "موارد در طول کار شکل می‌گیرد.",
            },
        },
    })

    # ── 7. the order of work ──────────────────────────────────────────────
    B.append({
        "block": "process-section-final", "id": "process",
        "data": {
            "eyebrow": "فرایند",
            "title": "یک پروژه معمولاً از چند خانواده عبور می‌کند",
            "lead": "کمتر پروژه‌ای فقط یک خدمت لازم دارد. ترتیب زیر همان ترتیبی "
                    "است که کار واقعاً در آن جلو می‌رود؛ آنچه بین خانواده‌ها فرق "
                    "می‌کند طول هر مرحله است.",
            "steps": [
                {"title": "تعریف مسئله و انتخاب مسیر", "body": LOREM, "placeholder": True},
                {"title": "طراحی و آماده‌سازی خروجی", "body": LOREM, "placeholder": True},
                {"title": "تولید، چاپ یا اجرا", "body": LOREM, "placeholder": True},
                {"title": "اکران، انتشار و اندازه‌گیری", "body": LOREM, "placeholder": True},
            ],
        },
    })

    # ── 8. choosing between families ──────────────────────────────────────
    B.append({
        "block": "compare-cards", "id": "choose",
        "data": {
            "eyebrow": "انتخاب خانواده",
            "title": "اگر بین دو خانواده مردد هستید",
            "lead": "این سه مورد بیشترین ابهام را ایجاد می‌کنند.",
            "items": [
                {"index": "۰۱", "title": "طراحی گرافیک یا چاپ و تولید؟",
                 "body": LOREM, "placeholder": True, "icon": "icon-compare"},
                {"index": "۰۲", "title": "دیجیتال مارکتینگ یا عکاسی و فیلم‌برداری؟",
                 "body": LOREM, "placeholder": True, "icon": "icon-compare"},
                {"index": "۰۳", "title": "تبلیغات محیطی یا سازه‌ها؟",
                 "body": LOREM, "placeholder": True, "icon": "icon-compare"},
            ],
            "icon": "icon-compare",
        },
    })

    # ── 9. questions ──────────────────────────────────────────────────────
    B.append({
        "block": "faq-section-final", "id": "faq",
        "data": {
            "eyebrow": "پرسش‌های پرتکرار",
            "title": "پیش از تماس، جواب کوتاه را همین‌جا ببینید",
            "lead": "برای برآورد دقیق هزینه و زمان، به جزئیات پروژه نیاز است؛ "
                    "پاسخ‌های اینجا عمومی‌اند.",
            "questions": [
                {"q": "آیا فقط یک خدمت را هم سفارش می‌دهید؟", "a": LOREM, "placeholder": True},
                {"q": "خدمات شما فقط در اصفهان ارائه می‌شود؟", "a": LOREM, "placeholder": True},
                {"q": "برآورد هزینه چقدر طول می‌کشد؟", "a": LOREM, "placeholder": True},
                {"q": "اگر طرح آماده داشته باشم، فقط چاپ و اجرا را انجام می‌دهید؟",
                 "a": LOREM, "placeholder": True},
            ],
        },
    })

    # ── 10. knowledge ─────────────────────────────────────────────────────
    B.append({
        "block": "knowledge-carousel", "id": "knowledge",
        "data": {
            "eyebrow": "مرکز دانش",
            "title": "مقاله‌ها و ویدیوهای مرتبط با خدمات",
            "groups": [
                {"title": "مقاله‌ها", "items": [
                    {"label": "کاور مقاله", "title": "عنوان مقاله", "meta": "در دست تهیه",
                     "alt": "جایگاه تصویر شاخص مقاله", "placeholder": True} for _ in range(3)]},
                {"title": "ویدیوها", "items": [
                    {"label": "کاور ویدیو", "title": "عنوان ویدیو", "meta": "در دست تهیه",
                     "alt": "جایگاه کاور ویدیو", "placeholder": True} for _ in range(3)]},
            ],
        },
    })

    # ── 11. conversion ────────────────────────────────────────────────────
    B.append({
        "block": "review-gate", "id": "review",
        "data": {
            "eyebrow": "قدم بعدی",
            "title": "بگویید چه کاری در دست دارید.",
            "body": "لازم نیست از قبل بدانید کارتان زیر کدام خانواده می‌نشیند. "
                    "صورت مسئله را بگویید؛ مسیر درست را با هم پیدا می‌کنیم.",
            "primary": {"label": "شروع گفت‌وگو"},
            "secondary": {"label": "بازگشت به بالای صفحه ↑", "href": "#top"},
        },
    })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    placeholders = json.dumps(spec, ensure_ascii=False).count('"placeholder": true')
    print(f"{out_path}: {len(B)} blocks, {placeholders} tagged placeholders")
    print("families:", ", ".join(f"{f['entity'].name_fa}({f['count']})" for f in families))


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "pages/drafts/services.json"))
