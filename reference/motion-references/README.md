# Motion & layout references — owner-supplied

Two screen recordings the owner sent on 2026-08-12 as examples of layout and
**soft motion** (موشن نرم). The videos are ~30MB each and are not committed;
these are representative frames pulled from them. The originals are the
owner's, re-request them if a frame is not enough.

| Source | Frames here | What it is |
|---|---|---|
| `ScreenRecording_08102026_201101_1.mov` (15s) | `01`, `02`, `03` | A "Volcanoes" full-screen slider, desktop |
| `ScreenRecording_08102026_164546_1.mp4` (22s) | `04`, `05` | Dribbble playing "Xurya — Manufacture Landing Page" |

## Slider (frames 01–03)

Layout, per slide:

- Left column: a small eyebrow with a red dash rule (`ICELAND —`), then a
  **huge headline in red** (`KRAFLA`), then a data block of three
  `label / value` rows (Latitude, Longitude, Elevation) over a faint
  outline map.
- Right: a large photo panel, with a **small inset photo overlapping its
  bottom-left corner** — depth without any 3D.
- A **large index numeral** (`01`) sitting on the photo, bottom-right.
- A **red bar previewing the next item** (`CHILE  02`) at the photo's
  bottom-right corner.
- Two small circular buttons bottom-left as the control.

Motion — frame `02` is the transition caught mid-flight:

- The **photo panel slides vertically**: the outgoing image travels up and
  out while the incoming one arrives from below, both visible at once.
- The **type does not travel with it.** The headline and data block clear
  out and re-enter on their own timing.
- Long, eased, no bounce. This is what the owner means by *soft*.

## Landing page (frames 04–05)

- **Two-tone headings**, again: "We offer quality," in ink, "with the best
  materials and service" in muted. Second independent confirmation of the
  house signature (design model §2).
- A **6-cell feature grid that reveals in reading order** — in frame `04`
  the later cells are still faded. Staggered, never all at once.
- A **testimonial as an asymmetric split**: quote block on one side, photo
  on the other, unequal widths (§14).
- White ground, one accent colour, generous whitespace.

## Mapping to us

| Reference element | Our equivalent |
|---|---|
| Eyebrow + red dash | Already the house eyebrow (`.eyebrow::before`) |
| Huge red headline | Structure name — but see the override below |
| 3-row label/value data block | `_specs()`: ابعاد · جهت · محیط نصب |
| Faint outline map behind the data | Our CSS dimension diagram (`_diagram()`) |
| Inset photo over the panel corner | A second real Didanshow photo |
| Index numeral + next-item preview bar | Real position in a real structure list |
| Vertical panel slide | Swiper, already vendored |
| Staggered grid reveal | Motion/GSAP, already vendored |

## Overrides

- **§1 colour.** The slider sets a huge headline in red on white. Ours does
  not: red stays an accent and the closing CTA. A structure name is `--ink`
  with the house two-tone treatment; the red dash, the index numeral accent
  and the next-item bar are where red belongs here.
- **§8 3D scroll** still applies — this slider is a legitimate showcase
  moment, not licence to make every section a slider.
- **§3** — the index and any count must reflect the real number of
  structures, never a decorative figure.
