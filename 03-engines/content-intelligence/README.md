# RUOS Content Intelligence Engine

موتور چندپروژه‌ای تحقیق، امتیازدهی، استخراج الگو، طراحی استراتژی و تقویم محتوای آژانس چتر قرمز.

## هدف

این موتور «ایده‌پرداز پست» نیست. هدف آن تبدیل دادهٔ واقعی بازار و عملکرد محتوا به تصمیم قابل‌تکرار است:

`Demand → Winning Content → Pattern Mining → Opportunity Score → Strategy → 30-day Rolling Calendar → Measurement → 45-day Strategic Review`

## اصول قفل‌شدهٔ v0.1

1. **Multi-project by design** — منطق موتور مشترک است؛ هر برند فقط پروفایل و وزن منابع خودش را دارد.
2. **Evidence before ideas** — ایده بدون شاهد از جست‌وجو، رفتار مخاطب، دادهٔ رقبا یا دادهٔ خود برند وارد تقویم نمی‌شود.
3. **Owned ≠ Competitive** — Insight خصوصی حساب‌های متصل هرگز با دادهٔ عمومی رقبا مخلوط نمی‌شود.
4. **Outlier over raw views** — نسبت عملکرد محتوا به baseline همان حساب مهم‌تر از عدد خام بازدید است.
5. **Search + Social + Voice of Customer** — گوگل، شبکه‌های اجتماعی و زبان واقعی مشتری هم‌زمان دیده می‌شوند.
6. **Reddit = pain/language miner** — برای کشف درد، سؤال، اعتراض و زبان طبیعی؛ نه نمایندهٔ مستقیم بازار ایران.
7. **30-day rolling execution / 45-day strategy** — تقویم اجرایی ۳۰روزه است؛ بازبینی راهبردی در روز ۴۵ انجام می‌شود.
8. **Free-first architecture** — نسخهٔ اول بدون وابستگی اجباری به سرویس پولی طراحی می‌شود.
9. **Human approval gate** — هیچ پیشنهاد استراتژیک یا تقویم نهایی بدون تأیید انسانی «publish-ready» نیست.

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

## وضعیت v0.1

در این نسخه، هستهٔ امتیازدهی و Outlier Detection پیاده‌سازی شده و قرارداد منابع، چرخهٔ تحقیق و پروفایل پروژهٔ Red Umbrella تعریف شده است. اتصال مستقیم APIها و دیتابیس در فاز بعدی انجام می‌شود.
