# Assistant Interoperability Protocol

Status: **BLOCKING CONTRACT**
Version: 1.0.0

This protocol makes RUOS usable by ChatGPT, Claude, Gemini, Codex, IDE agents, CI workers and human teams without relying on hidden conversation memory.

## Standard entry sequence

Every assistant must read, in order:

1. `00-governance/UNIVERSAL_ENGINE_CONSTITUTION.md`
2. `projects/<project-id>/project.yaml`
3. the project's active decision index
4. the project's locked baseline registry
5. relevant engine and page contracts
6. current CI and audit status

## Standard write sequence

When the owner approves a new fact or correction, the assistant must:

1. create or update a structured decision record;
2. mark older conflicting records as superseded;
3. update affected project manifests/contracts;
4. add or update tests where the rule can be mechanically checked;
5. open a pull request or commit through the repository workflow;
6. report exact paths, commit SHA and unresolved gaps.

## Portable output requirement

Assistant instructions must be stored in plain Markdown, YAML or JSON. Critical behavior may not exist only in a vendor-specific prompt, memory feature or chat transcript.

Vendor-specific adapter files may summarize the protocol, but they may not override it.

## Decision record schema

Each durable decision record must contain:

- `id`
- `project_id` or `scope: core`
- `date`
- `status`
- `owner_approved`
- `decision`
- `reason`
- `affected_paths`
- `supersedes`
- `evidence`
- `enforcement`

## Status values

- `proposed`
- `approved`
- `locked`
- `superseded`
- `rejected`

Only `approved` and `locked` decisions are active.

## No silent divergence

An assistant must not silently reinterpret a locked decision. Any proposed exception requires a new decision record and explicit owner approval.

## Context handoff

At the end of material work, the assistant must leave a repository handoff containing:

- completed changes;
- active branch/PR/commit;
- test and CI status;
- unresolved blockers;
- next safe action.

This handoff is the continuation point for the next assistant.
