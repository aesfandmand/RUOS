# Asymmetric layout references — owner-supplied

Sent by the owner on 2026-08-12 as **the model for asymmetric arrangement,
explicitly including the mobile version**. Read the images before laying
out a section.

| File | What it is | What to take from it |
|---|---|---|
| `01-numbered-zigzag-rows.jpeg` | Headphone product page | Three numbered rows that alternate side — image-left/text-right, then text-left/image-right, then image-left again. Each row's image is a *different* width and height. A large numeral (01/02/03) anchors each row above its heading. Below them a 4-across product tile row, then a wide closing banner with the heading on one side and a pill action on the other. |
| `02-alternating-rows-and-staggered-row.jpeg` | Lamp store page | The same alternating rows in a cream section. Above them, a "Best Sellers" row of three cards at *staggered heights and widths* rather than a level grid, with the carousel arrows sitting in the row. |
| — | The coach screen | The third image the owner sent with these is byte-identical to `../mobile-card-references/01-dark-coach-profile-mixed-cards.jpeg`, already stored. It shows the same idea at phone width: a narrow text card beside a wider photo card, then a text-left/photo-right row. |

## The pattern

1. **Alternate the side.** Consecutive rows must not put the image on the
   same side. Image-left, then image-right, then image-left.
2. **Cells are unequal, and unequal by different amounts each row.**
   Roughly 45/55, then 55/40, then 47/53 — not a repeated 50/50.
3. **Row heights vary.** A level grid of identical blocks is the failure
   mode these references exist to prevent.
4. **A large numeral can anchor a row** (01 / 02 / 03), sitting above the
   heading in ink, sized well beyond the heading.
5. **A card row can be staggered** — different heights and widths across
   the row, with any controls sitting inside the row rather than above it.
6. **Closing banner**: full width, heading on one side, pill action on the
   far side.
7. Section grounds alternate between white and a warm tint, which is
   already design model §1's white / `--paper` alternation.

## This must survive on mobile

The owner's caption was explicit: this is the asymmetric model **for the
mobile version**. The usual failure is that every row collapses into one
full-width stacked column at the mobile breakpoint and the rhythm is lost.

At phone width the rows stay **two unequal cells side by side**, alternating
which side is wide — as the coach screen shows. A row may collapse to a
single column only when its content genuinely cannot survive the narrower
cell, and then it is a deliberate exception, not the default.

See design model §14 for the rules, and §1/§3/§4 for what overrides these
references (white dominance, no invented data, reserved image slots).
