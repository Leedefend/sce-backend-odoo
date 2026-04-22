# Backend Scene Entry Authority Contract Screen V1

## Problem

Frontend is still not a unique scene-ready consumer because backend has not yet
frozen one canonical frontend-visible entry authority.

Current backend is partially converged:

- `default_route` and `role_surface` already carry `scene_key`
- navigation normalization already tries to infer and attach `scene_key`
- scene runtime contracts already use scene identity as the main semantic key

But backend still keeps public-facing mixed target grammar alive through
parallel references such as:

- `menu_id`
- `action_id`
- `model`
- `record_id`
- `target.route`

That leaves frontend with room to keep `/m`, `/a`, and `/r` as practical entry
families.

## Inputs Checked

1. `docs/architecture/frontend_scene_ready_only_contract_governance_topic_v1.md`
2. `docs/architecture/scene_route_boundary_alignment_screen_v1.md`
3. `docs/architecture/ui_base_vs_scene_ready_contract_v1.md`
4. `docs/architecture/backend_contract_layer_responsibility_freeze_v1.md`
5. `docs/architecture/runtime_entrypoint_inventory_v1.md`
6. `docs/architecture/backend_scene_switch_action_ownership_screen_v1.md`
7. `addons/smart_core/adapters/odoo_nav_adapter.py`
8. `addons/smart_core/governance/scene_normalizer.py`
9. `addons/smart_core/tests/test_system_init_payload_builder_semantics.py`
10. `addons/smart_core/tests/test_scene_normalizer_target_resolution.py`
11. `addons/smart_core/tests/test_scene_runtime_contract_chain.py`

## Current Backend Facts

### 1. Scene identity is already the strongest backend-owned key

Observed facts:

- `default_route` tests already assert `scene_key`
- `role_surface` tests already assert `landing_scene_key`
- scene runtime chain tests already use `landing_scene_key` as the primary
  entry identity

Conclusion:

- backend has already chosen scene identity as the main semantic anchor
- this should become the unique frontend-visible entry authority

### 2. Navigation still ships mixed target metadata

Observed facts:

- nav adaptation still resolves and carries `scene_key` together with
  `action_id`
- scene normalization target resolution still materializes `menu_id` and
  `action_id`
- scene-target resolution still depends on native anchors to bridge from Odoo
  navigation facts

Conclusion:

- native anchors are still needed internally
- but they are not yet frozen as internal-only references

### 3. No frozen public scene-entry target shape exists yet

Observed facts:

- there is clear scene-oriented identity
- there is no explicit released contract statement saying frontend-visible
  entry targets must be scene-oriented and that menu/action/model/record fields
  are compatibility-only references

Conclusion:

- missing contract freeze, not missing raw backend data

## Ownership Decision

### Business-fact layer?

No.

Reason:

- the problem is not ownership, state, permission, amount, or workflow truth
- no new business fact is needed to decide entry authority

### Scene-orchestration layer?

Yes.

Reason:

- the problem is how native anchors are translated into frontend-consumable
  scene entry semantics
- this is navigation and entry orchestration, not business truth creation

## Minimum Contract Decision

Frontend-visible entry authority must be one scene-oriented target family.

Minimum canonical target:

```json
{
  "entry_target": {
    "type": "scene",
    "scene_key": "projects.list"
  }
}
```

Allowed additive context:

```json
{
  "entry_target": {
    "type": "scene",
    "scene_key": "projects.list",
    "context": {
      "menu_id": 329,
      "action_id": 519
    }
  }
}
```

Rule:

- `scene_key` is the only frontend-visible authority field
- `menu_id/action_id/record_id/model/route` may survive only as bounded
  compatibility context or internal backend anchors
- they must not remain parallel target types at the public contract level

## Required Backend Freeze

### 1. Landing and default-route freeze

Backend should define:

- `default_route` public authority = `scene_key`
- `role_surface.landing_scene_key` public authority = `scene_key`

If additional refs are carried:

- they are compatibility context only
- they are not standalone frontend entry selectors

### 2. Menu and workspace navigation freeze

Backend navigation output should expose:

- target scene identity
- optional compatibility refs

Backend navigation output should not require frontend to choose among:

- `open_menu`
- `open_action`
- `open_record`
- arbitrary `target.route`

as separate public target families for ordinary product navigation.

### 3. List/form entry freeze

List and form work surfaces must be entered as scene-orchestration outputs.

This means:

- native form/tree/view facts may still feed backend assembly
- but frontend-visible entry semantics must still resolve to scene-oriented
  contract delivery
- direct record or action anchors are transitional compatibility paths, not the
  frozen public contract authority

## Scope Boundary

This screen does not decide:

- whether compatibility routes are removed immediately
- whether every existing record-open flow is rewritten in one batch
- whether backend stops storing menu/action anchors internally

This screen decides only:

- what the unique public authority is
- what is compatibility-only
- which layer owns the correction

## Decision Summary

1. Unique frontend-visible entry authority:
   - `scene_key`
2. Owner layer:
   - `scene-orchestration`
3. Native anchors:
   - internal or compatibility-only
4. List/form exception:
   - none

## Next Batch Recommendation

Open a backend implementation batch that freezes one additive released target
surface for:

- `default_route`
- navigation tree targets
- workspace/home/recommended-entry targets

with one rule:

- frontend consumes scene-oriented entry targets only

## One-Line Result

Backend is already closest to `scene_key` as the canonical identity, but it has
not yet frozen `scene_key` as the only frontend-visible entry authority while
downgrading menu/action/model/record fields to compatibility-only references.
