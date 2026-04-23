# Project member responsibility promotion rule v1

Status: FROZEN_BLOCKED  
Iteration: `ITER-2026-04-14-0030RF`

## Current Promotion Rule

```text
neutral carrier -> project.responsibility = blocked
```

Neutral carrier rows must not be promoted while `role_fact_status = missing`.

## Required Promotion Inputs

A future promotion task must provide at least one approved source:

- a verified legacy role source that maps `(legacy_member_id, legacy_project_id,
  legacy_user_ref)` to a target `role_key`;
- a business-approved default role rule with a named risk acceptor;
- a dedicated authority-path decision that explicitly accepts record-rule and
  visibility impact.

## Forbidden Shortcuts

- Do not assign a fixed default `role_key` for convenience.
- Do not make `project.responsibility.role_key` optional for migration.
- Do not use placeholder role values.
- Do not change record rules to make the migration pass.
- Do not infer responsibility from duplicate neutral membership evidence.

## Promotion Acceptance

Any future promotion batch must prove:

- source role evidence exists for each promoted row;
- target `role_key` is valid under the current selection;
- project/user identity is already mapped;
- rollback targets are generated;
- record-rule and project visibility impact are explicitly reviewed;
- neutral carrier rows remain traceable after promotion.
