# RUOS Content Intelligence Engine

موتور چندپروژه‌ای تحقیق، امتیازدهی، استخراج الگو، طراحی استراتژی و تقویم محتوای آژانس چتر قرمز.

## هدف

این موتور «ایده‌پرداز پست» نیست. هدف آن تبدیل دادهٔ واقعی بازار و عملکرد محتوا به تصمیم قابل‌تکرار است:

`Demand → Winning Content → Pattern Mining → Opportunity Score → Strategy → 30-day Rolling Calendar → Measurement → 45-day Strategic Review`

## اصول قفل‌شده

1. **Multi-project by design** — منطق موتور مشترک است؛ هر برند فقط پروفایل و وزن منابع خودش را دارد.
2. **Evidence before ideas** — ایده بدون شاهد از جست‌وجو، رفتار مخاطب، دادهٔ رقبا یا دادهٔ خود برند وارد تقویم نمی‌شود.
3. **Owned ≠ Competitive** — Insight خصوصی حساب‌های متصل هرگز با دادهٔ عمومی رقبا مخلوط نمی‌شود.
4. **Outlier over raw views** — نسبت عملکرد محتوا به baseline همان حساب مهم‌تر از عدد خام بازدید است.
5. **Same-age baseline** — عملکرد 6h فقط با 6h مقایسه می‌شود؛ 24h با 24h و همین‌طور ادامه.
6. **No stale backfill** — اگر checkpoint زمانی از دست رفت، عدد امروز به‌جای snapshot تاریخی ثبت نمی‌شود.
7. **Search + Social + Voice of Customer** — گوگل، شبکه‌های اجتماعی و زبان واقعی مشتری هم‌زمان دیده می‌شوند.
8. **Reddit = pain/language miner** — برای کشف درد، سؤال، اعتراض و زبان طبیعی؛ نه نمایندهٔ مستقیم بازار ایران.
9. **30-day rolling execution / 45-day strategy** — تقویم اجرایی ۳۰روزه است؛ بازبینی راهبردی در روز ۴۵ انجام می‌شود.
10. **Free-first architecture** — نسخهٔ اول بدون وابستگی اجباری به سرویس پولی طراحی می‌شود.
11. **Human approval gate** — هیچ پیشنهاد استراتژیک یا تقویم نهایی بدون تأیید انسانی «publish-ready» نیست.

## منابع نسخهٔ اول

- Google Search / SERP
- Google Trends
- Instagram (Owned Insights + public competitive research)
- YouTube / Shorts
- Reddit (web research by default)
- TikTok Creative Center
- Competitor websites / comments / Q&A
- First-party customer data: DM, comments, calls, consultations, sales objections

## خروجی‌های استاندارد

- `research_dataset`
- `winning_content_map`
- `pain_question_objection_map`
- `pattern_library`
- `opportunity_backlog`
- `content_strategy`
- `30_day_rolling_calendar`
- `day_15_mini_review`
- `day_30_performance_review`
- `day_45_strategic_review`

## وضعیت v0.2

پیاده‌سازی‌شده:

- Opportunity Score و Outlier Detection
- Snapshot checkpoints: 1h / 6h / 24h / 72h / 7d / 30d
- نرخ‌های Save / Share / Interaction بر مبنای Reach
- Instagram Owned Insights read-only connector روی `graph.instagram.com`
- resilient metric collection برای Metricهای ناسازگار با نوع Media
- PostgreSQL/Supabase schema و storage adapter
- Supabase live database برای موتور روی پروژهٔ `umbrella social` (`esobizhvqnvmhafqhlpc`)
- RLS فعال روی تمام جدول‌های `ci_*` بدون public policy؛ دسترسی عمومی API عمداً بسته است
- unique snapshot/source guards و foreign-key indexes
- پروژهٔ `red-umbrella` در دیتابیس seed شده است
- CLI اجرای sync: `ruos-content-sync`
- تست‌های واحد برای scoring، Instagram normalization، snapshot policy و sync orchestration

هنوز برای اتصال زنده Instagram لازم است:

- Meta App با Business Login for Instagram
- OAuth واقعی حساب Professional چتر قرمز
- Access Token و Instagram Professional User ID واقعی
- تعیین نسخهٔ فعال Graph API در زمان راه‌اندازی
- انتقال `CI_DATABASE_URL` و Credentialهای Meta به Secret Store / GitHub Actions Secrets
- اجرای Read-only live test روی حساب Red Umbrella
- بررسی Metric availability واقعی Mediaهای حساب
- Runner زمان‌بندی‌شده بعد از موفقیت تست زنده

قاعدهٔ گزارش وضعیت: دیتابیس اکنون زنده است؛ اما تا Read-only test واقعی Meta موفق نشده، سیستم را «Instagram connected» معرفی نکنید. عبارت صحیح فعلی:

`Content Intelligence database live; Instagram Owned Insights connector implemented; Meta authorization pending.`

راهنمای اتصال: `instagram-owned-insights.md`

## Database migrations

- Base schema: `postgres-schema.sql`
- Security/idempotency hardening: `migrations/002_hardening.sql`
- Foreign-key indexes: `migrations/003_fk_indexes.sql`
