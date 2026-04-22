# Backend Project Intake Input Chain Screen V1

## Problem

We already know `ContractFormPage` should stop inferring project intake
create-flow mode from:

- `model === "project.project"`
- `route.query.scene_key`
- `route.query.intake_mode`

But the backend governance layer cannot emit intake-specific `form_governance`
yet, because the intake scene identity does not currently reach the backend
mainline in the model-contract path.

## Current Fact

### Frontend caller

`ContractFormPage.loadContract()` does:

- prefer `loadActionContractRaw(actionId, ...)` when `actionId` exists
- otherwise fallback to `loadModelContractRaw(model, ...)`

For the model fallback, current request params are only:

- `op = "model"`
- `model`
- `view_type`
- `record_id`
- `render_profile`
- `contract_surface`
- `source_mode`

It does **not** send:

- `scene_key`
- `menu_xmlid`
- `menu_id`
- `intake_mode`

### Backend mainline

`ui.contract` / `load_contract` can already consume:

- `menu_id`
- `action_id`
- action context

Those values flow into:

- `ActionDispatcher`
- `PageAssembler`
- runtime context with:
  - `contract_action_id`
  - `contract_menu_id`

So the backend mainline already has a legal carrier for entry identity, but only
when the request uses action/menu-linked entry.

## Key Gap

Project intake entry currently reaches `/f/project.project/new` with route
query like:

- `scene_key=projects.intake`
- `menu_xmlid=smart_construction_core.menu_sc_project_initiation`

But `loadModelContractRaw(...)` drops those values before the request reaches
`ui.contract`.

Result:

- frontend knows the intake scene identity
- backend governance does not
- frontend starts inferring create-flow mode locally

## Ownership

Owner:
- backend entry/input chain

Primary sub-layer:
- `scene-orchestration layer`

Reason:
- the missing piece is not business fact of the project record
- the missing piece is transport of entry/scenario identity into the contract
  assembly chain

## Valid Fix Directions

### Direction A: extend model-contract request to carry entry identity

Allow `loadModelContractRaw(...)` and `ui.contract op=model` to pass:

- `menu_id` or `menu_xmlid`
- optional `scene_key`

Then backend governance can derive:

- this create form belongs to project intake scene

Pros:

- smallest behavioral change for current `/f/project.project/new` path

Cons:

- model-contract path becomes responsible for more entry semantics

### Direction B: make project intake form always open through action/menu entry

Instead of relying on bare model fallback, ensure intake form uses:

- `action_id` and/or `menu_id`

Then backend mainline already has the necessary entry carrier and can derive
intake identity without adding new model-path semantics.

Pros:

- cleaner ownership
- reuses existing backend entry-context machinery

Cons:

- requires ensuring intake route always carries resolvable action/menu identity

## Recommended Direction

Prefer `Direction B` if the intake route can reliably carry or resolve
`menu_id/action_id`.

Reason:

- backend mainline already treats action/menu as the legal entry carrier
- this avoids teaching bare model requests about scene-specific behavior
- it keeps contract governance dependent on entry semantics that already belong
  to orchestration

Fallback:

- use `Direction A` only if intake route cannot stably guarantee action/menu
  identity

## Next Batch Recommendation

Open one implementation batch to make project intake form contract loading use a
stable backend entry carrier:

1. first choice: ensure intake path loads contract through action/menu identity
2. fallback: extend model-contract request with explicit entry identity fields

Only after that lands should backend emit intake-specific `form_governance`.
