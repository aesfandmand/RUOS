# Instagram Owned Insights — Connection Contract

وضعیت: **connector implemented / live account not connected yet**

این لایه فقط برای حساب حرفه‌ای Instagram از نوع Business یا Creator است و دادهٔ خصوصی همان حساب را در کلاس `owned` نگه می‌دارد. دادهٔ عمومی رقبا هرگز در این مسیر وارد نمی‌شود.

## مبنای رسمی

- Instagram Insights برای حساب‌های Business و Creator در دسترس است.
- مسیر Instagram API with Instagram Login از Business Login for Instagram استفاده می‌کند.
- Host این مسیر `graph.instagram.com` است.
- مجوزهای پایهٔ خواندن Insight در این مسیر:
  - `instagram_business_basic`
  - `instagram_business_manage_insights`
- برای حساب‌هایی که خود App آن‌ها را مالک/مدیریت می‌کند Standard Access کافی است؛ اگر محصول بعداً حساب‌های حرفه‌ای دیگر مشتریان را در مقیاس سرویس‌دهی کند، فرایند Advanced Access و الزامات Meta باید جداگانه طی شود.
- بعضی Metricها به نوع Media، اندازه حساب و سیاست جاری Meta وابسته‌اند؛ connector به‌همین دلیل Metric نامعتبر را ثبت می‌کند ولی Snapshot کامل را از بین نمی‌برد.

مراجع:
- https://www.facebook.com/help/instagram/788388387972460
- https://www.facebook.com/help/instagram/138925576505882
- https://www.postman.com/meta/instagram/folder/23987686-f659d7d1-d74c-44e4-9192-9b1e8694c511

## اصل امنیتی

**هیچ Access Token، App Secret، Database password یا OAuth secret در Git ذخیره نمی‌شود.**

متغیرهای Runtime:

```text
CI_DATABASE_URL
CI_INSTAGRAM_ACCESS_TOKEN
CI_INSTAGRAM_USER_ID
CI_META_GRAPH_API_VERSION
CI_INSTAGRAM_ACCOUNT_KEY
CI_PROJECT_ID
CI_PROJECT_NAME
```

`CI_META_GRAPH_API_VERSION` عمداً hard-code نشده است؛ هنگام راه‌اندازی App باید نسخهٔ فعال و پشتیبانی‌شدهٔ Meta ثبت شود.

## دیتابیس

Schema اولیه:

```text
03-engines/content-intelligence/postgres-schema.sql
```

برای persistence:

```bash
pip install -e '.[content-intel]'
```

و سپس Schema روی PostgreSQL/Supabase اعمال شود.

## اجرای یک Sync

بعد از تنظیم Secretها و Schema:

```bash
ruos-content-sync
```

Runner این کارها را انجام می‌دهد:

1. Media حساب متصل را می‌خواند.
2. Media را در `ci_content_items` upsert می‌کند.
3. فقط اگر یکی از checkpointهای 1h / 6h / 24h / 72h / 7d / 30d واقعاً در بازهٔ ثبت باشد Insight می‌خواند.
4. Snapshot تاریخیِ ازدست‌رفته را با عدد امروز جعل نمی‌کند.
5. Save/Share/Interaction Rate را نسبت به Reach محاسبه می‌کند.
6. Views را فقط با Snapshot هم‌سن محتوای قبلی مقایسه می‌کند؛ مثلاً 6h با 6h، نه 6h با 30d.
7. Outlier Ratio را نسبت به median حداکثر 20 محتوای اخیر محاسبه می‌کند.
8. خطای Metricهای پشتیبانی‌نشده را در metadata همان Snapshot ثبت می‌کند.

## هنوز برای اتصال زنده لازم است

- ساخت یا انتخاب Meta App مناسب
- فعال‌سازی Business Login for Instagram
- تنظیم Redirect URI/OAuth
- گرفتن User ID و Access Token مجاز
- تعیین Graph API Version فعال
- ساخت Supabase/PostgreSQL instance و اجرای Schema
- انتقال Secretها به Secret Store / GitHub Actions Secrets
- تست Read-only روی حساب Red Umbrella
- سپس فعال‌سازی Runner زمان‌بندی‌شده

تا این موارد انجام نشده، عبارت درست برای وضعیت سیستم این است:

> Instagram Owned Insights connector implemented; live Red Umbrella connection pending credentials and Meta app setup.
