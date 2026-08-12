# Red surface finish — owner-supplied

Sent by the owner on 2026-08-12 as the mandatory finish for red **wherever
red is used**, in mobile mockups and a desktop hero for a "Creative Agency"
concept. Read the image before touching any red surface.

## The instruction, verbatim

> اگر رنگ قرمز در جایی استفاده میشه مطابق با این نمونه باشه — مات نباشه،
> تخت نباشه، شارپ و براق باشه، حتما تکسچر داشته باشه.

Not matte, not flat. Sharp, glossy, and it must carry a texture.

## What the reference shows

- The desktop hero's background and the mobile "Read More" pill and the
  "567+" stat badge are all the same family of finish: a fine, tight
  **repeating diagonal/vertical ribbing** (visible as thin parallel lines
  across the red), a **bright specular highlight** in the upper-left area
  that fades out (not a hard edge — a soft bloom), and a **darker edge**
  toward the lower-right, giving the surface real dimension instead of one
  flat hex value.
- It reads as brushed/ribbed metal or glossy fabric under a studio light,
  not a painted flat colour and not a smooth UI gradient.

## House implementation

Design model §1 records the exact recipe as `--red-gloss` /
`--red-gloss-shadow` in `blocks/_tokens/style.css`: a soft radial highlight
+ a tight repeating diagonal stripe for the ribbing + a subtle vertical
tone shift from a lighter red through `--red` to `--red-deep`, plus an inset
highlight/shadow pair on the box-shadow for the physical edge. No image
asset — the whole thing is CSS gradients, so it stays deterministic and
needs no vendoring.

## Where this does and does not apply

This is a **surface finish**, not permission to use red as a mood
background. Design model §1's separate rule against a "dark-radial-gradient
stage" is about using red/black as a whole section's dramatic backdrop
(what the owner rejected early in the project) — a different thing from
giving an actual red UI surface (a button, the closing CTA band, a pill)
this glossy, textured finish instead of a flat fill. Both rules hold at
once: red stays an accent and the single closing band, and wherever it
appears as a filled surface, it now uses this finish instead of a flat hex.
