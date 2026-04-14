# Project State Role Definition v1

## Forced Decision

Decision A is adopted:

```text
lifecycle_state = 主状态 / truth state
stage_id = 从状态 / UI stage projection
```

## Role Definitions

| Field | Role | Meaning |
| --- | --- | --- |
| `lifecycle_state` | 主状态 | business truth for project lifecycle, validation, import semantics, and workflow gates |
| `stage_id` | 从状态 | Odoo native UI stage and kanban/status projection derived from lifecycle or system signals |
| `legacy_state` | source trace | raw legacy `STATE`, not a normalized status |
| `legacy_stage_id` / `legacy_stage_name` | source trace | raw legacy stage values, not current-stage truth |
| `sc_execution_state` | sub-state | execution readiness/progress state, not project lifecycle truth |

## Rationale

`lifecycle_state` is already registered in `ScStateMachine.PROJECT`, has legal
transitions, drives lifecycle guard methods, and replaces the native `stage_id`
statusbar in the project form header. That makes it the only suitable truth
layer.

`stage_id` remains necessary because Odoo native project UX expects stages and
kanban/status projections. It should not become the business truth because it is
also subject to Odoo defaults and UI movement semantics.

## Current Implementation Gap

Current code already syncs lifecycle changes to `stage_id`. It also contains
stage-only write validation that blocks movement beyond derived business
signals. Governance target is stricter:

- lifecycle may update stage;
- stage must not reverse-update lifecycle;
- stage drag must not be treated as business lifecycle truth.

No code is changed in this batch.
