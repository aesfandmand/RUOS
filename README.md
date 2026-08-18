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
- Content Intelligence Engine v0.2 — هستهٔ چندپروژه‌ای امتیازدهی فرصت، Outlier Detection، Snapshot policy، دیتابیس زندهٔ Supabase و کانکتور read-only برای Instagram Owned Insights (`03-engines/content-intelligence/`, `src/ruos/content_intelligence*.py`)
- Multi-project workspaces، Persian-first localization

## وضعیت اتصال داده

- PostgreSQL/Supabase: دیتابیس واقعی روی پروژهٔ `umbrella social` provision شده، Schema و migrationهای امنیت/کارایی اعمال شده و پروژهٔ `red-umbrella` seed شده است.
- Instagram Owned Insights: کد و Runner آماده است، اما Meta App/OAuth، Token واقعی، Professional User ID و Read-only test حساب Red Umbrella هنوز انجام نشده است.

هنوز پیاده‌سازی/فعال‌سازی کامل نشده: Meta OAuth زنده برای Instagram Owned Insights، Search Intelligence خودکار، Capability Engine مستقل، ابزار `10-tools/validate_repository.py`. تا اتصال و تست واقعی Meta، Instagram را «connected» معرفی نکنید.

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
