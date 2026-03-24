# Scene Lifecycle Model v1

## Goal

Promote released scene snapshots from versioned assets to governed lifecycle units.

## Scope

Applies only to released scene assets used by:

- `construction.standard`
- `delivery_engine_v1.scenes`
- `scene_contract_standard_v1`

## Snapshot States

`sc.scene.snapshot.state`

- `draft`
- `ready`
- `beta`
- `stable`
- `deprecated`

## Lifecycle Rules

- freeze snapshot defaults to `draft`
- replicated snapshot defaults to `draft`
- only `stable + is_active=True` is considered bindable for released product policy
- `deprecated` snapshots cannot be promoted again

## Active Stable Uniqueness

For the same `(scene_key, product_key)`:

- only one snapshot may be `state='stable' and is_active=True`

Conflict handling:

- promotion to `stable` fails with `ACTIVE_STABLE_CONFLICT`
- explicit replacement is allowed via `replace_active=True`
- replaced active stable snapshots are marked `deprecated`

## Runtime Rule

`delivery_engine_v1.scenes` resolves:

```text
policy binding
-> active stable snapshot
-> snapshot contract
else
-> fallback standardized runtime contract
```

## Diagnostics

Runtime binding exposes:

- `snapshot_resolved`
- `snapshot_state`
- `snapshot_version`
- `snapshot_fallback_reason`
- `binding_allowed`
