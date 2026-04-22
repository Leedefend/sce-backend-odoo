# Frontend Pending Project Context Screen V1

## Scope

This screen covers one remaining frontend behavior path:

- `frontend/apps/web/src/pages/ContractFormPage.vue`
  - after create success for `project.project`, frontend calls
    `setPendingProjectContext(...)`
  - the payload currently hardcodes:
    - `stage: "initiated"`
    - `stage_label: "已立项"`
    - `milestone: ""`
    - `milestone_label: ""`
    - `status: "active"`

The downstream consumer is:

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
  - `loadLifecycleEntry()` consumes `consumePendingProjectContext()`
  - if present, it injects `{ project_context: pendingProjectContext }` into
    `project.dashboard.enter`

## Current Fact

Frontend is not just carrying the new `project_id`.

Frontend is fabricating a dashboard bootstrap context that includes project
execution semantics and status semantics before backend has supplied them.

This means the first dashboard load after create may depend on frontend-owned
business words instead of backend-owned project facts.

## Ownership Judgment

### `project_id` and `project_name`

These can be treated as local navigation carry values.

Reason:
- they are direct create result facts already known in frontend
- they identify which project the dashboard should open

### `stage`, `stage_label`, `milestone`, `milestone_label`, `status`

These do **not** belong to frontend orchestration.

Reason:
- they are business facts or fact-derived labels
- they affect what the project dashboard presents as current execution context
- frontend is currently inventing them without a backend contract

Classification:
- `requires_backend_semantic_supply`

## Backend Sub-Layer Decision

Primary owner:
- `business-fact layer`

Reason:
- current execution stage / milestone / status are domain facts of the newly
  created project
- frontend cannot legally infer them from “create just happened”

Optional follow-up owner:
- `scene-orchestration layer`

Reason:
- once business facts exist, backend may still choose to wrap them into a
  dashboard-ready bootstrap envelope for the first entry experience

## Why Frontend Must Stop Owning This

The current frontend path hardcodes:

- `initiated`
- `已立项`
- `active`

This violates the agreed boundary:

- frontend is not a business-fact author
- missing facts must be supplied by backend
- project execution stage and record/document status must not be guessed in page
  code

## Minimum Correct Direction

After create success, frontend should only rely on one of these backend-owned
inputs:

### Option A: create response includes dashboard bootstrap context

Example shape:

```json
{
  "id": 123,
  "post_create_context": {
    "project_context": {
      "project_id": 123,
      "project_name": "示例项目",
      "execution_stage": "initiated",
      "execution_stage_label": "已立项",
      "milestone": "",
      "milestone_label": "",
      "status": "active"
    }
  }
}
```

### Option B: dashboard entry intent resolves context from `project_id` only

Example:

- frontend passes only `project_id`
- backend `project.dashboard.enter` resolves execution stage / milestone /
  status from authoritative facts

This option is cleaner because frontend no longer needs any pending semantic
context cache at all.

## Recommended Implementation Order

1. backend screen/implement the authoritative post-create project context supply
2. frontend remove hardcoded stage/status payload from `setPendingProjectContext`
3. if possible, reduce pending context to `project_id` only or delete the
   pending context helper entirely
4. verify the first dashboard load after create still opens the correct project
   and shows backend-supplied context

## Decision Summary

This remaining frontend special-case is invalid.

Summary:
- `project_id` carry: frontend may carry
- project execution stage / milestone / status carry: backend must supply
- current `setPendingProjectContext(...)` semantic payload is a backend fact
  leak into frontend and should be removed after backend supply lands
