# Red Umbrella — Design & Build Model v1

Status: **owner-directed, in force.** Supersedes the earlier
"refuse-to-build" content policy where the two conflict (see §3).

This file is the durable record of the design and build rules the owner
set for the Chatreghermez (چتر قرمز) website. It exists so the engine and
future sessions do not re-litigate decisions that were already made and
paid for. Machine-enforced parts of it are noted with the test that locks
them.

---

## 1. Colour

Palette is unchanged from `blocks/_tokens/style.css`. The rules are about
**application**, which is where the earlier mistake was.

| Token | Hex | Where it may be used |
|---|---|---|
| `--white` | `#ffffff` | The default page ground. Most sections. |
| `--paper` | `#fbf8f3` | Alternating section, to let the page breathe. |
| `--paper-2` | `#f2ede6` | Card contrast against `--paper`, chips, wells. |
| `--line` | `#ded8d1` | Dividers, card borders. |
| `--muted` | `#68646a` | Secondary text, the soft half of a two-tone heading. |
| `--ink-soft` | `#29282b` | A charcoal emphasis band — **at most once per page**. |
| `--ink` | `#171719` | Body text and headings. |
| `--red` | `#da1e49` | Primary CTA, accent marks, active state. |
| `--red-deep` | `#b9123a` | Hover/pressed state of the above. |

Rules:

- White dominates. If a page reads as dark, it is wrong.
- Never a flat-black section, never a red gradient, never a
  dark-radial-gradient "stage". Flat fills only.
- Charcoal (`--ink-soft`) is an accent band, not a theme. Max one per page.
- Red as a full section background is reserved for the single closing
  conversion band.
- Contrast between a background and the cards on it comes from the cream
  tones (`--paper` / `--paper-2`), which is what the owner asked for.
- **`--red-soft` (`#fff0f3`, a pink tint) is removed from the palette —
  the owner does not want it anywhere.** A red icon badge sits on
  `--paper-2` instead. Done in the nav (mega-menu cards, mobile drawer
  cards, bottom-nav bubble). **Still outstanding:** `structure-hero`,
  `structure-services` and `assessment-section` reference it. Those are
  page blocks, deliberately untouched while the nav was awaiting approval —
  clear them out as part of the next page pass.

## 2. Typography

Vazirmatn variable (100–900), self-hosted as a base64 `@font-face` in
`blocks/_tokens/style.css`. No font CDN — the sandbox blocks them and the
production site should not depend on one either.

| Role | Size | Weight |
|---|---|---|
| h1 | `clamp(2.1rem, 3vw, 3.3rem)` | 900 |
| h2 | `clamp(1.6rem, 2.6vw, 2.4rem)` | 900 |
| h3 | `1.05rem` | 800 |
| body | `0.92rem` | 400 |
| label / meta | `0.72rem` | 700 |

**Two-tone heading is the house signature.** The first clause carries
`--ink`, the trailing clause `--muted`:

> **کنار این سازه** <span style="color:#68646a">چه خدماتی لازم دارید؟</span>

Headings get `text-wrap: balance`. Numerals that line up in columns get
`font-variant-numeric: tabular-nums`.

## 3. Content completeness — the page always ships

**This reverses the engine's original policy.** The engine used to raise
`StructureDetailSpecError` and refuse to build a page whose registry
record was thin. The owner's instruction is the opposite: build the
complete page.

When real data is missing, in this order:

1. Derive it from the registry if it can be derived honestly.
2. Otherwise emit a **tagged placeholder** — a real, sensible default
   value carrying an explicit marker in the data (`"placeholder": true`
   or a `data-placeholder` attribute in markup) so it can be found and
   replaced.
3. Never silently invent a number and present it as verified.

Rationale the owner gave: content and images are corrected at WordPress
upload time; this stage is UI/UX, front-end and back-end design. Blocking
the build stops design work for no benefit.

The `placeholder` marker is what keeps this honest — it is the difference
between "a default we will replace" and "a fabricated statistic". Any
report to the owner about a generated page must say how many placeholder
values it contains.

## 4. Images

- Every design that needs an image **reserves the slot** — the layout is
  built around the image, never collapsed because the file is missing.
- A missing image renders its slot with the real `alt` text plus a short
  description / generation prompt, so the slot is self-describing and the
  right asset can be dropped in later.
- Owner-supplied photography (the Didanshow archive) is the owner's own
  material. **No "نمونه نصب واقعی" credit chip, no provenance caption** —
  that requirement is withdrawn. Attribution and final imagery are
  handled at WordPress upload time.

