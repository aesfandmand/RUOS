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

### Red surface finish — glossy and textured, never flat (2026-08-12)

Source: `reference/red-surface-reference/`. **Every filled red surface**
(a button, the closing CTA band, a pill) uses `--red-gloss` /
`--red-gloss-shadow` (`blocks/_tokens/style.css`), never a flat `var(--red)`
fill. Not matte, not flat — sharp, glossy, with a real texture: a soft
highlight bloom top-left, a tight repeating diagonal for a ribbed texture,
and a light-to-deep vertical tone shift for dimension. CSS gradients only,
no image asset, so it stays deterministic.

**This does not reopen the "never a red gradient" rule above.** That rule
bans red/black used as a whole section's dramatic mood backdrop — the flat,
staged look the owner rejected early in the project. `--red-gloss` is a
surface finish for an actual UI element (a button, a badge, the one closing
band §1 already allows full red). Both hold at once: red stays an accent
and the single closing conversion band, and wherever it fills a surface, it
now uses this finish instead of a flat hex.

Applied to (non-nav only — the locked nav is never touched for this or any
other reason): `.primary-button` and `.honest-no` (`_foundation`),
`.review-gate`, `.products-route-cta`, `.cmp-cta`, `.var-cta:active`,
`.p-hero-next`, `.contact-link:hover` (`contact-sheet`). Small accent marks
(a 6px dot, a 3px bar) are exempt — texture is invisible at that size.

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

## 15. Motion — what "soft" means

Source: `reference/motion-references/`, two recordings the owner sent on
2026-08-12 asking for **موشن نرم** (soft motion). This is the definition of
record; §8 still governs *where* motion is allowed, this governs *how* it
moves.

### The rules

1. **Long and eased, never bouncy.** 400–700ms on entrances and panel
   transitions, `cubic-bezier(.16,1,.3,1)` or similar ease-out. Springy
   overshoot is reserved for the locked bottom-nav bubble, which the owner
   approved specifically; it is not the house default.
2. **The panel and the type move separately.** In the slider reference the
   photo panel slides vertically while the headline and data block clear
   out and re-enter on their own timing. One animation dragging a whole
   section around is the thing to avoid.
3. **Reveal in reading order, staggered.** Grid cells, list rows and cards
   arrive one behind another — already how the locked nav does it, via
   per-item `--step` custom properties (§5).
4. **Direction carries meaning.** The slider moves its panel vertically
   because the slide is a change of subject; small entrances rise a few
   pixels. Do not mix six directions in one section.
5. **Depth by overlap, not by 3D.** The reference gets its depth from a
   small photo overlapping the big panel's corner. Cheap, robust, and it
   survives at any width.
6. **Always preview what is next.** The slider keeps a bar naming the next
   item and its number on screen. Anything paged should do the same rather
   than leaving the visitor to guess there is more.
7. `prefers-reduced-motion: reduce` collapses every one of these.

### Confirmed again by these references

- **Two-tone headings** (§2) appear in the second reference independently —
  ink for the clause that carries the claim, muted for the rest. Treat this
  as settled house style, not a per-page choice.
- **Asymmetric splits** (§14) — the testimonial is an unequal two-cell row.

### Libraries for this

All already vendored (§10): Swiper for the paged panel, Motion or GSAP
ScrollTrigger for staggered reveals, Lenis for scroll feel. Do not add a
new animation library for any of the above.

## 16. Motion must fail open — and it must be measured

Learned the hard way on the straboard page, where the first build shipped
with **50 elements stuck at `opacity: 0`**. Whole paragraphs were invisible.
The page looked empty and motionless and the owner rejected it.

1. **A reveal that does not fire is missing content, not a missing
   animation.** Any pattern that starts an element hidden must have a
   fallback that reveals it: alongside the observer, sweep on scroll and
   reveal anything the viewport has already passed. A fast flick outruns
   `IntersectionObserver`'s delivery, and without the sweep those sections
   stay blank forever.
2. **Prefer the platform.** Motion's `inView` silently never fired in our
   vendored bundle. `IntersectionObserver` is native, has no bundle to go
   wrong, and is what the foundation now uses.
