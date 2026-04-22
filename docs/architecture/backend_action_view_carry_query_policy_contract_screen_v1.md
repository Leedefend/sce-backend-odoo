# Backend ActionView Carry-Query Policy Contract Screen V1

## Problem

Frontend currently removes `scene` and `scene_key` from carry query when a row
click opens a record whose target model is `project.project`.

This is invalid because carry-query policy is not a frontend inference from
model identity. It is navigation orchestration policy owned by backend.

## Ownership

Owner:
- `scene-orchestration layer`

Reason:
- this is transition/navigation behavior for the current list/action surface
- it is not intrinsic business truth of the record model
- frontend should only consume an explicit carry policy for record-open actions

## Minimum Contract Target

The current action/list surface should expose record-open carry-query policy.

Minimum shape:

```json
{
  "record_open_policy": {
    "carry_query_mode": "preserve"
  }
}
```

If scene context must be cleared before record open:

```json
{
  "record_open_policy": {
    "carry_query_mode": "clear_scene_context"
  }
}
```

If only certain keys may be carried:

```json
{
  "record_open_policy": {
    "carry_query_mode": "whitelist",
    "carry_query_keys": ["company_id", "menu_id", "action_id"]
  }
}
```

## Required Semantics

Per action/list surface:
- `record_open_policy.carry_query_mode`

Supported minimum modes:
- `preserve`
- `clear_scene_context`
- `whitelist`

Optional:
- `record_open_policy.carry_query_keys`
- `record_open_policy.reason`

## Frontend Consumption Rule

Frontend follow-up target:
- stop checking `targetModel === 'project.project'`
- apply carry-query behavior only from `record_open_policy`
- when mode is:
  - `preserve`: keep current carry query
  - `clear_scene_context`: remove `scene` and `scene_key`
  - `whitelist`: carry only declared keys

## Contract Placement Recommendation

Recommended placement:
- current scene-ready list/action surface contract

Acceptable placement examples:
- `scene_ready.list_surface.record_open_policy`
- `action_contract.surface_policies.record_open_policy`

The key requirement is that the policy is emitted for the current row-open
surface and is not reconstructed by frontend.

## Recommended Implementation Order

1. backend orchestration emits `record_open_policy`
2. frontend removes `project.project` carry-query special-case
3. verify row open transitions preserve/clear scene context only according to
   contract policy

## Stop Boundary

Do not let frontend infer carry-query clearing from record model name after this
contract lands.