## 5. Navigation — LOCKED (2026-08-11)

Designed first, reviewed on a real phone, approved, and now **frozen for
the rest of the project**. The full specification and the procedure for
changing it live in **`05-rules/website/navigation-lock.md`** — read that
file, not this summary, before going near the nav.

- Identical on every page. No per-page variation, ever.
- Enforced by `tests/test_navigation_lock.py` (sha256 of all six files,
  plus a check that no other stylesheet targets a nav class, plus a check
  that every composed page gets the same shell data). **A failure there is
  a change to revert, not a test to update.**
- Also still covered by `tests/test_structure_detail_spec.py::
  test_default_shell_mega_menu_has_real_identical_family_cards_on_every_page`.
- Review with `python3 tools/build_nav_preview.py out.html`.

### What that build taught us — keep these

- **Judge glass against a vivid dark backdrop.** On a white-dominant page
  correct glass is nearly invisible and reads as broken. The preview tool
  paints a saturated backdrop for exactly this reason. It is a measuring
  rig, not a design.
- **Hover and click must not both be bound** on a mega-menu trigger for
  mouse users: the pointer opens the panel and the click that follows
  closes it again. Branch on
  `matchMedia("(hover: hover) and (pointer: fine)")`.
- **One handler per interactive element.** A legacy drawer handler left in
  `_foundation/behavior.js` fought the header's own and the drawer never
  visibly opened.
- **`@property` for anything two elements must share.** The bottom nav's
  `--bn-x` / `--bn-dip` drive the bar's notch, the bubble and the raised
  icon from one pair of values, so they cannot drift apart mid-animation.
- **`getBoundingClientRect` is physical space** — positioning maths off it
  needs no RTL branch. An RTL branch there was a bug.
- **A goo/metaball filter's blur sets its bridging distance.** At
  `stdDeviation` 9 it welded shut the gap that was supposed to show the
  page through the bar; 7 keeps the hole and still fuses on contact.
- **Stagger by class, not by hand.** Per-item `--step` custom properties
  feeding `transition-delay` and `animation-delay` keep sequenced entrances
  readable and easy to retune.
- **Verify with measurements, not screenshots.** Reading computed opacity
  per row is what proved the stagger; the screenshot looked simultaneous
  because of capture latency.

## 6. Mobile layout

Composition comes from the owner's supplied mobile references, not from
the engine's own taste. Card stacks, full-bleed image headers with the
heading in a floating white card, the bottom tab bar, chip filter rows.

## 7. Desktop layout

Irregular / editorial grids as in the references — mixed cell sizes, a
large feature cell beside smaller ones, deliberate asymmetry. Not a
uniform card grid. Hover states, horizontal scrollers and vertical
scroll-driven motion are part of the composition, taken from the
references rather than invented.

## 8. 3D scroll

Used **where it earns its place**, not everywhere: the structure gallery
(Swiper coverflow) and comparable showcase moments. A page should not be
one 3D effect after another.

## 9. Standing goals — never drop these

Every page is still judged against them:

- Schema.org structured data appropriate to the page type
- A correct, single-`h1` heading outline
- FAQ section
- The page's position in the sales funnel drives its structure
- Marketing and sales technique, explicit CTA
- Dwell time up, bounce rate down, conversion rate up
- The house content-writing model

## 10. Libraries

Vendored, real, licence-verified, no CDN. Public CDNs are blocked in the
build sandbox and the production site should not depend on one either.

| Library | Version | Purpose | Licence | Vendored at |
|---|---|---|---|---|
| Vazirmatn | variable 100–900 | Persian type | SIL OFL | `blocks/_tokens/style.css` (base64 `@font-face`) |
| Phosphor Icons | core | The single icon family | MIT | `blocks/_foundation/assets/icon-sprite.svg` |
| Motion | — | Entrance + scroll animation | MIT | `blocks/_foundation/assets/motion.min.mjs` |
| Swiper (+ coverflow, pagination) | 14.1.0 | Carousels, 3D gallery | MIT | `blocks/structure-gallery/assets/` |
| GSAP + ScrollTrigger + SplitText | — | Scroll storytelling, per-character headings | Free commercial (Webflow-sponsored) | `blocks/_foundation/assets/gsap.min.mjs` |
| Lenis | 1.3.26 | Smooth scroll | MIT | `blocks/_foundation/assets/lenis.min.mjs` |

Each ships a `<lib>.LICENSE.md` beside it recording origin and terms.
Registered in `VENDOR_LIBRARIES` in `src/ruos/block_registry.py`; a page
importing one is emitted with `<script type="module">`.

