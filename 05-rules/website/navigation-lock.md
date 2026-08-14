# Navigation — LOCKED

**Status: locked by the owner on 2026-08-11. In force until the end of the
project.**

The site header (desktop mega-menu + mobile glass drawer) and the mobile
bottom nav were designed against the owner's own reference material,
reviewed on a real phone, and approved. They are now **frozen**.

## The rule

> The navigation is identical on every page of the site and does not change
> again. No page may restyle it, extend it, shorten it, recolour it, or
> "improve" it.

This applies to every assistant, every session, and every page still to be
built. If a page seems to need a different nav, the page is wrong, not the
nav.

## What enforces it

`tests/test_navigation_lock.py`, which fails the suite if:

1. any of the six locked files changes (sha256 pinned in the test),
2. any other block's stylesheet targets a nav class (`.site-header`,
   `.mega-*`, `.mobile-menu`, `.m-*`, `.bottom-nav`, `.bn-*`, …), which is
   the other way a per-page variation could sneak in,
3. two composed pages end up with different `site-header` or `bottom-nav`
   shell data.

The locked files:

```
blocks/site-header/{markup.html,style.css,behavior.js}
blocks/bottom-nav/{markup.html,style.css,behavior.js}
```

**A failure here is not a test to update. It is a change to revert.**

## The only way to change it

1. Ask the owner and get explicit approval **for that specific change**.
2. Make the change.
3. Rebuild the nav preview and verify it in a real browser at both
   breakpoints.
4. Recompute the hashes and update `LOCKED_FILES`, in the same commit as the
   change, with the owner's approval quoted in the commit message.

Steps 1 and 4 are not optional and not inferable from context. "The user
asked me to redesign the homepage" is not approval to touch the nav.

---

## What is locked — the specification

Keep this section accurate; it is the description of record.

> **Amended 2026-08-14 on the owner's explicit instruction** — "نوار منو در
> هنگام باز شدن نرم باز نمیشود / در زمان بسته شدن که کلا حرکتی ندارد که آن
> هم باید خیلی نرم بسته شود". Only `site-header/style.css` changed, and only
> its mega-menu transitions:
>
> - **Open and close are now tuned separately.** Both directions previously
>   shared the single transition declared on `.mega-panel`. Measured in a
>   real browser, `cubic-bezier(.16,1,.3,1)` spent **81% of the fade in the
>   first 60ms** of a 280ms open — a flash, not a reveal — and **92% in the
>   first 140ms** of the close, which is why the close read as no animation
>   at all. The base rule now governs closing, and a matching declaration on
>   `.mega-item.is-open .mega-panel` governs opening.
> - Curves are mid-weighted rather than front-loaded, and the panel, the
>   lead column and the cards each get both directions. The staggered card
>   entrance, the icon ring, the geometry, the colours and every behaviour
>   in `behavior.js` are unchanged.
> - Re-measured after the change: the open now moves 0.07 → 0.42 → 0.71 →
>   0.88 across its duration, and the close 0.88 → 0.59 → 0.26 → 0.06.

> **Amended again, same day** — the owner reported the identical symptom
> was still live: "بسته شدن مگا منو که درست نشده". The pass above only
> touched `.mega-panel`/`.mega-lead`/`.mega-card`; it never reached
> `.mobile-menu`, which had the same shared-curve bug. Measured before the
> fix: the drawer's close had already lost 94% of its opacity by 140ms of a
> 400ms transition. `.mobile-menu`'s base rule (closing) and `.is-open`
> (opening) are now split the same way the mega-panel's were. Re-measured:
> open moves 0.06 → 0.29 → 0.59 → 0.84 across its duration, close
> 0.98 → 0.88 → 0.59 → 0.26 → 0. Geometry, glass, stagger and every
> behaviour in `behavior.js` are unchanged. **Both amendments are on the
> current pinned hash — do not assume a fresh `git blame` read of only the
> first amendment's note is the full story.**

> **Amended a third time, same day** — a site-wide palette change, the
> owner's choice of "سیگنال ایمنی" from three proposed directions (see
> `blocks/_tokens/style.css`: `--red` is now `#e5142f`, was `#da1e49`; the
> ground tokens moved from a pink-cream to a warm-stone family). Everything
> in the header that reads its colour from a `var(--red)`/`var(--paper)`/etc.
> token picked this up automatically with no edit here. What *did* need
> editing: `@keyframes mega-ico-in`'s glow ring hardcodes three alpha-blended
> copies of the red hex instead of referencing the token, so those three
> literal values were updated to match. No geometry, layout, or `behavior.js`
> changed — only those hex literals.

### Desktop mega-menu

- White header bar, `--line` bottom border, backdrop blur. Never dark glass.
- Panel is anchored to the **fixed header**, not to its trigger, and spans
  the full content width (`inset-inline: max(24px, 50vw - 640px)`), so every
  structure family is visible at once with no inner scrolling.
- Layout: a 250px lead column (title, note, "see all" link) beside a
  4-column card grid.
- Opens on hover for mouse/fine-pointer devices, on click for touch. Binding
  both is a real bug — the pointer opens the panel and the click that
  follows immediately closes it. `behavior.js` branches on
  `matchMedia("(hover: hover) and (pointer: fine)")`.
