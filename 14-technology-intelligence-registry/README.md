# Technology Intelligence Registry (TIR)

Status: active-draft
Version: 0.1.0
Project: RUOS / Red Umbrella
Last verified: 2026-08-05

## Mission

TIR یک فهرست ساده از ابزارها نیست. این Registry باید برای هر مأموریت وب، مناسب‌ترین ترکیب فناوری، Skill، Plugin، GPT، Agent و سرویس را با توجه به کیفیت، هزینه، مالکیت، قابلیت نگهداری، دسترس‌پذیری، سازگاری با فارسی و مسیر تبدیل پیشنهاد کند.

## Core rule

ابزار نباید زبان بصری یا معماری صفحه را تحمیل کند. ابزار فقط باید قابلیت، تعامل، دسترس‌پذیری، سرعت و قابلیت نگهداری را تقویت کند.

## Scope

- UI components and design systems
- Motion and interaction
- Frontend and runtime
- WordPress
- SEO and AI SEO
- Research and content intelligence
- Skills, GPTs, agents and MCP
- Testing, performance and accessibility
- Analytics, conversion and experimentation
- Deployment and automation

## Record model

هر رکورد حداقل شامل این موارد است:

- identity and category
- official sources
- license and cost model
- supported runtimes
- documented strengths
- RUOS assessment
- approved roles
- prohibited roles
- risks and validation needs
- last verification date

## Selection principle for Red Umbrella

برای وب‌سایت چتر قرمز، پیش‌فرض تولید همچنان HTML معنایی، CSS اختصاصی، JavaScript حداقلی و WordPress-ready است. کتابخانه‌های React یا Vue فقط زمانی وارد Runtime می‌شوند که ارزش روشن و قابل سنجش ایجاد کنند. در غیر این صورت از آن‌ها برای الگوهای تعامل، دسترس‌پذیری و معماری Component استفاده می‌شود، نه برای تحمیل ظاهر آماده.

## Hard gates

1. هیچ کتابخانه‌ای مجاز نیست صفحه را به مجموعه‌ای از کارت‌های تکراری تبدیل کند.
2. Component library جای Design Direction، Art Direction، Storytelling و Conversion Architecture را نمی‌گیرد.
3. وابستگی Runtime باید توجیه عملکردی داشته باشد.
4. RTL، فارسی، Mobile Safari، Keyboard و Reduced Motion باید پیش از پذیرش نهایی آزمایش شوند.
5. اطلاعات License، Cost و Maintenance باید از منبع رسمی و با تاریخ بررسی ثبت شود.
6. هر ابزار باید امکان جایگزینی داشته باشد و نباید RUOS را به Vendor خاص قفل کند.

## Initial registry

اولین Registry روی UI Components و Design Systems متمرکز است. خروجی آن ابزارها را به چهار نقش تقسیم می‌کند:

- preferred foundation
- conditional runtime
- reference and governance
- not-default for marketing websites

## Directory

- `schemas/` — قرارداد رکورد ابزار
- `registries/` — فهرست‌های نسخه‌بندی‌شده
- `policies/` — قوانین انتخاب و استفاده
- `profiles/` — ترکیب فناوری برای پروژه‌ها
- `sources/` — منابع رسمی و تاریخ راستی‌آزمایی
