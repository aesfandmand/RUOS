# Content Intelligence Research Engine v0.3

## هدف
تبدیل تحقیق بازار محتوا به یک pipeline تکرارپذیر، چندپروژه‌ای و evidence-first. خروجی این لایه مستقیماً ایده یا تقویم نیست؛ ابتدا شواهد نرمال، قابل امتیازدهی و قابل ممیزی می‌سازد.

## Source roles
- Google Search / SERP: demand, intent, PAA, related searches, ranking formats
- Google Trends: direction, rising queries, seasonality; نه حجم مطلق جست‌وجو
- Instagram Competitive: public content, format, visible engagement, account-relative outliers when enough public history exists
- Instagram Owned: private insights; AUTH_PENDING و جدا از competitive
- YouTube / Shorts: topic demand, long-form questions, hooks, formats, visible performance
- Reddit: pain, question, objection, language, story, controversy; نه نماینده آماری بازار ایران
- TikTok Creative Center: emerging formats, hooks and creative patterns
- Competitor sites / comments / Q&A: positioning, gaps, objections, proof patterns
- Voice of Customer: DM, comments, calls, consultations, sales objections; بالاترین وزن برای مسئله واقعی برند

## Research horizon
- Default: 180 days
- Fast-moving social formats: 30–90 days weighted higher
- Evergreen demand: up to 365 days
- هر evidence باید `observed_at` و در صورت وجود `published_at` داشته باشد.

## Research stages
1. Project brief + query universe
2. Source discovery
3. Evidence capture
4. Deduplication / canonicalization
5. Intent + funnel classification
6. Pain / question / objection extraction
7. Hook / format / angle extraction
8. Performance normalization
9. Cross-source validation
10. Pattern mining
11. Opportunity scoring
12. Human approval gate
13. Strategy inputs
14. 30-day rolling calendar inputs

## Evidence contract
هر رکورد تحقیق حداقل:
- project_id
- source
- source_class: owned | competitive | search | community | first_party
- canonical_url یا stable source identifier
- title / topic
- observed_at
- published_at if known
- language / geography if known
- raw visible metrics if available
- normalized performance fields if defensible
- query / audience problem
- intent
- funnel stage
- pain / question / objection
- hook
- format
- angle
- evidence excerpt/summary
- confidence
- commercial relevance

## Cross-source rule
یک موضوع فقط به دلیل وایرال‌شدن در یک پلتفرم «فرصت قطعی» نیست. موتور باید تفکیک کند:
- single-source signal
- corroborated signal (>=2 independent source classes)
- first-party confirmed signal

First-party confirmation می‌تواند بدون وایرال بودن، اولویت تجاری را بالا ببرد.

## Outlier rule
- raw views به تنهایی معیار برنده بودن نیست.
- در صورت داشتن history کافی: item performance / median comparable items.
- مقایسه format و age تا حد ممکن همسان باشد.
- اگر baseline قابل دفاع نیست، outlier_ratio = null و موتور حق ساخت عدد تخمینی ندارد.

## Reddit policy
Reddit برای کشف زبان و مسئله استفاده می‌شود. هر insight Reddit برای بازار ایران باید یکی از این برچسب‌ها را بگیرد:
- hypothesis_only
- locally_corroborated
- first_party_confirmed

## Trend policy
- Trend ≠ strategy.
- Google Trends برای جهت/شتاب/فصل استفاده می‌شود، نه ادعای search volume.
- ترندهای اجتماعی کوتاه‌عمر باید freshness penalty داشته باشند.

## Quality gates
- no invented metrics
- no fabricated URLs
- no mixing owned/private and competitive/public metrics
- no calendar item without evidence_id(s)
- no commercial claim without source or first-party evidence
- preserve Persian query language as actually observed
- distinguish `تابلو تبلیغاتی` / `بیلبورد` from generic `تابلو` in Red Umbrella project
- `نصب` service-level positioning ممنوع مگر research evidence و project override صریح داشته باشد

## Standard outputs
1. research_dataset
2. query_demand_map
3. winning_content_map
4. pain_question_objection_map
5. hook_format_pattern_library
6. content_gap_map
7. opportunity_backlog
8. research_summary_for_strategy

## Review cadence
- Weekly lightweight discovery refresh
- Day 15 mini-review
- Day 30 performance review
- Day 45 strategic review
- Calendar remains 30-day rolling; strategy cycle remains 45 days.

## Current connector status
- Database: LIVE
- Instagram Owned: IMPLEMENTED / AUTH_PENDING
- Search/Reddit/YouTube: research contract defined in v0.3; automated collectors pending
- Manual/live web research may populate the same evidence contract before automation is complete.
