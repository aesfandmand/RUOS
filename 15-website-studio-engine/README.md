# RUOS Website Studio Engine

این پوشه نخستین موتور اجرایی واقعی RUOS برای تولید صفحه است؛ نه Registry و نه سند مفهومی.

## فرمان اجرا

```bash
python3 15-website-studio-engine/ruos_build.py \
  --spec 15-website-studio-engine/examples/structures.json \
  --out dist/structures
```

خروجی:

- `index.html`
- `assets/styles.css`
- `assets/runtime.js`
- `schema.jsonld`
- `qc-report.json`

## Pipeline اجرایی

1. خواندن Page Spec
2. اعتبارسنجی ورودی‌های اجباری
3. اعمال Visual DNA
4. انتخاب الگوهای روایت، خوانش، تعامل و تبدیل
5. ساخت HTML معنایی
6. ساخت CSS responsive
7. ساخت JavaScript تعامل و Motion
8. ساخت Schema.org
9. اجرای ۱۰ Creative/Business Gate
10. توقف Build در صورت رد شدن Gate سخت

## نکته مهم

این موتور عمداً هیچ ادعایی درباره استفاده از v16 نمی‌کند مگر اینکه `visual_dna.source` در Spec به فایل واقعی v16 اشاره کند. نبود این منبع باعث ثبت خطای Gate می‌شود.

## وضعیت

- executable: yes
- deterministic build: yes
- one-command output: yes
- creative quality: rule-driven, not guaranteed
- v16 fidelity: only when actual v16 source is supplied
