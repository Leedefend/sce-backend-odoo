# Scene Promotion Policy v1

## Allowed Transitions

- `draft -> ready`
- `ready -> beta`
- `ready -> stable`
- `beta -> stable`
- `stable -> deprecated`

## Forbidden Transitions

- `draft -> beta`
- `draft -> stable`
- `beta -> ready`
- `deprecated -> *`

## Stable Promotion Preconditions

Before promoting a snapshot to `stable`, the platform must verify:

- scene contract is `scene_contract_standard_v1`
- `scene_key` is present
- `product_key` is present
- `capability_key` is present
- there is no active stable conflict for the same `(scene_key, product_key)`
  - unless `replace_active=True`

## Replacement Rule

When `replace_active=True`:

- existing active stable snapshot for the same `(scene_key, product_key)` is deprecated
- new target snapshot becomes the only active stable

## Product Policy Binding Rule

`scene_version_bindings` may only bind snapshots that are:

- `state == stable`
- `is_active == True`

Otherwise:

- runtime binding is rejected
- delivery runtime falls back to standardized runtime contract
- diagnostics must expose the fallback reason
