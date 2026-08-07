# Baseline floor vs aspirational quality

Status: **LOCKED OWNER DECISION**
Date: 2026-08-07

## Decision

The approved `services-urban-investment-final-v16.html` baseline package is a **non-regression floor**, not the target quality ceiling.

RUOS must never interpret V16 as "copy this quality" or "stop at this level". Its role is only to prevent future pages from becoming weaker than the approved baseline in interaction, motion, mobile behavior, typography, layout integrity, content completeness, and overall execution quality.

## Aspirational target

For new digital-experience builds, the creative target is materially higher: contemporary award-level web experiences comparable in ambition, craft, motion, composition and interaction quality to owner-approved Awwwards/Dribbble references.

The engine must therefore use two distinct reference layers:

1. **Baseline / Floor** — the project-approved Gold Master that defines what must not regress.
2. **Aspirational / Ceiling-seeking references** — live-researched, owner-approved examples used to push the new page beyond the baseline.

A build is not successful merely because it passes V16. It must also show evidence of creative advancement appropriate to the page's intent.

## Required build behavior

Before every page build, RUOS must:

- load and verify the project baseline package;
- load current project-specific design DNA and voice rules;
- run live research for relevant high-quality references and libraries;
- translate references into explicit decisions for typography, composition, scroll narrative, motion, interaction, imagery, information hierarchy and conversion strategy;
- compare viable technology/library options and select the best fit for the page objective;
- produce a page that is at least non-regressive relative to the baseline and intentionally aims above it;
- document what was improved beyond the baseline.

## Baseline package role

The baseline package may contain:

- `page.html`
- `assets/`
- `manifest.json`
- `design-dna.json`
- `motion.json`
- `voice.json`
- `capabilities.json`
- `knowledge-graph.json`
- `screenshots/`

These files describe the minimum inherited quality and project context. They do not replace live research or aspirational references.

## Failure conditions

Reject a build when any of these are true:

- it is visually or interactively weaker than the locked baseline;
- it merely reproduces the baseline without page-specific creative advancement;
- it skips live reference/library research when such research is available and relevant;
- it falls back to plain raw HTML as the creative strategy;
- it cannot explain why chosen libraries and interaction patterns are appropriate to the page objective and conversion hypothesis.