**How to vendor another one.** `npm install <pkg>` in a scratch dir →
read the licence → `esbuild --bundle --format=esm --minify --target=es2020`
→ confirm zero unresolved imports → copy into the owning block's `assets/`
→ write the `LICENSE.md`. Match the bundle's export shape to the import in
`behavior.js`: a default-vs-named mismatch throws at module load, and since
every block's script is concatenated into one module, that one error kills
the whole page's JavaScript, including unrelated blocks.

Rejected, with reason: Tailwind (conflicts with the token-based CSS
architecture this project is built on), Animate.css (redundant against
Motion/GSAP, and its canned effects are the generic look the owner
rejected), Bootstrap, HTML5 Boilerplate (a skeleton template, not a
library; the engine emits its own document).

All motion respects `prefers-reduced-motion: reduce`.

## 11. Tooling and working practice

Repeatable scripts live in `tools/` — never as one-off scratch files, so
the next session can rerun them:

| Tool | What it does |
|---|---|
| `tools/build_icon_sprite.py` | Rebuilds the Phosphor sprite from an npm checkout; `ICONS` maps sprite ids to `(name, weight)` |
| `tools/build_nav_preview.py` | Standalone preview of the locked nav on a vivid dark backdrop, for review |
| `tools/build_designspec.py` | Regenerates the design-model spec page from real repo assets |

**Browser verification.** Chromium is preinstalled at
`PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`; never run `playwright install`.
Check both breakpoints, use `pw.devices["iPhone 13"]` for mobile, capture
`pageerror` and console errors, and **measure computed values** — a
screenshot alone will not tell you whether a staggered animation is
staggered.

**Commit as you go.** The owner's standing instruction, and the sandbox has
already been reset mid-session once, silently reverting local work. Anything
not pushed can vanish. Branch: `claude/block-library`.

**Skills used on this project:** the `xlsx` skill for the owner's registry
spreadsheet, and `pdf` for the persona-system document. Both are Claude
Code skills, not runtime dependencies of the site.

**On "UI/UX PROMAX":** repeatedly asked about. It is a design-reasoning
skill/plugin for the assistant, not a JS or CSS library, and it is not
present in this environment's plugin catalogue — it adds nothing to the
page and cannot be installed into the repo. Say so plainly rather than
implying it is in use.

## 12. Mobile card system

Source: `reference/mobile-card-references/` — three screens the owner sent
on 2026-08-12 as the model for the **compact 2-up cards** in a mobile grid.
For the desktop card and the full-width card on mobile see §13 instead. **Look at the images**
before designing a card; §6 says mobile composition comes from the owner's
references, not from taste, and this is the reference set for cards.

### The shape language

- Card radius **20–28px**. Chips, pills and avatars fully round.
- **Photos bleed to the card's rounded edge.** Never a photo in a padded
  frame inside a card.
- **Rows are asymmetric**: two cells of different widths, or text beside
  image. A uniform grid repeated down the page is the failure mode these
  references exist to prevent — it is the same "list, not a designed page"
  problem `block_composer`'s card-grid cap already guards against.
- **Badges sit over the photo**, not in the text area.
- Text stack under a photo: **title → subtitle → meta**, each smaller and
  lighter than the last.
- **Section header = title on one side, link on the other**
  ("سازه‌های مرتبط" / "دیدن همه ←").
- **The card carries its own action** — a pill inside the card.
- **Category rows scroll horizontally**, icon + label per cell, clipped at
  the edge so more is obviously available.

### Applied to real Red Umbrella content

| Reference element | Our real equivalent | Data source |
|---|---|---|
| Category chip / icon row | Structure families, with their Phosphor icon | `_FAMILY_ICONS` + structure registry |
| 2-up photo card | One structure: real Didanshow photo, family name, context · dimensions meta | structure registry + `media/structures/<ID>/` |
| Badge over the photo | Dimensions, or the install context | registry `dimensions` / `context` |
| Text-left / photo-right split card | A related service beside a real photo | service registry |
| Stats flanking an avatar | **Do not use.** We have no verified follower/student counts and will not invent them | — |

### Rules that override the references

The references are travel and coaching apps. The composition transfers;
their look does not.

- **§1 wins on colour.** These screens are dark-card or warm-beige. Ours
  stays white-dominant, cream for contrast, red only as accent and the
  closing CTA. Do not import a dark card theme from reference 01.
