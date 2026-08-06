# RUOS Website Studio Engine

این پوشه نخستین موتور اجرایی واقعی RUOS برای تولید صفحه است؛ نه Registry و نه سند مفهومی.

## فرمان اجرا

موتور واقعی از طریق پکیج نصب‌شدهٔ `ruos` اجرا می‌شود (نگاه کنید به `pyproject.toml` و `src/ruos/`)، نه یک اسکریپت مجزا در این پوشه:

```bash
pip install -e .
ruos build structures --spec-root pages --output dist
```

`structures` نام Slug است؛ فایل متناظرش باید در `pages/structures.json` وجود داشته باشد (نمونهٔ فعلی همین مخزن).

خروجی در `dist/structures/`:

- `index.html`
- `assets/styles.css`
- `assets/runtime.js`
- `assets/motion-manifest.json`
- `assets/creative-intelligence.json`
- `agency-quality-report.json`
- `build-manifest.json`
- `qa-report.json`

## Pipeline اجرایی (`src/ruos/compiler.py`)

1. خواندن و اعتبارسنجی Page Spec (`spec_loader.py`)
2. اعمال Visual DNA (`visual_dna.py`)
3. ساخت محتوای معنایی صفحه (`content_composer.py`)
4. ساخت لایهٔ Creative Intelligence: کوئری، فروش، معنایی، خلاقانه (`creative_intelligence.py`)
5. تفکیک کامپوننت هر بخش (`component_resolver.py`)
6. تعیین الگوی روایت/اسکرول هر بخش (`pattern_resolver.py`)
7. ساخت برنامهٔ موشن هماهنگ با الگوها (`motion_composer.py`)
8. رندر HTML/CSS/JS (`render.py`)
9. ارتقای معنایی: H1، Schema Graph (`semantic_enhancer.py`)
10. اجرای ۱۰ Gate کیفی (`qa.py`) و امتیازدهی آژانسی با آستانهٔ انتشار ۸۸ (`quality_score.py`)
11. توقف Build در صورت رد شدن هر Gate یا پایین‌تر بودن امتیاز از آستانه

## نکتهٔ مهم دربارهٔ Visual DNA

فعلاً `PageSpec` هیچ فیلد `visual_dna.source` ندارد؛ `visual_profile` فقط یک شناسهٔ رشته‌ای است که در `src/ruos/visual_dna.py` به یک دیکشنری از‌پیش‌نوشته‌شده (مثلاً `red-umbrella-v16`) نگاشت می‌شود. یعنی صحت توکن‌های آن پروفایل (رنگ، تایپوگرافی، ریتم) در حال حاضر مسئولیت کسی است که آن را دستی در `visual_dna.py` می‌نویسد و تأیید می‌کند — موتور هیچ مکانیزمی برای ردیابی خودکار به یک فایل مرجع واقعی ندارد. اگر ردیابی خودکار لازم شود، باید فیلد `source` و منطق استخراج، به‌صورت جدید طراحی و اضافه شود.

## وضعیت

- executable: yes
- deterministic build: yes
- one-command output: yes
- creative quality: rule-driven QA gates + weighted agency-quality score (threshold 88); not a substitute for human creative review
- visual DNA provenance: manually authored per profile in `visual_dna.py`; no automated source-file tracing yet
