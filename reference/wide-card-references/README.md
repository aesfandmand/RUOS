# Wide card references — owner-supplied

Sent by the owner on 2026-08-12 as the model for **the desktop card, and
the full-width card on mobile**. Distinct from
`reference/mobile-card-references/`, which covers the compact 2-up cards in
a mobile grid. Read the images before designing; this table is an index,
not a substitute.

| File | What it is | What to take from it |
|---|---|---|
| `01-inset-photo-two-tone-caption.jpeg` | Rounded square card, photo on top, caption below | The photo is **inset** — it sits inside the card's padding with its own smaller radius, floating on the white, rather than bleeding to the edge. A small grey uppercase label above a two-tone sentence where the emphasis words are ink-dark and the rest is muted. |
| `02-photo-overlay-action-plus-stat-row.jpeg` | Trail card: photo with an overlay bar, then a data block | Title + subtitle sitting **on** the photo over a bottom gradient, with the primary action as a translucent pill beside them. Below the photo: a qualifier line, a hairline rule, then a row of 3 stats as `value` over `label`, and a square thumbnail parked on the far side. |
| `03-tag-chips-rating-carousel-cta.jpeg` | Book/adventure card | Tag chips and a rating floating over the top corners of the photo, carousel dots at the photo's bottom edge, then title + an outline pill on the same line, a 3-line description, a small meta line, and a full-width black pill CTA. |

## The pattern

1. **Two photo treatments, chosen deliberately.** Inset (ref 01) reads
   quiet and editorial; full-bleed with an overlay (refs 02, 03) reads
   like a product. Do not mix both in one row.
2. **The photo carries chrome.** Tags, rating, carousel dots and even the
   title/action bar sit over the image, on a gradient scrim — never in the
   text area below.
3. **The data block under the photo is layered**, not one paragraph:
   qualifier → hairline rule → stat row → description → meta → action.
4. **Stats are `value` over `label`**, value in ink at ~2x the label, label
   muted and small. Three across.
5. **A hairline rule separates the identity from the numbers.**
6. **The action is either an overlay pill on the photo, or a full-width
   pill at the very bottom.** Both appear; a bare text link does not.
7. **Two-tone sentence** (ref 01): the sentence is muted, the words that
   carry the claim are ink-dark and heavier. This is already the house
   heading signature — design model §2.
8. **A secondary square/round thumbnail can park at the end of the stat
   row** (ref 02's route map) to hold a diagram.

## Mapping to Red Umbrella's real content

| Reference element | Our real equivalent | Data source |
|---|---|---|
| Title + subtitle over the photo | Structure name + family | structure registry |
| Overlay action pill | «درخواست استعلام» / «مشاهده مشخصات» | — |
| 3-stat row | Real registry attributes: ابعاد · جهت · محیط نصب | `_specs()` |
| Qualifier line above the rule | Structure family, or install context | structure registry |
| Square thumbnail beside the stats | The CSS dimension diagram we already draw | `_diagram()` |
| Tag chips over the photo | Context / orientation labels | registry `context`, `orientation` |
| Carousel dots | Real Didanshow photos for that structure | `media/structures/<ID>/` |
| Star rating | **Do not use.** No verified rating exists and one will not be invented | — |

## Rules that override these

- **§1 colour.** Ref 03's black CTA pill becomes `--red`; ref 02's dark
  overlay is acceptable *on a photo* (it is a scrim, not a flat-black
  section) but must not become a dark card body.
- **§3 content.** Any stat with no registry value gets a tagged
  placeholder, never a plausible-looking number.
- **§4 images.** The slot is reserved even when the photo is missing — for
  the overlay treatments that means the scrim and its text still lay out.
