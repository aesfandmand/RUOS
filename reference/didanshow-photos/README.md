# Didanshow reference photos

Real, non-AI photographs of real OOH structures installed in real Iranian
streets, supplied directly by the project owner on 2026-08-10. The owner
confirmed Didanshow (the "دیده‌شو" watermark visible on every photo) is
their own company (Tehran office, owned by مرتضی محرمی) — these are not
third-party stock and are authorized for use in building Chatreghermez
(چتر قرمز) product pages.

**Important distinction to preserve in any page copy:** the *structure and
photograph* belong to Didanshow. The *ad creative shown on the board face*
(Signal, Lux, Mammut, Gerad, SAIPA, Benelli, etc.) belongs to Didanshow's
own advertising clients — not to Chatreghermez. When these photos are used
on a Chatreghermez page, caption them as real installation samples from
the Didanshow network (e.g. "نمونه نصب واقعی"), never as Chatreghermez's
own client work — that would misattribute someone else's project.

## `raw/` contains 4 unrelated files — do not use

Verified 2026-08-14 by opening every file in `raw/` (26 total). Four of them
are **not** Didanshow photos at all — they're unrelated stock UI mockups
(furniture/real-estate site templates, a 3D-coverflow motion reference) that
ended up in this folder, most likely swept in by upload-time proximity, not
content:

- `0c89f9db-IMG_3972.jpeg`, `3a0ebc46-IMG_3951.jpeg`, `e0b87cca-IMG_3950.jpeg`
  — furniture/real-estate website mockups, no OOH structure in them.
- `72d69139-IMG_3952.jpeg` — a 3D coverflow card-carousel UI reference
  (Vision-Pro-style), not a structure photo.

The remaining 22 files are real. **Per-file structure assignment, verified
by visually matching mount hardware against
`reference/structure-diagrams/strabord-4x3-exploded-assembly.jpg` /
`strabord-4x3-dimensions.jpg`** (owner-supplied 2026-08-14):

| Structure | Photos now in `media/structures/<ID>/` | Visual basis |
|---|---|---|
| STR-002 بیلبورد افقی ۶×۱۲ | `227d9c74`, `4518b3d3`, `679278a1` | large wall-mounted panel over a boulevard |
| STR-004 استرابورد عمودی ۴×۳ | `c421e90b`, `ca7f07a5`, `64f4f9d4` ("ایمنی" sign), `64e54100` (concert ad), `563eea79` (تپسی‌فود) — all owner-confirmed | pole runs through the **center** of the panel |
| STR-006 لایت‌باکس عمودی ۱۸۰×۱۲۰ | `54d2f9ad`, `999f279b`, `f0cb630a`, `ca75d1fb` (فرش رهسپار, owner-confirmed: outdoor vertical light-box) | single black pedestal base, evenly backlit face |
| STR-008 برایت‌بورد عمودی ۳×۲ | *(none)* | the side-pole rule that first put `563eea79` here turned out wrong per the owner — see correction round 5 |
| STR-009 برایت‌بورد افقی (owner: "یک‌طرفه") | `78fbc9da`, `dbee3309`, `73e8b50d`, `61a22166`, `a8f9ffd9`, `fe0c0e1d` | owner confirmed 2026-08-14 — all six (pole- and wall-bracket-mounted alike) are the same product line, برایت‌بورد افقی یک‌طرفه |
| STR-015 لایت‌باکس دیواری ایندور | `e8718dad`, `3e6bec7b`, `db2b2c11`, `aacfeca6`, `8f4b829e` | (unchanged from earlier session) |

Every real photo in `raw/` (all 22, plus the owner's 2026-08-14 "ایمنی"
upload) is now assigned to a structure. Nothing left unfiled.

**No structure currently has STR-003 (استرابورد افقی ۵×۳) photos** — see
correction round 3 below.

**Correction history, 2026-08-14 (three rounds, in order):**
1. `563eea79`/`73e8b50d` were first filed under STR-008, on the theory the
   side rods visible in the panel frame were floodlight fixtures.
2. The owner's exploded-assembly diagram showed those rods are strut-mount
   hardware, common to strabord too — both photos were moved to STR-004.
3. The owner then gave the real distinguishing rule: برایت‌بورد's pole
   sits at one *side* of the panel; استرابورد's pole runs through the
   *center*. Re-checked against this rule: `563eea79`/`73e8b50d` are
   side-pole (→ STR-008), `c421e90b`/`ca7f07a5` are center-pole (→ STR-004,
   confirmed).
4. **The owner then explicitly grouped five photos together as one
   product — برایت‌بورد افقی یک‌طرفه — including the three Mammut
   wall-bracket shots that had been filed under STR-003 (استرابورد افقی) on
   a mount-type guess.** That guess was wrong: `61a22166`, `a8f9ffd9`,
   `fe0c0e1d` moved from STR-003 to STR-009, alongside `78fbc9da`,
   `dbee3309`, and `73e8b50d` (which also moved out of STR-008, since it's
   the same product as the others in this group). **STR-003 now has no
   photos at all — don't assume the earlier Mammut/STR-003 pairing is still
   valid anywhere else in the repo (e.g. old commit messages, drafts).**

**Do not re-derive any of this from mount silhouette alone** — round 4
showed that pole-vs-wall-bracket mounting is not a reliable signal for
product family; the owner's own product grouping overrides it.

5. **Round 5:** the owner confirmed `64e54100` (concert ad, wall-mounted)
   and `563eea79` (تپسی‌فود — round 3 had called this side-pole برایت‌بورد,
   which the owner corrected) are both استرابورد عمودی → STR-004. And
   `ca75d1fb` (فرش رهسپار, light-box + marquee topper) is لایت‌باکس عمودی
   اوت‌دور → STR-006 (the marquee topper doesn't make it a separate
   لایت‌برد product). **STR-008 (برایت‌بورد عمودی) now has zero photos** —
   the center-vs-side-pole rule from round 3 correctly separated STR-004
   from STR-009's product line, but did not reliably separate STR-004 from
   STR-008; go by the owner's direct call per-photo, not that rule alone,
   for any future برایت‌بورد‌ی‌عمودی candidate.

**Still open:**
- STR-009 vs STR-010 (5×3 vs 7×3): all six STR-009 photos are filed on a
  visual aspect-ratio estimate, not a measured fact — still needs owner
  confirmation of exact width.
- Photo counts per structure as of now: STR-002 (3), STR-004 (5), STR-006
  (4), STR-008 (0), STR-009 (6), STR-015 (5). STR-004, STR-009, and STR-015
  clear the 5-photo threshold (`_MAX_HERO_SLIDES=3` + gallery minimum 2)
  that makes the 3D coverflow gallery block appear on a page — STR-006 is
  one photo short.

## `raw/`

The unmodified uploads, kept under their original upload filenames. Those
filenames are **not** structure IDs — they're just the upload tool's
names. The per-file table above is now the source of truth for which photo
shows which structure; don't re-derive it from filename/order.
