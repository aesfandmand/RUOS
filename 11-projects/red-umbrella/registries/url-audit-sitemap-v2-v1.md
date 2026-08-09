# Red Umbrella — URL Audit, Sitemap v2 & Redirect Map v1

**Status:** controlled pre-deploy artifact  
**Project:** Red Umbrella / چتر قرمز  
**Date:** 2026-08-09  
**Architecture source:** `11-projects/red-umbrella/registries/چتر_قرمز_معماری_و_رجیستری_سایت_v2.xlsx`

## Purpose

This package turns the approved Architecture & Page Registry v2 into an executable URL layer without silently inventing the current production state. It separates target information architecture from legacy-URL migration decisions and keeps uncertain redirects behind explicit evidence gates.

## Deliverables

- `چتر_قرمز_URL_Audit_Sitemap_Redirect_v1.xlsx` — review workbook and decision registry.
- `chatreghermez-sitemap-v2-target-predeploy.xml` — target sitemap candidate containing 80 URLs eligible for the planned indexable surface.
- `chatreghermez-redirect-map-v1.csv` — 22 legacy/migration rules with action, gate, confidence, and rationale.
- This document — deployment gate and operating notes.

## Current audit state

The target sitemap is **not yet a production-current sitemap**. Direct live HTTP retrieval of `chatreghermez.com` was not available from the current execution environment, so existing status codes, canonicals, indexability, and redirect chains have not been asserted as facts. Public web references support the domain association with Red Umbrella, but they do not prove the current state of every historical URL.

Therefore:

- Target architecture URLs are registered separately from live-current verification.
- Redirects are only marked ready when the architecture mapping is unambiguous and the source URL existence can be verified at deployment time.
- City pages remain evidence-gated.
- Legacy URLs with possible ranking/backlink value are held until Search Console / backlink / content-match review.

## Key locked URL decisions

- `/structures/` remains the master knowledge/data route for advertising structures.
- `/investment/` is a standalone investment hub, not a child of Services.
- `/blog/` is preserved as the canonical knowledge-content route; the UI label may be «مرکز دانش» without forcing a URL rename.
- `/projects/{project-slug}/` is the canonical project pattern.
- `/environmental-advertising/` is preserved unless live evidence requires a different migration decision.
- `/web-design-isfahan/` is not automatically collapsed into `/web-design/`; it requires GSC/backlink review.
- `/billboard-rental-isfahan/` requires content-intent matching before choosing service vs. Isfahan-local destination.
- `/about` vs `/about-us` and `/contact` vs `/contact-us` require live canonical verification before consolidation.
- Removed irrelevant content must not be mass-redirected to the home page; use the closest true equivalent or a genuine 404/410 when no equivalent exists.

## Deployment gate

Before publishing the XML as the production sitemap or applying redirects, complete these checks:

1. Crawl the live domain and capture status code, final URL, canonical, robots directive, and indexability for every legacy URL.
2. Export Google Search Console URL/page performance for the legacy set; record clicks, impressions, indexed state, and query intent.
3. Check backlink-bearing legacy URLs before any slug consolidation.
4. Resolve every `HOLD`, `LIVE_CANONICAL_REQUIRED`, `GSC_AND_BACKLINK_GATE`, `CONTENT_MATCH_REQUIRED`, and `EVIDENCE_GATED` row.
5. Apply permanent URL moves as server-side 301/308 redirects, one hop only where possible.
6. Update internal links, canonicals, structured-data URLs, navigation, hreflang if introduced, and media references to the chosen canonical URLs.
7. Generate the production sitemap from only final canonical indexable 200 URLs, deploy it, then submit it in Search Console.
8. Keep migration redirects in place long enough for users and search systems to complete the move; do not remove them immediately after re-crawl.

## Technical references

Primary Google Search Central references used for the migration rules:

- Redirects and Google Search: https://developers.google.com/search/docs/crawling-indexing/301-redirects
- Site moves with URL changes: https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes
- URL structure best practices: https://developers.google.com/search/docs/crawling-indexing/url-structure

## Production truth rule

**Architecture target ≠ proven live state.**  
No redirect or canonical decision marked as gated in this package may be promoted to production merely because the target architecture is cleaner. Live evidence wins for migration risk; the approved architecture wins for the intended future state.
