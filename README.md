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
- Multi-project workspaces، Persian-first localization

هنوز پیاده‌سازی نشده (فقط در نسخه‌های قبلی به‌عنوان هدف ذکر شده بودند): Instagram Engine، Capability Engine مستقل، Search Intelligence، ابزار `10-tools/validate_repository.py`. تا پیاده‌سازی واقعی، این‌ها را به‌عنوان دامنهٔ فعلی معرفی نکنید.

## اجرای اعتبارسنجی

اعتبارسنجی واقعی فعلی، مجموعه‌تست پکیج پایتون `ruos` است:

```bash
pip install -e .
pip install pytest
python3 -m pytest tests/ -q
```

برای Build واقعی یک صفحه:

```bash
ruos build structures --spec-root pages --output dist
```
