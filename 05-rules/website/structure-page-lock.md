# Structure Detail page — LOCKED

**Status: locked by the owner on 2026-08-14. In force until the end of the
project.**

The straboard page — `pages/blocks/straboard.json` — was designed, reviewed
across mobile and desktop, corrected through three full rounds of the
owner's feedback (content restoration, motion, layout, carousel controls),
and given a site-wide colour pass ("سیگنال ایمنی"). It is now **frozen**,
and it is the **mandatory template for every other structure's page**.

## The rule

> The Structure Detail archetype — its 19 blocks, in this exact order, with
> this exact markup/CSS/behaviour — is identical for every structure. When
> another structure's page is prepared, copy `straboard.json`'s block list
> and order, replace only the data, and never touch a locked block file to
> make one structure "look different." If a structure seems to need a
> different layout, the layout is not the thing to change.

This applies to every assistant, every session, and every structure still to
get its own page. It is the same rule `05-rules/website/navigation-lock.md`
already states for the header and bottom nav — this extends it to the rest
of the page.

## What enforces it

`tests/test_structure_page_lock.py`, which fails the suite if:

1. any of the locked block files changes (sha256 pinned in the test),
2. `pages/blocks/straboard.json`'s own block order changes,
3. `LOCKED_FILES` pins a block `straboard.json` no longer actually uses
   (the inverse mistake — catches a stale lock, not tampering).

`page_critic.py` also checks discipline `"structure-archetype"` on every
critique run, the same way it already checks `"navigation"` — a hash
mismatch there is a **blocker**, not a graded finding.

**A failure here is not a test to update. It is a change to revert.**

## The locked archetype — 19 blocks, in order

```
top      product-hero          hero, real photos, stats
what     editorial-split       "چیست؟" — full definition, sticky photo
why      numbered-features     benefits, lead-column card (icon+number+title | description)
models   variant-carousel      model variants, desktop prev/next + dots
gallery  structure-gallery     real installation photos, 3D coverflow (>=5 photos)
parts    parts-zigzag          components, one card per row
compare  compare-cards         path/model comparison
specs    spec-table            technical spec sheet, both variant columns always visible
color    editorial-split       colour/finish options, sticky photo
price    checklist-section     pricing factors
projects variant-carousel      real project examples, desktop prev/next + dots
factory  workshop-gallery      real workshop photos, CSS multi-column masonry
knowledge knowledge-carousel   articles/videos, desktop prev/next + dots (per group)
fit      checklist-section     "is this the right fit" checklist
paths    compare-cards         alternate path comparison
services structure-services    cross-sell services, two columns at every width
others   structure-related     sibling structure families
faq      faq-section-final     — second-to-last, per the owner's explicit placement
quote    lead-form             — always last
```

Shell (identical on every page, separately locked in `navigation-lock.md`
except `site-footer`, locked here): `site-header`, `site-footer`,
`bottom-nav`.

## Locked files

```
blocks/_tokens/style.css
blocks/_foundation/{style.css,behavior.js}
blocks/site-footer/{markup.html,style.css}
blocks/product-hero/{markup.html,style.css,behavior.js}
blocks/editorial-split/{markup.html,style.css}
blocks/numbered-features/{markup.html,style.css}
blocks/variant-carousel/{markup.html,style.css,behavior.js}
blocks/structure-gallery/{markup.html,style.css,behavior.js}
blocks/parts-zigzag/{markup.html,style.css}
blocks/compare-cards/{markup.html,style.css}
blocks/spec-table/{markup.html,style.css}
blocks/checklist-section/{markup.html,style.css}
blocks/workshop-gallery/{markup.html,style.css}
blocks/knowledge-carousel/{markup.html,style.css,behavior.js}
blocks/structure-services/{markup.html,style.css}
blocks/structure-related/{markup.html,style.css,behavior.js}
blocks/faq-section-final/{markup.html,style.css}
blocks/lead-form/{markup.html,style.css,behavior.js}
```

`blocks/site-header/*` and `blocks/bottom-nav/*` are locked separately by
`navigation-lock.md` — not duplicated here, but every bit as much part of
this page.

## The only way to change it

Identical procedure to the navigation lock:

1. Ask the owner and get explicit approval **for that specific change**.
2. Make the change.
3. Rebuild the preview and verify it in a real browser at both breakpoints
   (`python3 tools/build_draft_preview.py <structure-id> --spec pages/blocks/straboard.json`).
4. Recompute the hashes and update `src/ruos/structure_page_lock.py`'s
   `LOCKED_FILES`, in the same commit as the change, with the owner's
   approval quoted in the commit message — same as `navigation_lock.py`.
5. If the block order itself changed, update `LOCKED_BLOCK_ORDER` too.

Steps 1 and 4 are not optional and not inferable from context. "The user
asked me to build STR-004's page" is not approval to change the archetype —
it is the instruction to *copy* it.

## Building the next structure's page

1. Copy `pages/blocks/straboard.json` to `pages/blocks/<slug>.json`.
2. Keep the `blocks` array's order and `block` values exactly as they are.
3. Replace every `data` value with that structure's own real content: real
   registry data where it exists (hero, specs, gallery, related, services —
   `structure_detail_spec.py`'s helpers already produce these), and a
   Lorem-Ipsum value tagged `"placeholder": true` everywhere real content
   does not exist yet (design model §3/§20). Never invent a plausible
   number or claim.
4. Never edit a block's own `markup.html`/`style.css`/`behavior.js` to make
   this structure's version look different — that is exactly what this
   lock exists to prevent.
5. Render both breakpoints, get the owner's explicit approval in chat, then
   commit `pages/blocks/<slug>.json` — same gate as every page before it
   (design model §20, CLAUDE.md §5).
