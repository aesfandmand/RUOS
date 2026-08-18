# RUOS Repository v2.0

مخزن پایدار و نسخه‌بندی‌شدهٔ Red Umbrella Operating System.

## منبع حقیقت

این مخزن منبع اصلی است. فایل‌های ZIP فقط Snapshot هستند.

## دامنهٔ فعلی (پیاده‌سازی‌شده)

- Website Studio Engine — موتور اجرایی تولید صفحه (`src/ruos/`, `15-website-studio-engine/`)
- Reasoning / API / Audit / Migration Engines — تعریف‌شده به‌صورت قرارداد YAML (`03-engines/`)
- Knowledge Migration — دانش پروژهٔ چتر قرمز (`02-knowledge/`, `11-knowledge-migration/`, `11-projects/`)
- GCERA-DSL — مدل Entity/Journey/Page (`12-gcera-dsl/`)
- Canonical Repository Specification — قرارداد مسیرگذاری و UID (`13-canonical-repository/`)
- Technology Intelligence Registry — رجیستری دستیِ ارزیابی کتابخانه‌ها (`14-technology-intelligence-registry/`)
- Content Intelligence Engine v0.2 — هستهٔ امتیازدهی، Outlier Detection، Snapshot policy، Instagram Owned Insights connector و PostgreSQL storage adapter (`03-engines/content-intelligence/`, `src/ruos/content_intelligence*.py`)
- Multi-project workspaces، Persian-first localization

## پیاده‌سازی شده ولی هنوز زنده متصل نشده

- Instagram Owned Insights connector: کد و Runner آماده است، اما Meta App/OAuth، Token واقعی، User ID واقعی و Read-only test حساب Red Umbrella هنوز انجام نشده.
- PostgreSQL/Supabase adapter: کد و Schema آماده است، اما instance واقعی و Secretها هنوز provision نشده‌اند.

هنوز پیاده‌سازی نشده: Search Intelligence خودکار، Capability Engine مستقل، ابزار `10-tools/validate_repository.py`. تا پیاده‌سازی واقعی، این‌ها را به‌عنوان دامنهٔ فعلی معرفی نکنید.

## اجرای اعتبارسنجی

اعتبارسنجی واقعی فعلی، مجموعه‌تست پکیج پایتون `ruos` است:

```bash
pip install -e .
pip install pytest
python3 -m pytest tests/ -q
```

برای لایهٔ Persistence موتور محتوا:

```bash
pip install -e '.[content-intel]'
```

برای Build واقعی یک صفحه:

```bash
ruos build structures --spec-root pages --output dist
```