- Motion: panel fades and rises; the lead column follows at 50ms; the cards
  arrive in sequence, 30ms apart, each icon lighting up behind a brief
  neon-red ring. Icon lifts and tilts on hover.
- Closes on Escape and on outside click.

### Mobile drawer

- **65vw** wide (capped at 340px), on the inline-start edge.
- Opens **downward** from behind the header (`translateY(-100%)` → `0`),
  not sideways.
- Real glass: translucent white gradient over
  `backdrop-filter: blur(30px) saturate(1.9)`, bright hairline border,
  rounded inner corners, outer shadow plus inset highlights. Groups and rows
  are lighter glass layered on top. **The page must remain visible through
  it** — that is the whole point, and it is the criterion the owner judges
  it by.
- Rows are compact: 28px icon badge, 0.7rem title, ~7px padding. The
  context/dimension note is **desktop-only** (`display:none` here) — at 65%
  width it truncated mid-number, and the owner's glass references are all
  single-label rows.
- Motion: rows arrive one at a time, 70ms apart, starting after the panel
  lands; each icon badge lights up under a neon-red ring on its own beat.
  Never all at once.

### Mobile bottom nav

Built to the owner's reference video frame by frame. Three mechanics, all
required.

> **Amended 2026-08-13 on the owner's explicit instruction** (the only
> change to any locked file since 2026-08-11):
>
> - **Red, per the owner's colour reference.** Bar and bubble both take
>   `--red-gloss` — glossy and textured, never flat or matte (design model
>   §1). They share one token deliberately: the goo filter fuses them while
>   travelling, and a white bubble sinking into a red bar blends to pink at
>   the neck, which the palette forbids. Icons are white (`#fff` active,
>   `#ffffff8f` idle).
> - **The bubble sits down in the bar.** `--bn-out: .2` — only 20% of it
>   rises above the bar's top edge; it was ~82%, which the owner judged too
>   high.
> - **The ring around the icon is 30% tighter.** `--bn-bubble: 46px`, down
>   from 56px: the empty space between the 23px icon and the bubble's edge
>   goes from 16.5px to 11.5px.
>
> The geometry lives in named custom properties on `.bottom-nav`
> (`--bn-bubble`, `--bn-out`, `--bn-cy`, `--bn-rest`, `--bn-gap`) rather
> than baked-in pixels, so these ratios stay legible and re-tunable.

Two things had to move to keep the mechanics intact under that geometry, and
both are load-bearing rather than cosmetic:

- **The notch is now concentric with the bubble** (`--bn-gap: 11px` of
  clearance all round). Offset centres were tried first: the crescent read
  at ~11px on the sides but fell to 6.8px underneath, and the goo filter
  filled that in — killing the hole on the very edge the reference shows it
  on. Measured, a gap under ~9px gets bridged at `stdDeviation` 7.
- **The goo layer runs 30px past the bottom of the viewport.** The filter
  blurs-then-thresholds whatever silhouette it is given, so it rounds every
  corner. On a white bar that was invisible; on a red one the rounded
  *bottom* corners showed as two white notches in the screen corners.
  Running the shape off-screen leaves only the top corners rounded.

One pre-existing, site-wide bug was fixed **inside this component only**:
the sprite's paths carry no `fill` attribute and no stylesheet sets `fill`,
so every icon on the site paints SVG-default black and every `color:` meant
to tint one is a no-op — the header's `--muted` nav icons, the `--red`
icon-badges and the `--red` checklist ticks included. `.bn-ico svg` now sets
`fill: currentColor` because this bar needs white icons on red. **The rest
of the site is untouched**; fixing it globally repaints every page and is
the owner's call, not a side effect of a nav change.

The three mechanics:

1. **The notch.** The bar is masked with a radial-gradient circle centred on
   the active item, cutting a real hole so the page shows through the
   crescent between the bar and the bubble. The goo filter's `stdDeviation`
   is **7** — at 9 it bridges the gap and the hole disappears.
2. **The dip.** Travelling between items the bubble sinks 34px into the bar,
   the goo filter fuses them into one liquid shape, then it surfaces at the
   destination. Lateral motion alone is wrong.
3. **The icon.** The active icon rides up into the bubble and tumbles
   (rotate + scale) while travelling. It must not slide across rigidly.

- `--bn-x` (bubble centre) and `--bn-dip` are registered with `@property`,
  so the notch, the bubble and the raised icon all interpolate from the same
  two values and cannot drift apart. `behavior.js` only measures and sets
  `--bn-x`; everything else is derived in CSS.
- No text labels — the reference has none. Labels ship as
  `.visually-hidden` for screen readers.
- `getBoundingClientRect` is physical/viewport space, so the positioning
  maths needs **no RTL branch**. An earlier RTL branch here was a bug.

### Both

- Phosphor icons only, from `blocks/_foundation/assets/icon-sprite.svg`.
- Every motion path has a `prefers-reduced-motion: reduce` fallback.
- No pink. `--red-soft` is gone from the palette; icon badges sit on
  `--paper-2`.

## How to review a change to it (once approved)

`tools/build_nav_preview.py` builds a standalone preview of just the two
components — no page content — and can drop a saturated dark backdrop behind
the page. **Judge the glass on that backdrop**: on the real white site,
glass is nearly invisible and looks "broken" when it is in fact correct.
That backdrop is a measuring rig, not a design.
