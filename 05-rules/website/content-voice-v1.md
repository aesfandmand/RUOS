# Red Umbrella — Content Voice & Sourcing Rules v1

Status: **owner-directed, in force.** Governs everything
`content_brief.py` / `content_draft.py` produce for the rich Structure
Detail sections (`numbered-features`, `parts-zigzag`, `checklist-section`,
and any `compare-cards` copy drafted the same way). The visual/palette/
layout rules stay in `red-umbrella-design-model-v1.md` — this file only
covers what gets *written* and where it's allowed to come from.

**§0 below is the real, owner-supplied, locked source of truth for tone
and language, supplied 2026-08-13.** Everything after §0 is this project's
own sourcing/honesty rules for the drafting *pipeline* specifically
(citation, placeholders) — narrower in scope, and must never contradict §0.

## 0. The locked Persian style guide, and the 13-writer corpus

Two real source files, both owner-supplied and locked, live next to this
file:

- **`persian-writing-style-v1.html`** — «سبک‌نامهٔ نگارش فارسی», status
  "قفل‌شده — هر متنی، از هر کسی، باید از این عبور کند" (locked — every
  text, from anyone, must pass through this). Based on Ogilvy's own
  writing plus an explicit warning against StoryBrand-style oversimplification
  in Iranian B2B. Open it directly for the full text (12 rules, glossary,
  rhythm table, 6 persona-voice profiles, 4 real before/after rewrites of
  Red Umbrella's own copy, and a 3-stage pre-publish test) — summarized
  here only to the depth `content_draft.py` can actually check by code.
- **`13-writers-corpus-v1.md`** (extracted from `13-writers-corpus-v1.docx`,
  the original) — 52 short, real, directly-quoted passages from 13 named
  authors, each with a one-line **قاعدهٔ آموزشی** (teaching rule) distilled
  from their actual sentence construction, not a paraphrase of their ideas.
  This is the concrete answer to "which masters" ground the voice — it was
  supplied, not invented, and every one of the 13 rules below is quoted
  from that file:

  | # | Author | Base work | Teaching rule |
  |---|---|---|---|
  | 1 | ست گادین (Seth Godin) | مهره‌ی حیاتی | یک ارزش انسانی را به یک رفتار مشخص و سپس به پیامد کسب‌وکاری وصل کن؛ جمله را با نتیجه‌ای ملموس ببند. |
  | 2 | جو پولیزی (Joe Pulizzi) | بازاریابی پرمحتوا | مفهوم را با یک تقابل روشن بازتعریف کن و بلافاصله معیارهای قابل سنجش را در یک فهرست کوتاه بیاور. |
  | 3 | جیم کالینز (Jim Collins) | ساختن برای ماندن | پس از ارائهٔ شاهد یا بحث، نتیجه را در یک اصل کوتاه و به‌یادماندنی جمع‌بندی کن. |
  | 4 | دن نوریس (Dan Norris) | استارت‌آپ نوپای هفت‌روزه | هر توصیه را به یک اقدام فوری و یک شاخص تجاری قابل مشاهده پیوند بده. |
  | 5 | دیل کارنگی (Dale Carnegie) | آیین دوست‌یابی | اصل رفتاری را با یک نیاز انسانی توضیح بده و برای هشدار، از استعاره‌ای روشن و کوتاه استفاده کن. |
  | 6 | چیپ هیث و دن هیث (Chip & Dan Heath) | ایدهٔ عالی مستدام | مغز ایده را در یک جملهٔ کوتاه بگو؛ جزئیات را پس از آن و فقط در صورت نیاز اضافه کن. |
  | 7 | رابرت کیوساکی (Robert Kiyosaki) | ۱۱۰ راز کیوساکی | اصطلاح مالی را با تعریف ساده و سپس یک تشبیه روزمره توضیح بده؛ منبع نسخه را حتماً کنترل کن. |
  | 8 | فیلیپ کاتلر (Philip Kotler) | نسل چهارم بازاریابی | ابتدا الگوی قدیمی و جدید را در تقابل قرار بده؛ سپس پیامد اجتناب‌ناپذیر محیط را صریح بیان کن. |
  | 9 | **دیوید اگیلوی (David Ogilvy)** | اعترافات یک تبلیغاتچی | توصیه را به شکل فرمان روشن و قابل اجرا بنویس؛ هر جمله فقط یک اقدام داشته باشد. |
  | 10 | استفان کاوی (Stephen Covey) | ۷ عادت مردمان مؤثر | مفهوم را از رفتار روزمره به اصل هویتی ارتقا بده و با ضمیر جمع، خواننده را همراه کن. |
  | 11 | پیتر تیل (Peter Thiel) | از صفر به یک | فرض رایج را زیر سؤال ببر و سپس یک نهی راهبردی روشن ارائه کن. |
  | 12 | نیر ایال (Nir Eyal) | قلاب | رفتار کاربر را با محرک، تکرار و پیامد توضیح بده؛ از اصطلاحات پیچیده فقط پس از تعریف ساده استفاده کن. |
  | 13 | **دانلد میلر (Donald Miller, StoryBrand)** | هر برند یک قصه است | خواننده یا مشتری را قهرمان قرار بده؛ پیام را با یک تقابل ساده و قابل فهم بساز. |

  #9 and #13 are the two the style guide itself names as its explicit
  basis ("مبنا: اگیلوی + هشدار StoryBrand دربارهٔ B2B ایران") — Ogilvy for
  the discipline of the writing itself, Miller's StoryBrand cited as a
  *caution*, not a template to copy wholesale: §1's own rule 11 exists
  specifically because oversimplifying for an Iranian B2B/institutional
  reader (a municipal manager, an engineer) reads as shallow, not
  persuasive — authority there comes from real technical detail, not from
  removing it.

### The 12 hard rules (§1 of the style guide, condensed)

1. No em dash (—) — use «؛» or a full stop instead; it's a translation tell.
2. No «ما می‌دانیم که...» and its family («این بدان معناست که»، «اجازه
   دهید»، «ما اینجاییم تا»، «نه تنها... بلکه»، «به شما کمک می‌کنیم تا») —
   direct StoryBrand-template translation, reads as a translated book.
3. No perfectly symmetric triads — at least one list per page must have 2,
   4 or 5 items, and items should not all be the same length.
4. Not every section closes on a clever aphorism — one or two per page,
   not one per paragraph.
5. No unsupported adjective («بهترین»، «بی‌نظیر»، «منحصربه‌فرد»،
   «انقلابی»، «پیشرو») — replace with a real number and name.
6. No industry clichés («راهکار جامع»، «تیم متخصص و مجرب»، «رضایت مشتری
   اولویت ماست»، «همراه شما»، «تجربه‌ای متفاوت»، «در دنیای امروز»).
7. No abstraction where a scene will do — build a picture, not a concept.
8. No more than 3 stacked ezafe constructions in a row.
9. No translated passive voice («انجام می‌شود»، «صورت می‌گیرد»، «قرار داده
   می‌شود») unless the subject genuinely doesn't matter — Persian is an
   active-voice language.
10. No redundant «شما» — Persian's verb ending already carries the
    subject; add «شما» only for real emphasis.
11. Simple, yes — but never at the cost of real technical detail. Iranian
    B2B authority comes from specifics (real numbers, real project names),
    not from an emotional, oversimplified story.
12. No rounded/inflated numbers («بیش از ۱۰۰ پروژه») — a small, real,
    specific number is more credible than a big round one. If the real
    number isn't known, leave it blank and ask the owner — never invent one.

## 1. Two kinds of claim, two different rules

**Comparative / market / general-engineering claims** — "sazeh X typically
costs less to maintain than a same-size billboard," "this structure suits
lower-speed urban frontage rather than highway shoulders" — can be drafted
from real search evidence (Iranian and international OOH-industry sources),
each sentence carrying a `source_id` that resolves in the verified
`ResearchSnapshot` it was drafted from.

**Claims about Red Umbrella's own product** — an exact part dimension, a
specific wattage, "our workshop uses X alloy," an internal process detail —
can **never** come from a competitor's page or a generic industry article,
even with a citation attached. No external source can honestly attest to
Red Umbrella's own engineering. These either come from the owner directly
(the straboard model) or stay a tagged placeholder. Never infer Red
Umbrella's own spec by analogy to what a competitor's page says about
theirs.

## 2. When real, cited text isn't found: fill, mark, ship

Per the owner's explicit instruction (2026-08-13): the engine's job is to
produce a **complete, standard page** — never to leave a hole because one
slot's research came up short. Where `content_brief.py`'s search genuinely
could not surface enough real text for a slot, `content_draft.py` fills
that slot with real Lorem Ipsum (the standard Latin placeholder passage —
not an invented Persian filler; being obviously foreign text in an
RTL Persian page is exactly what makes it unmissable) and tags the item
`"placeholder": true`. The block markup renders any `placeholder`-tagged
text in the muted `#9a938a` tone already used by `spec-table`'s
`data-placeholder` cells (`numbered-features`, `parts-zigzag`,
`checklist-section` — see their `style.css`) — one consistent, recognizable
"not final" signal across every block, not a new color per block.

**This is not a relaxation of the no-fabrication rule — it's the same rule
applied to prose.** Lorem Ipsum is never mistakable for a real claim; a
`"value": "قیمت پس از استعلام"` placeholder chip and a Lorem Ipsum
paragraph do the same job at different content shapes. What must never
happen is real-looking, specific Persian prose standing in for research
that wasn't actually done.

A page with placeholder-tagged sections is a genuine deliverable at this
stage of the pipeline: it previews, composes, and passes `ruos critique`
(placeholders are counted, not penalized — see design model §17). The
**human edit pass that replaces every placeholder with real copy happens
before the page is uploaded to WordPress** — that boundary, not
`ruos generate`, is the actual publish gate.

## 3. Tone

Governed by `persian-writing-style-v1.html` §1–3 (the 12 rules above,
plus the Persian-signature techniques — real idiom, rhetorical questions,
speech particles like «که»/«هم»/«دیگر»، starting from a scene not a
thesis, Iranian modesty in claims, «؛» over «—», expert-only concrete
detail — and the rhythm rules — at least one under-6-word sentence per
paragraph, no paragraph over 4 sentences, vary list-item length). No
unsourced superlatives. A specific claim ("مقاوم در برابر باد تا ۹۰
کیلومتر بر ساعت") needs a citation or a placeholder tag; a comparative
claim in general terms ("نسبت به بیلبورد هم‌سایز سبک‌تر است") is fine
when it traces to real search evidence, same as §1 above.

Watch-listed regardless of citation — the real glossary from the style
guide's §4 (tab ۴), not an invented shortlist:

خط تیرهٔ بلند (—) · ما می‌دانیم که… · این بدان معناست که · به شما کمک
می‌کنیم تا… · نه تنها… بلکه… · اجازه دهید · ما اینجاییم تا · در دنیای
امروز · راهکار جامع · فول‌سرویس · تیم متخصص و مجرب · رضایت مشتری اولویت
ماست · بهترین / برترین / بی‌نظیر · منحصربه‌فرد / انقلابی · تجربه‌ای
متفاوت · همراه شما · انجام می‌شود / صورت می‌گیرد · قرار داده می‌شود ·
شما می‌توانید… · جهت (به‌جای «برای») · می‌باشد · بیش از ۱۰۰ … (عدد گرد
گزافه) · با ما تماس بگیرید · خدمات ما شامل … می‌باشد

`content_draft.py` always surfaces a hit as a non-blocking `refinement`
finding rather than judging from the text alone whether context already
handles it — that judgment call is for the human reading the report, not
a regex. A finding here is never a rejection on its own; it is always
worth a second look before the sentence ships. The glossary is explicitly
a living document (see the style guide's own note on tab ۴) — add to it
in `persian-writing-style-v1.html` first, then mirror new entries into
`content_draft._BANNED_WORDS` so the checker actually catches them.

## 4. Per-block writing guidance

- **`numbered-features`** (`چرا این سازه`): 4–6 items, each a real
  advantage — comparative claims sourced per §1, own-spec claims from the
  owner or placeholder.
- **`parts-zigzag`** (`اجزای سازه`): a component breakdown. Component
  *names* (ستون اصلی، فک بالا، فونداسیون…) are generic OOH-structure
  engineering vocabulary and safe to draft from industry sources; exact
  *dimensions/materials/wattages* for Red Umbrella's own build are owner-only
  — see straboard's own parts-zigzag section for the shape (some rows carry
  real specifics, others are explicitly marked "در انتظار دیتای مهندسی").
- **`checklist-section`**: "when this structure fits" / "what drives its
  price" — both are reasonable to draft from comparative research, same
  rule as `numbered-features`.
- **`workshop-gallery`, `knowledge-carousel`**: out of scope for this
  pipeline entirely — real workshop photography and real published
  articles/videos are owned assets no search can produce. These stay
  owner-supplied, same as today.

## 5. What the validator checks (`content_draft.py`)

Mirrors `page_critic.py`'s finding shape (discipline/severity/observation),
not a new mental model:

- Every block entry validates against its real `block.json` contract
  (reuses `block_composer._validate_slots`).
- Every non-placeholder sentence stating a specific/comparative claim
  carries a `source_id` present in the brief's verified snapshot.
- Every `placeholder`-tagged item is genuinely Lorem Ipsum (or an existing
  short placeholder-chip pattern), never real-looking prose mislabeled.
- The §3 banned-word list is checked against non-placeholder text only.

A clean report means "safe to build and preview" — it does not mean "ready
for WordPress." `placeholder_count` in the report is the actual to-do list
for the human edit pass.
