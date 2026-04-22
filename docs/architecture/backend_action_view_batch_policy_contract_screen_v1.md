# Backend ActionView Batch Policy Contract Screen V1

## Problem

Frontend currently decides batch action behavior through model-name
special-cases:

- block batch delete for `project.project`
- force delete-only batch mode for:
  - `project.task`
  - `res.company`
  - `hr.department`
  - `res.users`

This is invalid because batch action affordance is not a frontend inference from
model identity. It is a scene/action policy owned by backend orchestration.

## Ownership

Owner:
- `scene-orchestration layer`

Reason:
- batch actions are page-level action-surface policy
- they are not base business truth of a model record
- frontend should only consume the policy envelope for the current action/list
  surface

## Minimum Contract Target

The current action/list surface should expose explicit batch policy.

Minimum shape:

```json
{
  "batch_policy": {
    "enabled": true,
    "delete_allowed": false,
    "delete_only_mode": false,
    "available_actions": ["archive", "assign", "export"]
  }
}
```

If delete is available, it should be surfaced explicitly instead of inferred.

Example:

```json
{
  "batch_policy": {
    "enabled": true,
    "delete_allowed": true,
    "delete_only_mode": true,
    "available_actions": ["delete"]
  }
}
```

## Required Semantics

Per action/list surface:
- `batch_policy.enabled`
- `batch_policy.delete_allowed`
- `batch_policy.delete_only_mode`
- `batch_policy.available_actions`

Optional:
- `batch_policy.delete_block_reason`
- `batch_policy.selection_required`
- `batch_policy.max_selection`

## Frontend Consumption Rule

Frontend follow-up target:
- stop checking model names for batch delete behavior
- derive delete affordance only from `batch_policy.delete_allowed`
- derive delete-only mode only from `batch_policy.delete_only_mode`
- derive visible batch actions from `batch_policy.available_actions`

## Contract Placement Recommendation

Recommended placement:
- current scene-ready list/action surface contract

Acceptable placement examples:
- `scene_ready.list_surface.batch_policy`
- `action_contract.surface_policies.batch_policy`

The key requirement is that the policy is emitted for the current list/action
surface and is not reconstructed by frontend.

## Recommended Implementation Order

1. backend orchestration emits `batch_policy`
2. frontend removes:
   - `project.project` delete block special-case
   - `batchDeleteOnlyModels` hardcoded model set
3. verify visible batch actions and destructive-action behavior from contract

## Stop Boundary

Do not let frontend infer batch delete or delete-only behavior from model names
after this contract lands.
