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
  `--paper-2` instead. Fixed so far in the nav (mega-menu cards, mobile
  drawer cards, bottom-nav bubble); `structure-hero` and
  `structure-services` still reference it and are pending a fix when page
  work resumes, since page files are out of scope while the nav is
  unlocked.

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

## 5. Navigation — designed first, then locked

The mega-menu (desktop **and** mobile) and the mobile bottom nav are
built and approved **before** any page design continues, and are then
identical site-wide, with no per-page variation.

- Both follow the owner's supplied references: an icon rail opening into
  a labelled panel, grouped sections, a highlighted active item, soft
  motion between states.
- Each entry uses an icon that actually matches its section, from the one
  approved family (Phosphor).
- Bottom nav is always `position: fixed` to the viewport bottom on
  mobile, with the liquid-bubble active indicator from the reference.
- Locked by `tests/test_structure_detail_spec.py::
  test_default_shell_mega_menu_has_real_identical_family_cards_on_every_page`.

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

Vendored, real, licence-verified, no CDN:

| Library | Purpose | Licence |
|---|---|---|
| Vazirmatn | Persian variable font | SIL OFL |
| Phosphor Icons | The single icon family (owner-approved) | MIT |
| Motion | Entrance + scroll animation | MIT |
| Swiper (+ coverflow) | Carousels, 3D gallery | MIT |
| GSAP + ScrollTrigger + SplitText | Scroll storytelling, per-character headings | Free commercial (Webflow-sponsored) |
| Lenis | Smooth scroll | MIT |

Rejected, with reason: Tailwind (conflicts with the token-based CSS
architecture this project is built on), Animate.css (redundant against
Motion/GSAP, and its canned effects are the generic look the owner
rejected), Bootstrap, HTML5 Boilerplate (a skeleton template, not a
library; the engine emits its own document).

All motion respects `prefers-reduced-motion: reduce`.
