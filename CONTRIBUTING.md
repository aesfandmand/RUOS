# Contributing to RUOS

RUOS is maintained as a canonical, reviewable operating-system repository. Changes should be small enough to review, testable, and traceable to an issue or decision.

## Development workflow

1. Create or reference an Issue describing the change and acceptance criteria.
2. Create a feature/fix/chore branch from `main`.
3. Make the smallest coherent change.
4. Run the full test suite locally:

```bash
python -m pip install -e . pytest
pytest -q
```

5. For Website Engine changes, run a clean production build:

```bash
ruos build structures
```

6. Open a Pull Request to `main` and complete the PR checklist.
7. Merge only after CI passes and review comments are resolved.

## Branch naming

Use one of these prefixes:

- `feat/` for capabilities
- `fix/` for defects
- `chore/` for maintenance/governance
- `docs/` for documentation-only changes
- `test/` for test coverage
- `refactor/` for behavior-preserving structural changes

## Definition of Done

A change is done only when all applicable conditions are true:

- tests are added or updated for behavior changes;
- all tests pass on supported Python versions;
- production build passes when Website Engine output is affected;
- canonical YAML/JSON/spec contracts remain valid;
- Persian-first and RTL requirements are preserved where applicable;
- no secrets, generated caches, or local artifacts are committed;
- documentation is updated when interfaces, architecture, or workflows change;
- CI passes and review feedback is resolved.

## Commit convention

Prefer Conventional Commit style, for example:

- `feat(engine): add page-spec validation`
- `fix(qa): reject missing SEO metadata`
- `test(compiler): cover deterministic rebuild`
- `docs(governance): define canonical layers`

## Canonical repository rules

`main` is the source of truth. ZIP files and exported build artifacts are snapshots only. Do not introduce a second authoritative copy of a rule, schema, project decision, or version record without explicitly documenting its relationship to the canonical source.

## Pull Request policy

Direct pushes to `main` should be avoided. Repository settings should require:

- Pull Request before merge;
- successful `RUOS Engine CI` checks;
- resolved review conversations;
- at least one approving review when more than one maintainer is available;
- no force-pushes to `main`.

These repository-level protections must be enforced in GitHub settings in addition to this document.
