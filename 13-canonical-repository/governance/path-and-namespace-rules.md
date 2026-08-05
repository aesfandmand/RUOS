# Path and Namespace Rules v0.1

وضعیت: `implemented-draft`

## 1. هدف

این سند قواعد نام‌گذاری، مسیرگذاری، ارث‌بری، مرجع‌دهی و مهاجرت اشیای RUOS را تعیین می‌کند.

## 2. قرارداد نام فایل

نام فایل باید:

- با حروف کوچک لاتین باشد.
- از `kebab-case` استفاده کند.
- نوع شیء را از مسیر بگیرد، نه از تکرار بی‌دلیل در نام.
- نسخه را فقط هنگامی در نام داشته باشد که فایل خودش specification یا schema نسخه‌دار است.
- از فاصله، حروف مبهم و نام‌های موقت مانند `final-final-2` استفاده نکند.

نمونه درست:

```text
04-entities/structures/unipole.yaml
08-pages/red-umbrella/structures-hub.yaml
12-gcera-dsl/schemas/gcera-dsl-v0.1.schema.json
```

نمونه نادرست:

```text
Unipole Final New.yaml
structure-unipole-v7-last.yaml
صفحه نهایی ۲.yaml
```

## 3. قرارداد UID

فرمت پایه:

```text
ruos:{namespace}:{scope}:{kind}:{name}
```

نمونه‌ها:

```text
ruos:project:red-umbrella:page:structures-hub
ruos:project:red-umbrella:entity:structure:unipole
ruos:project:red-umbrella:decision:structure-master-mission
ruos:global:capability:semantic-content-architecture
```

قواعد:

1. UID پس از انتشار تغییر نمی‌کند.
2. تغییر نام نمایشی نباید UID را تغییر دهد.
3. تغییر معنای بنیادی، شیء تازه و UID تازه می‌سازد.
4. شیء منسوخ باید با رابطه `superseded_by` به جایگزین متصل شود.
5. UID در همه کانال‌ها یکسان می‌ماند.

## 4. اولویت فضای نام

```text
global → industry → project → brand → implementation
```

- `global`: قاعده یا دارایی قابل استفاده در همه پروژه‌ها
- `industry`: دانش مشترک یک حوزه
- `project`: تصمیم و داده اختصاصی پروژه
- `brand`: هویت، صدا، طراحی و استثنای برند
- `implementation`: نگاشت به WordPress، GitHub، Figma یا فناوری دیگر

فضای نام پایین‌تر می‌تواند مورد بالاتر را توسعه دهد، اما حق بازنویسی خاموش ندارد.

## 5. Override و Exception

هر Override باید شامل موارد زیر باشد:

```yaml
override:
  parent_uid: ruos:global:rule:example
  decision_uid: ruos:project:red-umbrella:decision:example-exception
  reason: "دلیل کسب‌وکاری یا معماری"
  status: approved
  approved_by: human
```

بدون Decision Reference، Override نامعتبر است.

## 6. قواعد منبع حقیقت

برای پروژه چتر قرمز:

1. تصمیم جدید و صریح کارفرما
2. اسناد LOCKED متأخر
3. فهرست زنده تغییرات
4. معماری و مدل داده تأییدشده
5. نسخه‌های طراحی تأییدشده
6. فایل‌های کاری و پیش‌نویس‌ها

وجود فایل جدیدتر از نظر تاریخ، به‌تنهایی به معنای معتبرتر بودن محتوای آن نیست.

## 7. قواعد وضعیت

- `draft`: پیش‌نویس آزاد
- `candidate`: نامزد ورود به سیستم
- `pending`: نیازمند داده یا تأیید
- `review`: در حال بازبینی
- `approved`: تأییدشده برای دامنه مشخص
- `canonical`: منبع مرجع فعال
- `published`: منتشرشده در کانال
- `superseded`: جایگزین‌شده با حفظ تاریخچه
- `deprecated`: قابل استفاده برای تاریخچه، نه تولید جدید
- `archived`: خارج از چرخه فعال

فقط `approved`، `canonical` و `published` وارد تولید رسمی می‌شوند.

## 8. منع کپی حقیقت

Viewها و صفحات مجازند:

- UID را مرجع دهند.
- بخشی از داده را انتخاب کنند.
- داده را بر اساس پرسونا و نیت مرتب کنند.
- CTA و روایت متفاوت داشته باشند.

Viewها مجاز نیستند:

- مشخصات فنی را مستقل از Entity بازنویسی کنند.
- FAQ مرجع را بدون رابطه و منشأ کپی کنند.
- رکورد متناقض برای همان موجودیت بسازند.
- داده `pending` را فکت قطعی نمایش دهند.

## 9. قواعد پروژه چتر قرمز

### صفحه Structure

- UID: `ruos:project:red-umbrella:page:structures-hub`
- نقش: مرجع مادر و منبع داده سازه‌ها
- نقش‌های ممنوع: صفحه فروش، صفحه سرمایه‌گذاری، صفحه اجاره
- مسیرهای خروجی: خرید ایندور، خرید اوتدور، سرمایه‌گذاری، اجاره و کمپین، فروش سازمانی
- baseline طراحی: Structure v16 تا ثبت جایگزین تأییدشده

### موجودیت Structure

هر سازه یک رکورد مرجع دارد و صفحات دیگر فقط View متناسب می‌سازند.

### زبان

- فارسی زبان مبناست.
- نسخه انگلیسی، عربی و کوردی بعد از تأیید نسخه فارسی ساخته می‌شوند.
- ترجمه نباید جایگزین رکورد فارسی تأییدنشده شود.

## 10. قواعد مسیر پروژه

ساختار پیشنهادی هر پروژه:

```text
03-projects/{project}/
├── project.repository.yaml
├── project.sources.yaml
├── project.rules.yaml
├── project.decisions.yaml
├── project.routes.yaml
├── project.languages.yaml
├── brand/
├── mappings/
├── memory/
└── overrides/
```

## 11. قواعد کنترل کیفیت

اعتبارسنجی باید خطا بدهد اگر:

- UID تکراری باشد.
- Reference الزامی حل نشود.
- فیلد اجباری وجود نداشته باشد.
- شیء pending وارد production شود.
- canonical بدون Decision جایگزین شود.
- صفحه بدون Intent یا Persona تعریف شود.

اعتبارسنجی باید هشدار بدهد اگر:

- صفحه Knowledge Graph Scope ندارد.
- صفحه Capability Layer ندارد.
- صفحه orphan است.
- منبع یا مالک مشخص نیست.
- Evidence برای ادعای حساس وجود ندارد.

## 12. مهاجرت

مهاجرت فایل‌های موجود باید به‌ترتیب زیر باشد:

```text
Inventory → Classification → UID Assignment → Mapping → Validation → Approval → Move → Redirect/Reference → Audit
```

هیچ فایل موجودی صرفاً برای مرتب‌سازی حذف یا جابه‌جا نمی‌شود؛ ابتدا نگاشت و وابستگی آن ثبت می‌شود.
