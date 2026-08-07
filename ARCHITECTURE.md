# RUOS Canonical Architecture Map

This document explains the current top-level repository layers and resolves the meaning of repeated numeric prefixes. Numeric prefixes are grouping labels, not a strict unique sequence.

## Runtime and executable layers

- `src/ruos/` — executable Python package and compiler/runtime implementation.
- `pages/` — compile-ready page specifications consumed by the engine.
- `tests/` — automated contract, regression, engine, research, quality and build tests.
- `.github/workflows/` — repository CI automation.

## Canonical operating-system layers

| Path | Role | Authority |
| --- | --- | --- |
| `02-knowledge/` | Project knowledge, decisions and promoted knowledge records | Canonical knowledge layer |
| `03-engines/` | Engine contracts and engine-level specifications | Canonical engine contracts |
| `04-templates/` | Schemas and reusable record templates | Canonical template/schema layer |
| `05-rules/` | Global and domain rules | Canonical rule layer |
| `06-workflows/` | Operating and migration workflows | Canonical workflow layer |
| `11-knowledge-migration/` | Migration-stage records and source-to-canonical transformation artifacts | Migration workspace |
| `11-projects/` | Project-scoped operational workspace | Project workspace |
| `12-gcera-dsl/` | GCERA domain language and entity/journey/page contracts | Canonical DSL |
| `12-versions/` | Version records and repository release history artifacts | Versioning workspace |
| `13-canonical-repository/` | Canonical repository contracts, UID/path conventions and governance specifications | Repository governance authority |
| `14-technology-intelligence-registry/` | Evaluated technology/library intelligence | Technology registry |
| `15-website-studio-engine/` | Website Studio design/production engine specifications and assets | Website Studio specification layer |

## Why prefixes repeat

`11-*` and `12-*` intentionally represent families at the same architectural stage rather than a single ordinal filesystem sequence. They must not be interpreted as duplicate authorities.

- `11-*` = project/migration workspaces.
- `12-*` = formalized DSL/version control artifacts.

If a future refactor renumbers these directories, it must be handled as a repository migration with explicit path aliases or migration records. Renaming directories casually is prohibited because internal references may depend on canonical paths.

## Source-of-truth precedence

When sources conflict, use this precedence unless a more specific repository contract states otherwise:

1. Explicit locked/project decision in canonical knowledge.
2. Canonical rules and repository governance contracts.
3. Engine/schema/workflow contracts.
4. Project workspace implementation records.
5. Generated output, ZIP exports and snapshots.

Generated output never becomes authoritative merely because it is newer.

## Change control

Changes affecting canonical paths, schemas, rule precedence, DSL contracts, build gates, or project-wide behavior require:

- an Issue or decision record;
- a branch and Pull Request;
- passing CI;
- relevant tests or validation evidence;
- documentation updates when the contract changes.

See `CONTRIBUTING.md` for the operational workflow.
