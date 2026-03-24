# Scene Contract Standard v1

## Goal

Standardize released scenes as a single product delivery contract without reopening FR-1 to FR-5 business semantics.

This standard is for released surface governance only.

## Scope

Applies to:

- `projects.intake`
- `project.dashboard`
- `project.plan_bootstrap`
- `project.execution`
- `cost.tracking`
- `payment`
- `settlement`
- `my_work.workspace`

## Standard Shape

```json
{
  "contract_version": "scene_contract_standard_v1",
  "identity": {},
  "target": {},
  "state": {},
  "page": {},
  "actions": {},
  "governance": {}
}
```

## 1. identity

Required:

- `scene_key`
- `title`
- `product_key`
- `capability`
- `version`

Rules:

- `scene_key` is the runtime scene identity, not the menu key
- `product_key` must match `construction.standard` released slice membership
- `capability` must be the released delivery capability key

## 2. target

Required:

- `route`
- `openable`
- `target`

Rules:

- `route` must be a released route, not `/workbench?...`
- `openable` must reflect whether the scene can be opened from released surface
- `target` is currently frozen to `same_tab`

## 3. state

Required:

- `status`
- `state_tone`
- `reason_code`
- `message`

Rules:

- `status` is release-facing scene state, not domain workflow state
- `reason_code` may reuse existing `suggested_action.reason_code`
- `message` must be user-facing, not diagnostics-only

## 4. page

Required:

- `layout`
- `zones`
- `blocks`

Rules:

- all calculations stay in backend
- `zones` must be array
- `blocks` must be array
- route-only entry scenes may expose empty `blocks`

## 5. actions

Required:

- `primary_actions`
- `secondary_actions`
- `next_action`

Rules:

- `next_action` is the preferred forward action for released surface
- for runtime entry scenes, it maps from existing `suggested_action`
- for route-only scenes, actions may be route actions

## 6. governance

Required:

- `contract_version`
- `trace_id`
- `policy_match`
- `released`
- `diagnostics_ref`

Rules:

- `contract_version` must equal top-level `contract_version`
- `policy_match` must remain `true` on released surface
- `released` must remain `true`

## Source Adapters

### Delivery exposure adapter

Source:

- `delivery_engine_v1.scenes`

Use:

- released entry governance
- route-only scene standardization

### Runtime entry adapter

Source:

- `project.dashboard.enter`
- `project.plan_bootstrap.enter`
- `project.execution.enter`
- `cost.tracking.enter`
- `payment.enter`
- `settlement.enter`

Use:

- FR-2 to FR-5 runtime standardization

### Page-contract adapter

Source:

- `page.contract(page_key=my_work)`

Use:

- `my_work.workspace` standardization

## Compatibility

Kept:

- legacy runtime payload keys
- `page_orchestration_v1`
- `scene_contract_v1`

Not allowed:

- frontend fallback to workbench route on released surface
- per-scene frontend hardcoding as the primary released contract source
- rewriting existing business orchestrators in this batch