- **§3 wins on content.** A card with no real data gets a tagged
  placeholder, never an invented number. The follower-count pattern in
  reference 01 has no honest equivalent here.
- **§4 wins on images.** Reserve the image slot even when the photo is
  missing, and describe it with `alt` plus a short prompt.
- **The navigation is locked.** References 01–03 all show a bottom bar;
  ours is already built and frozen. Take card composition from these
  screens, nothing else.

## 13. Wide card system — desktop, and full-width on mobile

Source: `reference/wide-card-references/` — three cards the owner sent on
2026-08-12. §12 governs the compact 2-up card; this governs the big one.
**Look at the images.**

### Two photo treatments — pick one per row, never both

- **Inset.** The photo sits inside the card's padding with its own smaller
  radius, floating on white. Quiet, editorial. Use where the card is
  mostly words.
- **Full-bleed with a scrim.** The photo runs to the card's rounded edge
  and carries chrome over a bottom gradient. Use where the card is
  mostly the thing itself — a structure.

### The parts, in order

1. **Chrome on the photo**: tag chips and any rating/marker in the top
   corners; carousel dots at the photo's bottom edge; the title, subtitle
   and primary action pill over a bottom scrim.
2. **A qualifier line** under the photo (family, install context).
3. **A hairline rule** separating identity from numbers.
4. **A stat row**: three cells, `value` over `label`. Value in `--ink` at
   roughly twice the label; label `--muted`, small. Optionally a square
   thumbnail parked at the far end — our dimension diagram belongs there.
5. **Description**, at most three lines.
6. **A meta line**, small and muted.
7. **The action**: either the overlay pill on the photo, or a full-width
   pill at the bottom. Never a bare text link.

Not every card needs all seven; the order never changes.

### House adjustments

- The reference CTA pills are black. Ours are `--red`.
- A dark scrim **over a photo** is fine — it is not a flat-black section
  and does not count against §1's charcoal budget. A dark *card body*
  does, and is not allowed.
- The two-tone sentence in reference 01 is already the house heading
  signature (§2): muted sentence, ink-dark emphasis on the words carrying
  the claim.
- Stats come from `_specs()` — ابعاد, جهت, محیط نصب. A missing one gets a
  tagged placeholder (§3), never an invented value. **There is no star
  rating**; we have no verified ratings and will not fabricate them.

## 14. Asymmetric row rhythm — and it must survive on mobile

Source: `reference/asymmetric-layout-references/`, sent 2026-08-12. This
supersedes the one-line version in §7 and extends it to mobile, which the
owner called out explicitly.

### The rules

1. **Alternate the side.** Consecutive rows never put the image on the same
   side: image-start, image-end, image-start.
2. **Cells are unequal, by a different amount each row** — 45/55, then
   55/40, then 47/53. A repeated 50/50 is the thing being avoided.
3. **Row heights vary.** Equal blocks in a level grid read as a list.
4. **A large numeral may anchor a row** (۰۱ / ۰۲ / ۰۳) above its heading,
   in `--ink`, sized well past the heading. Persian numerals, tabular.
5. **A card row may be staggered** — different heights and widths across
   the row, controls sitting inside the row rather than above it.
6. **Closing banner**: full width, heading on one side, pill action on the
   far side.
7. Grounds alternate white / `--paper` (§1), which these references already
   do with white and cream.

### On mobile the rhythm stays

The default failure is that every row collapses to one full-width stacked
column at the phone breakpoint and the asymmetry disappears. **That is not
acceptable here.** At phone width rows remain two unequal cells side by
side, alternating which side is wide — exactly what the coach screen in
`reference/mobile-card-references/` shows.

Collapsing a row to a single column is a per-row exception for content that
genuinely cannot survive the narrower cell, and it needs a reason. It is
never the blanket mobile treatment.

### Where the engine already helps

`block_composer` caps card grids per page (`MAX_CARD_GRIDS_PER_PAGE`) and
blocks runs of the same surface — the same instinct as these references.
The `layout` field in `block.json` is the hook: an alternating row block
should declare its own layout rather than reusing `card-grid`.

### What overrides these references

- **§1 colour.** Reference 02 is a dark/cream store and reference 01 is
  cool grey. Ours stays white-dominant with `--paper` for contrast and red
  as accent only.
- **§3 content.** Prices, ratings and product counts in these references
  have no verified equivalent here; a row with no real data gets a tagged
  placeholder, never an invented figure.
- **§4 images.** Each row's image slot is reserved even when the photo is
  missing — the asymmetry is in the layout, so it must not depend on the
  file existing.
