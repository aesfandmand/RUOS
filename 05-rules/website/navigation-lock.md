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
required:

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
