# Instagram High-Performance Discovery Policy v0.3

## اصل قفل‌شده
برای پروژه‌های آژانس، به‌ویژه Red Umbrella، کشف دسته‌ای محتوای اینستاگرامی با عملکرد بالا یک منبع فرعی نیست؛ یکی از ورودی‌های اصلی Content Intelligence است.

## هدف
موتور باید بتواند در هر حوزه/Query Universe:
1. حساب‌های حرفه‌ای و رقبای مرتبط را کشف/ثبت کند.
2. نمونه‌ای همسان از محتوای اخیر آن‌ها بگیرد.
3. محتوای با آمار عمومی بالا و Outlierهای حساب را جدا کند.
4. Hook، موضوع، فرمت، زاویه، ساختار روایت، CTA و نشانه‌های بصری را استخراج کند.
5. Pattern را فقط پس از مقایسه دسته‌ای و Cross-source validation پیشنهاد دهد.

## دو نوع «آمار بالا»
### Absolute high performance
اعداد عمومی بالا در سطح دسته: views/plays، likes، comments و هر metric عمومی قابل اتکا.

### Account-relative outlier
عملکرد یک محتوا نسبت به baseline همان حساب و محتوای قابل‌مقایسه. این معیار برای جلوگیری از سوگیری به سمت اکانت‌های بسیار بزرگ ضروری است.

اگر baseline کافی نداریم، outlier_ratio باید null بماند؛ حدس ممنوع است.

## Sampling rule
- حداقل 10 حساب مرتبط در هر cluster مهم، در صورت وجود.
- ترجیحاً 20–30 محتوای اخیر برای هر حساب.
- Reels با Reels، carousel با carousel و static با static مقایسه شود.
- age normalization تا حد امکان رعایت شود.
- هم حساب‌های بزرگ و هم mid/small account outlierها وارد نمونه شوند.

## Metrics policy
### Competitive/Public
فقط metricهای واقعاً عمومی یا داده‌ای که از مسیر مجاز/قابل ممیزی دریافت شده ثبت شود.
ممنوع: جعل/استنتاج Reach، Saves، Shares، Retention، Profile Visits، Leads یا Sales رقبا.

### Owned
Reach، Saves، Shares، watch/retention و conversion metrics فقط از Instagram Owned Insights و پس از authorization رسمی Meta.

## Official path
Instagram API with Facebook Login برای Professional accounts می‌تواند basic metadata/metrics درباره دیگر Instagram Businesses/Creators و Business Discovery را فراهم کند. این مسیر پس از رفع Meta authorization باید به‌عنوان مسیر رسمی Competitive Discovery آزمایش شود.

## Fallback path
تا قبل از رفع Meta authorization:
- live public web/manual research
- user-provided exports/screenshots
- approved competitive analytics provider در صورت انتخاب آژانس

هیچ fallback نباید private metric را جعل کند.

## High-performance batch output
برای هر batch:
- account / username
- content URL / stable ID
- published_at
- format
- public metrics observed
- follower count at observation if defensible
- absolute rank within sample
- account-relative outlier ratio if defensible
- hook
- topic
- angle
- visual pattern
- CTA
- comments/question signals
- evidence confidence

## Gate before Pattern Mining
Pattern Mining اصلی Red Umbrella تا وقتی Instagram Competitive sample کافی نداشته باشد کامل تلقی نمی‌شود.
Pilot minimum:
- >=15 Instagram Competitive evidence
- >=5 distinct relevant accounts
- شامل حداقل 5 high-performance/outlier items در صورت وجود داده قابل دفاع

Target production batch:
- 10+ accounts per cluster
- 20–30 recent comparable items/account where technically feasible

## Red Umbrella priority clusters
- تبلیغات محیطی / بیلبورد / OOH
- دیجیتال مارکتینگ / هدررفت بودجه / انتخاب کانال
- مشاوره تبلیغات و بازاریابی
- تولید محتوا / creative strategy
- سرمایه‌گذاری تبلیغات محیطی
- integrated marketing / OOH + social

## Decision rule
تعداد ویو به‌تنهایی «ایده برنده» نمی‌سازد. موتور باید آمار را با relevance، repeatability، commercial relevance، local fit و evidence from other sources ترکیب کند.
