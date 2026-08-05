# Professional Web Experience Policy v0.1

Status: active-draft
Project scope: Red Umbrella public website and future client websites

## Objective

خروجی RUOS باید در سطح یک وب‌سایت حرفه‌ای، متمایز، تعاملی، قابل اعتماد و تبدیل‌محور باشد؛ نه چیدمان تکراری کامپوننت‌ها یا مجموعه‌ای از کارت‌ها.

## 1. Design direction before components

پیش از انتخاب Component Library باید این موارد تعیین شوند:

- نیت ورود و کوئری اصلی
- پرسونا و مرحله سفر
- مسئله تجاری و تبدیل مطلوب
- روایت صفحه
- Art Direction
- ریتم دیداری و سلسله‌مراتب
- تعامل‌های ضروری
- رسانه، تصویر، ویدئو و موشن
- سناریوی موبایل و دسکتاپ

Componentها بعد از این مرحله انتخاب می‌شوند.

## 2. Anti-card rule

کارت یک الگوی نمایش است، نه معماری صفحه.

Hard gateها:

- دو بخش کارت‌محور مشابه نباید پشت سر هم قرار بگیرند.
- Grid کارت نباید جای روایت، مقایسه، شواهد، نمونه‌کار یا تصمیم‌سازی را بگیرد.
- هر Card Group باید دلیل روشن داشته باشد: مقایسه، انتخاب، دسته‌بندی یا اسکن سریع.
- ظاهر Default کتابخانه‌ها ممنوع است.
- در صفحات بلند باید چند الگوی Composition حضور داشته باشد؛ مانند Editorial Section، Full-bleed Media، Sticky Narrative، Timeline، Comparison، Interactive Explorer، Gallery، Map، Data View و Scrollytelling.

## 3. Preferred production stack

برای وب‌سایت‌های عمومی و WordPress-ready:

1. Semantic HTML
2. CSS Custom Properties و Design Tokens اختصاصی
3. CSS Grid و Container Queries در صورت پشتیبانی هدف
4. JavaScript حداقلی و ماژولار
5. Progressive Enhancement
6. Componentهای اختصاصی با API روشن
7. Library فقط برای مسئله‌ای که ساخت امن آن پرریسک یا پرهزینه است

## 4. Library roles

- Interaction primitives: رفتار، Keyboard، Focus، Dialog، Menu، Tabs، Tooltip
- Design-system references: Governance، Token، Documentation و Quality Gates
- App libraries: پنل‌ها، داشبوردها و ابزارهای داخلی
- Source-owned libraries: شتاب‌دهنده توسعه با بازطراحی کامل

هیچ Library نقش Brand Direction یا Page Composition را ندارد.

## 5. Conversion requirements

هر صفحه باید:

- در چند ثانیه اول تطابق با نیت کاربر را روشن کند.
- مشتری را قهرمان و برند را راهنما نگه دارد.
- مسیر بعدی را بدون بن‌بست ارائه کند.
- CTA را بر اساس مرحله سفر انتخاب کند، نه تکرار یک دکمه ثابت.
- اعتراض‌ها، ریسک‌ها و پرسش‌های تصمیم را پاسخ دهد.
- شواهد، نمونه‌کار، فرایند یا Capability مرتبط ارائه کند.
- تماس تلفنی را برای مخاطبان سازمانی و ایرانی ساده نگه دارد.

## 6. Iranian Persian content gate

محتوا باید:

- فارسی طبیعی، روان و غیرترجمه‌ای باشد.
- با کوئری، پرسونا و زبان واقعی مخاطب ایرانی تطابق داشته باشد.
- اصطلاحات فنی را در صورت نیاز توضیح دهد.
- از ادعا، عدد و فکت تأییدنشده دوری کند.
- برای Google و موتورهای AI ساختارپذیر باشد.
- خلاصه، هدینگ روشن، پاسخ مستقیم، FAQ و روابط انتیتی داشته باشد.
- پس از تأیید نهایی چتر قرمز Canonical شود.

## 7. Interaction and motion gate

تعامل یا موشن فقط زمانی مجاز است که یکی از این کارها را انجام دهد:

- جهت‌یابی
- نشان دادن پیشرفت
- توضیح رابطه یا تغییر
- افزایش درک سازه یا فرایند
- کمک به مقایسه و انتخاب
- ایجاد Feedback
- تقویت روایت بدون کاهش خوانایی

موشن تزئینی، سنگین یا مختل‌کننده تبدیل رد می‌شود. Reduced Motion و Mobile Safari اجباری‌اند.

## 8. Acceptance gates

پیش از Production:

- Desktop و Mobile در یک Codebase واقعی QC شوند.
- RTL و فارسی روی Safari و iOS بررسی شوند.
- Keyboard و Focus کامل باشند.
- HTML معنایی و Schema معتبر باشند.
- Core Web Vitals و حجم وابستگی بررسی شوند.
- هیچ فکت ساختگی، لینک مرده یا CTA بی‌مسیر وجود نداشته باشد.
- صفحه از نظر Business، UX، UI، Content، SEO، AI SEO و Accessibility امضا شود.

## 9. Current Red Umbrella decision

برای `/structures` و دیگر صفحات عمومی، Runtime React پیش‌فرض نیست. Interaction Patternها از منابع برتر استخراج می‌شوند، اما خروجی اولیه باید HTML/CSS/JS اختصاصی، Responsive و WordPress-ready باقی بماند. این تصمیم فقط با اثبات ارزش تجاری یا فنی قابل تغییر است.
