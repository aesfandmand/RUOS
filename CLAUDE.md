# RUOS — instructions for any assistant working in this repository

Read this before changing anything. It is short on purpose; the detail lives
in the linked rule files, which are the source of record.

## 1. The navigation is LOCKED

The site header (desktop mega-menu + mobile glass drawer) and the mobile
bottom nav were approved by the owner on 2026-08-11 and frozen **for the
rest of the project**.

> They are identical on every page and they do not change again. No page may
> restyle, extend, shorten, recolour or "improve" them.

Enforced by `tests/test_navigation_lock.py`. **If it fails, you edited a
locked file — revert, do not update the test.** The one procedure allowed to
move those hashes is in `05-rules/website/navigation-lock.md` and it starts
with the owner's explicit approval for that specific change. A request to
work on some page is never approval to touch the nav.

Locked files:

```
blocks/site-header/{markup.html,style.css,behavior.js}
blocks/bottom-nav/{markup.html,style.css,behavior.js}
```

To review the nav (or show it to the owner):
`python3 tools/build_nav_preview.py out.html`

## 1a. The Structure Detail page archetype is LOCKED

`pages/blocks/straboard.json` — the full 19-block page, approved on
2026-08-14 across mobile and desktop — is the **mandatory template for
every other structure's page**: same blocks, same order, same
markup/CSS/behaviour. Only the data changes per structure.

Enforced by `tests/test_structure_page_lock.py` and, on every critique run,
`page_critic.py`'s `"structure-archetype"` discipline (a hash mismatch is a
blocker). **If it fails, you edited a locked file — revert, do not update
the test.** The procedure to change it — same shape as the nav lock — is in
`05-rules/website/structure-page-lock.md`, which also has the exact steps
for building the *next* structure's page (copy `straboard.json`, replace
data, never touch a locked block file).

## 2. Design rules

`05-rules/website/red-umbrella-design-model-v1.md` is the owner-approved
design model: palette and how to apply it, typography, content policy,
image policy, layout sources, motion budget, standing SEO/marketing goals,
and the approved library list. It is in force. Do not re-derive these
decisions from taste — they were argued out and paid for.

The three that get violated most often:

- **White dominates.** No flat-black sections, no red gradients, no dark
  "stage" backgrounds. Charcoal (`--ink-soft`) is an accent band, at most
  once per page. Red as a full background is only the closing CTA.
- **No pink.** `--red-soft` was removed from the palette by owner decision.
  Icon badges sit on `--paper-2`.
- **The page always ships.** When registry data is thin, emit a *tagged*
  placeholder (`"placeholder": true`) and build the complete page. Do not
  refuse to build, and do not silently invent a number and present it as
  verified.

## 3. Structure pages build themselves from the registry

`ruos generate` composes any Structure Detail page — hero, spec sheet, FAQ,
lead form, plus real photos/siblings/services when the registry has them —
straight from `structure-page-registry-v2.1.yaml`, no hand-authored JSON
required. See design model §18. A hand-authored `pages/blocks/<slug>.json`
(a real owner content brief, like straboard's) still always wins over the
auto-build; this only fills the gap for structures nobody has written one
for yet. It never fabricates the rich marketing/engineering sections a
brief would carry — see §18 for exactly which sections that means.

## 4. The rich sections can be drafted from real research, never invented

`python3 -m ruos.cli content-brief <structure-id>` runs real search + fetch
(Iranian and international OOH sources) for `numbered-features`/
`parts-zigzag`/`checklist-section`; `content-review --fill-gaps` fills any
slot research couldn't cover with tagged Lorem Ipsum and validates every
real claim carries a citation. See design model §19 and
`05-rules/website/content-voice-v1.md`. The human edit pass that replaces
placeholders with real copy happens before WordPress upload — not before
`ruos generate` composes the page.

## 5. Every page is a draft until the owner approves it, both breakpoints

`python3 tools/build_draft_preview.py <structure-id>` builds the
always-complete page (§20 — real content where it exists, tagged Lorem
Ipsum everywhere it doesn't, never an omitted section) and screenshots
**both mobile and desktop**. Show both to the owner. A page's JSON only
gets written to `pages/blocks/<slug>.json` and committed after the owner
explicitly approves it here — that commit is also what removes it from
the `ruos next`/`generate` build queue. There is no CLI "approve" command
on purpose: approval is a conversation, never a script flag.

## 6. Review every page with the critic before calling it done

`python3 -m ruos.cli critique <slug> --spec-root pages/blocks` runs an
automated art/creative-director pass — ten real, code-based checks against
the actually-rendered page (colour, navigation, motion, icons, content
honesty, images, rhythm, accessibility, SEO/schema, performance). See design
model §17 for what each checks and why it is not the older
`design_critic.py`/`virtual_studio.py`/`qa.py` stack. A `reject` means a
locked-nav violation; anything else is a real, actionable finding, not
noise — it does not grade a page down for no reason, so trust what it says.

## 7. Layout comes from the owner's references

Mobile and desktop composition follow the reference images and videos the
owner supplied, not the assistant's taste. When a reference exists, match it
— go and look at the frames rather than approximating from memory. Ask for
the reference if you cannot find it.

## 8. Verify in a real browser

Every visual or motion change is checked with Playwright before it is
reported as done — both breakpoints, console errors captured, and the actual
computed values measured rather than eyeballed from a screenshot. Chromium
is preinstalled; do not run `playwright install`. Full-page screenshots have
their own artifacts (see design model §20) — don't chase them as if they
were real rendering bugs without checking first.

"It should work" is not a result. Neither is a screenshot that you did not
read.

## 9. Commit as you go

The owner's standing instruction: commit and push each decision as it lands,
so a lost container never costs the work twice. Branch: `claude/block-library`.

## 10. Scope

Do what was asked. Do not rebuild or regenerate pages while working on a
component, and do not widen the task because something nearby looks
improvable. If you think something else is wrong, say so in a sentence and
keep to the ask.

---

## Stack

Vanilla HTML/CSS/JS, generated deterministically from a block library. No
framework, no build step in the output, no CDN at runtime — every dependency
is vendored into the repo with its licence.

| What | Where |
|---|---|
| Blocks | `blocks/<id>/{block.json,markup.html,style.css,behavior.js,assets/}` |
| Template language | `src/ruos/block_template.py` |
| Composer (shape rules, anti-repetition) | `src/ruos/block_composer.py` |
| Page document assembly | `src/ruos/block_page.py` |
| Registries (structures, services, personas) | `src/ruos/*_registry.py` |
| Rules of record | `05-rules/` |
| Repeatable tooling | `tools/` |

Tests: `python3 -m pytest -q` from the repo root.
