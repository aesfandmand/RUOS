# RUOS Universal Engine Constitution

Status: **SOURCE OF TRUTH**
Owner-approved: 2026-08-06

## Mission

RUOS is not a Red Umbrella-only repository. It is a reusable operating and website-intelligence engine for all current and future projects owned by the organization.

Red Umbrella is the first fully populated project workspace and reference implementation, not the hard-coded identity of the engine.

## Assistant neutrality

RUOS must be usable and extendable by any capable assistant, agent, IDE, CI worker or human contributor. No rule may depend on private memory, an undocumented chat state, or behavior unique to ChatGPT.

Every contributor must be able to discover the same source of truth from repository files and machine-readable contracts.

## Living-source rule

Every owner-approved decision, correction, prohibition, baseline, reference, architecture change, content rule, voice rule, QA finding and process improvement must be persisted in GitHub during the same work cycle.

A decision that exists only in chat is provisional and must not be treated as durable project knowledge.

## Separation of concerns

RUOS consists of:

1. **Core engine** — project-neutral schemas, gates, workflows, adapters and validators.
2. **Project workspaces** — project-specific brand, architecture, content, evidence, baselines and artifacts.
3. **Assistant adapters** — concise entry contracts for different assistants and execution environments.
4. **Living decision registry** — append-only owner decisions with supersession links.
5. **Canonical artifacts** — immutable approved baselines with checksums.

## No hard-coding

Core code and schemas must not hard-code Red Umbrella names, routes, colors, tone, personas or file paths. Project-specific values must be loaded from a project manifest and workspace.

## Precedence

When sources conflict, precedence is:

1. latest explicit owner-approved decision;
2. locked project constitution and baseline contracts;
3. current project manifest and architecture;
4. reusable core defaults;
5. historical snapshots.

Superseded decisions remain auditable but cannot remain active.

## Required behavior for every contributor

Before changing or generating a project output, a contributor must:

1. load this constitution;
2. load the target project manifest;
3. load active locked decisions and baselines;
4. declare intended changes and prohibited regressions;
5. run blocking gates;
6. write new approved knowledge back to GitHub;
7. produce a diff and audit record.

## Failure policy

If repository state is incomplete, contradictory, stale or missing the approved baseline, production stops. The contributor must report the missing source rather than inventing it.
