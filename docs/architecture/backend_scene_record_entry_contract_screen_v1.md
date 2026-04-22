# Backend Scene Record Entry Contract Screen v1

## Goal

Determine whether backend already exposes a generic scene-carried record-entry
contract that frontend can consume as the unique public authority, or whether a
new additive scene-orchestration contract must be supplied first.

## Scope

Focused screening only:

- `addons/smart_core/core/system_init_payload_builder.py`
- `addons/smart_core/governance/scene_normalizer.py`
- `addons/smart_core/identity/identity_resolver.py`
- `addons/smart_core/core/load_contract_entry_context.py`
- `addons/smart_core/handlers/ui_contract.py`

This batch does not change runtime behavior.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration screen
- Module: generic scene-carried record entry contract
- Module Ownership: `smart_core` contract surface
- Kernel or Scenario: kernel
- Reason: determine whether the missing piece is backend semantic organization
  rather than another frontend routing special case

## Screen Findings

### 1. Backend already carries `record_id`, but only as compatibility or request input

- `system_init_payload_builder`, `scene_normalizer`, and `identity_resolver`
  can all materialize `entry_target`
- that `entry_target` is frozen as `type=scene` and uses `record_id` only inside
  `compatibility_refs`
- this means backend has not declared `record_id` as a first-class scene-entry
  authority carrier

Minimum observed shape today:

```json
{
  "entry_target": {
    "type": "scene",
    "scene_key": "some.scene",
    "compatibility_refs": {
      "model": "x.model",
      "record_id": 42
    }
  }
}
```

### 2. Scene-ready export does not provide a canonical record-entry envelope

- startup/minimal `scene_ready_contract_v1` only keeps `meta.target`
- `meta.target` may include `model`, `action_id`, `menu_id`, `route`, and now
  `entry_target`, but there is no dedicated scene-level `record_entry` or
  equivalent envelope
- no backend rule currently states how frontend should reopen a concrete record
  from scene semantics without depending on native route params

### 3. `ui.contract` can consume `record_id`, but that is request-time input, not startup authority output

- `ui_contract` already accepts `record_id` for `subject=model` and
  `subject=action`
- `load_contract_entry_context` resolves model/action/view context from
  `menu_id/action_id`, but it does not define one startup/exported scene-entry
  contract for concrete record identity
- this confirms the gap is not record-read capability itself; the gap is the
  absence of one backend-supplied scene-carried record-entry semantic surface

## Decision

Backend does **not** yet expose a sufficient generic record-entry contract for
frontend to collapse `/r/:model/:id` as a public authority route.

The current backend state is:

- `scene_key` is the public authority
- `record_id/model` survive only as compatibility refs or request payload
- no canonical record-entry envelope is exported for scene-first consumers

So frontend would still need to infer record authority from native routing if we
attempted `/r` convergence now. That is out of boundary.

## Backend Sub-Layer Decision

The next batch belongs to the `scene-orchestration layer`, not the
`business-fact layer`.

Reason:

- no new business truth is missing
- the missing piece is how existing record identity is organized for
  scene-oriented consumption
- backend must supply a consumption-ready envelope that lets frontend reopen or
  embed a concrete record while keeping `scene_key` as the public authority

## Minimum Additive Direction

The next implementation batch should introduce one bounded scene-carried
record-entry envelope under scene target semantics.

Frozen direction:

```json
{
  "entry_target": {
    "type": "scene",
    "scene_key": "projects.detail",
    "record_entry": {
      "model": "project.project",
      "record_id": 42,
      "action_id": 519,
      "menu_id": 329
    }
  }
}
```

Constraints:

- `scene_key` remains the only public authority field
- `record_entry` is additive orchestration context, not a parallel authority
  family
- backend must not fabricate record identity; it may only surface concrete
  record identity when already known by scene orchestration
- frontend should consume this envelope generically and must not add
  model-specific reopen logic

## Frozen Next-Step Rule

- do not reduce `/r` public authority before one bounded backend implementation
  batch materializes the generic scene-carried `record_entry` envelope
- that batch should stay inside `smart_core` scene-orchestration contract output
  and avoid widening into business-fact or frontend-specific layout changes
