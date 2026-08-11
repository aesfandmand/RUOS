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

## 3. Layout comes from the owner's references

Mobile and desktop composition follow the reference images and videos the
owner supplied, not the assistant's taste. When a reference exists, match it
— go and look at the frames rather than approximating from memory. Ask for
the reference if you cannot find it.

## 4. Verify in a real browser

Every visual or motion change is checked with Playwright before it is
reported as done — both breakpoints, console errors captured, and the actual
computed values measured rather than eyeballed from a screenshot. Chromium
is preinstalled; do not run `playwright install`.

"It should work" is not a result. Neither is a screenshot that you did not
read.

## 5. Commit as you go

The owner's standing instruction: commit and push each decision as it lands,
so a lost container never costs the work twice. Branch: `claude/block-library`.

## 6. Scope

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
