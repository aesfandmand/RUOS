# Red Umbrella — Content Voice & Sourcing Rules v1

Status: **owner-directed, in force.** Governs everything
`content_brief.py` / `content_draft.py` produce for the rich Structure
Detail sections (`numbered-features`, `parts-zigzag`, `checklist-section`,
and any `compare-cards` copy drafted the same way). The visual/palette/
layout rules stay in `red-umbrella-design-model-v1.md` — this file only
covers what gets *written* and where it's allowed to come from.

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

Matter-of-fact, engineering-register Persian, second person plural
(«شما»/«می‌توانید») where the sentence needs a subject. No unsourced
superlatives. A specific claim ("مقاوم در برابر باد تا ۹۰ کیلومتر بر
ساعت") needs a citation or a placeholder tag; a comparative claim in
general terms ("نسبت به بیلبورد هم‌سایز سبک‌تر است") is fine when it
traces to real search evidence, same as §1.

Watch-listed regardless of citation: بهترین، بی‌نظیر، پیشرفته‌ترین، تضمینی،
انقلابی، مادام‌العمر، ۱۰۰٪ تضمین‌شده. `content_draft.py` always surfaces
these as a non-blocking `refinement` finding rather than trying to judge
from the text alone whether a nearby citation actually attributes the
specific superlative — that judgment call is for the human reading the
report, not a regex. A finding here is never a rejection on its own; it is
always worth a second look before the sentence ships.

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