3. **Verify motion by measuring, never by screenshot.** The check is:
   count `[data-reveal]` elements, scroll the whole page, count how many
   carry `is-in`. It must reach 100%. A screenshot of a page whose text is
   invisible looks like a page with generous whitespace.
4. **Translucent red is pink.** `var(--red)` at 14–34% opacity over white
   renders as the one colour the owner banned. Use a full-opacity red
   accent or a cream token — never a faded red.

### The motion floor for any page

A page with only scroll-fade is "خواب‌آور". Every page carries, at minimum:

- staggered reveal in reading order (`--reveal-i`, ~90ms apart),
- one masked image reveal (`data-reveal="mask"`, clip-path wipe),
- rows in a zigzag arriving from alternating sides
  (`data-reveal="start"` / `"end"`),
- depth on any card rail — the centred card dominant, neighbours scaled
  back and turned, driven from scroll position,
- parallax on the hero image,
- micro-interaction on every pressable thing.

## 17. The page critic — an automated art/creative-director pass

Source: `src/ruos/page_critic.py`, `tests/test_page_critic.py`. Built
2026-08-12 at the owner's request for an assistant that reviews every
generated page — section by section, icon by icon if needed — the way a
creative director and an art director would, before the owner has to.

```
python3 -m ruos.cli critique <slug> --spec-root pages/blocks
```

Ten disciplines, each a real code check against the actually-rendered page
(HTML, CSS, script, the source spec, the block registry) — never a model's
subjective opinion, which design model §3 would forbid as an unverifiable
claim: **colour** (no pink, no flat black, no flat `var(--red)` fill where
`--red-gloss` belongs — checked per block, so it can name which one),
**navigation** (the locked shell is present and hash-matches — any failure
here is a hard blocker, not graded), **motion** (every section reveals,
driven by a real observer, with a reduced-motion fallback), **icons** (every
`#icon-*` reference resolves in the sprite, content is not carrying zero
icons), **content-honesty** (placeholders are counted and must render a
visible marker — §3), **images** (no collapsed slot), **rhythm** (surfaces
the composer's own anti-repetition proof), **accessibility** (one H1, every
image/button has a real accessible name), **seo-schema** (JSON-LD, canonical,
a description sized for a real snippet), **performance** (byte budgets).

A finding's severity depends only on whether it found something — a check
with zero failures is a **strength**, full stop, never graded down by an
arbitrary baseline. A critic that reports "96/100, needs work" on a page
with nothing wrong trains people to stop reading it.

### Not the old `design_critic.py` / `virtual_studio.py` / `qa.py` stack

That stack already existed in the repository and is real, deterministic
code — but its `qa.py::evaluate()` gate is hard-wired to exactly one legacy
page: a fixed five-section kind sequence
(`hero, story, knowledge, interaction, conversion`), literal strings from
the old static compiler's output (`"ruos-bottom-nav"`,
`"data-component-variant"`), and `PageSpec.metadata` keys nothing in the
block-library pipeline populates. Bridging it would have meant rewriting its
internals anyway, so `page_critic.py` is a clean rebuild against what the
block pipeline actually produces, reusing only the reporting shape that
stack got right (a finding per discipline, with severity, a concrete action
and evidence — never a bare pass/fail). Do not try to wire the old stack in
later without rereading this section; it was a deliberate, considered choice
the first time.

### What it found, the first time it ran

Proof it is a real check and not a rubber stamp: run cold against the three
pages that existed before it, it caught genuine, previously-undetected
leftovers — `--red-soft` (pink) still in `structure-hero`,
`structure-services` and `assessment-section`, and four flat `var(--red)`
fills (`.structure-diagram-box:before/:after`, `.structure-spec-row:before`,
two `.eyebrow:before` dashes) that should have been `--red-gloss` per §1.
All fixed the same session, verified clean by rerunning the critic
afterward. The two billboard pages still carry one honest, unresolved
finding — no `[data-reveal]` motion, since they predate the motion system
built for straboard — left as backlog rather than silently fixed, since that
is page work outside this task's scope.
