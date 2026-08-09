# Red Umbrella — Live URL Audit v1

**Execution:** GitHub Actions live HTTP audit
**Base:** https://chatreghermez.com
**URLs tested:** 52

## Status summary

- `200`: 9
- `404`: 3
- `ERROR`: 40

## URLs with errors or non-200 final status

- `https://chatreghermez.com/environmental-advertising` → `404` → `https://chatreghermez.com/environmental-advertising` — 
- `https://chatreghermez.com/environmental-advertising/` → `ERROR` → `https://chatreghermez.com/environmental-advertising/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/municipality-investment` → `404` → `https://chatreghermez.com/municipality-investment` — 
- `https://chatreghermez.com/municipality-investment/` → `ERROR` → `https://chatreghermez.com/municipality-investment/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/investment/` → `ERROR` → `https://chatreghermez.com/investment/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/billboard-rental-isfahan` → `ERROR` → `https://chatreghermez.com/billboard-rental-isfahan` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/billboard-rental-isfahan/` → `404` → `https://chatreghermez.com/billboard-rental-isfahan/` — 
- `https://chatreghermez.com/billboard-mobarakeh` → `ERROR` → `https://chatreghermez.com/billboard-mobarakeh` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/billboard-mobarakeh/` → `ERROR` → `https://chatreghermez.com/billboard-mobarakeh/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/cities/mobarakeh/` → `ERROR` → `https://chatreghermez.com/cities/mobarakeh/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/advertising-foladshahr` → `ERROR` → `https://chatreghermez.com/advertising-foladshahr` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/advertising-foladshahr/` → `ERROR` → `https://chatreghermez.com/advertising-foladshahr/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/cities/foladshahr/` → `ERROR` → `https://chatreghermez.com/cities/foladshahr/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/billboard-types` → `ERROR` → `https://chatreghermez.com/billboard-types` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/billboard-types/` → `ERROR` → `https://chatreghermez.com/billboard-types/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/structures/` → `ERROR` → `https://chatreghermez.com/structures/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/web-design-isfahan` → `ERROR` → `https://chatreghermez.com/web-design-isfahan` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/web-design-isfahan/` → `ERROR` → `https://chatreghermez.com/web-design-isfahan/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/web-design/` → `ERROR` → `https://chatreghermez.com/web-design/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/graphic-design` → `ERROR` → `https://chatreghermez.com/graphic-design` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/graphic-design/` → `ERROR` → `https://chatreghermez.com/graphic-design/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/printing` → `ERROR` → `https://chatreghermez.com/printing` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/printing/` → `ERROR` → `https://chatreghermez.com/printing/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/video-marketing-isfahan` → `ERROR` → `https://chatreghermez.com/video-marketing-isfahan` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/video-marketing-isfahan/` → `ERROR` → `https://chatreghermez.com/video-marketing-isfahan/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/advertising-video-production/` → `ERROR` → `https://chatreghermez.com/advertising-video-production/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/product-photography` → `ERROR` → `https://chatreghermez.com/product-photography` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/product-photography/` → `ERROR` → `https://chatreghermez.com/product-photography/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/social-media-management` → `ERROR` → `https://chatreghermez.com/social-media-management` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/social-media-management/` → `ERROR` → `https://chatreghermez.com/social-media-management/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/consulting` → `ERROR` → `https://chatreghermez.com/consulting` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/consulting/` → `ERROR` → `https://chatreghermez.com/consulting/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/about` → `ERROR` → `https://chatreghermez.com/about` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/about/` → `ERROR` → `https://chatreghermez.com/about/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/contact` → `ERROR` → `https://chatreghermez.com/contact` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/contact/` → `ERROR` → `https://chatreghermez.com/contact/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/credentials` → `ERROR` → `https://chatreghermez.com/credentials` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/credentials/` → `ERROR` → `https://chatreghermez.com/credentials/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/blog` → `ERROR` → `https://chatreghermez.com/blog` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/blog/` → `ERROR` → `https://chatreghermez.com/blog/` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/robots.txt` → `ERROR` → `https://chatreghermez.com/robots.txt` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/sitemap.xml` → `ERROR` → `https://chatreghermez.com/sitemap.xml` — TimeoutError: The read operation timed out
- `https://chatreghermez.com/sitemap_index.xml` → `ERROR` → `https://chatreghermez.com/sitemap_index.xml` — TimeoutError: The read operation timed out

## Canonical / redirect observations

- `https://chatreghermez.com/` | final `200` `https://chatreghermez.com/` | hops `0` | canonical `https://chatreghermez.com/` | title: آژانس تبلیغاتی چتر‌قرمز - شرکت تبلیغات در اصفهان
- `https://chatreghermez.com/services` | final `200` `https://chatreghermez.com/services` | hops `0` | canonical `https://chatreghermez.com/services/` | title: خدمات آژانس تبلیغاتی چترقرمز
- `https://chatreghermez.com/services/` | final `200` `https://chatreghermez.com/services/` | hops `0` | canonical `https://chatreghermez.com/services/` | title: خدمات آژانس تبلیغاتی چترقرمز
- `https://chatreghermez.com/portfolio` | final `200` `https://chatreghermez.com/portfolio` | hops `0` | canonical `https://chatreghermez.com/portfolio/` | title: نمونه کارها - آژانس تبلیغاتی چتر‌قرمز
- `https://chatreghermez.com/portfolio/` | final `200` `https://chatreghermez.com/portfolio/` | hops `0` | canonical `https://chatreghermez.com/portfolio/` | title: نمونه کارها - آژانس تبلیغاتی چتر‌قرمز
- `https://chatreghermez.com/about-us` | final `200` `https://chatreghermez.com/about-us` | hops `0` | canonical `https://chatreghermez.com/about-us/` | title: درباره ما - آژانس تبلیغاتی چتر‌قرمز
- `https://chatreghermez.com/about-us/` | final `200` `https://chatreghermez.com/about-us/` | hops `0` | canonical `https://chatreghermez.com/about-us/` | title: درباره ما - آژانس تبلیغاتی چتر‌قرمز
- `https://chatreghermez.com/contact-us` | final `200` `https://chatreghermez.com/contact-us` | hops `0` | canonical `https://chatreghermez.com/contact-us/` | title: تماس با ما - آژانس تبلیغاتی چتر‌قرمز
- `https://chatreghermez.com/contact-us/` | final `200` `https://chatreghermez.com/contact-us/` | hops `0` | canonical `https://chatreghermez.com/contact-us/` | title: تماس با ما - آژانس تبلیغاتی چتر‌قرمز

## Truth note

This records live HTTP evidence. `indexable_guess` only means final HTTP 200 with no explicit `noindex`; it is not a Google Search Console indexed-state claim.
