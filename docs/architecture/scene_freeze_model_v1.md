# Scene Freeze Model v1

## Scope

`Scene Freeze & Replication v1` only covers released delivery scenes already governed by:

- `construction.standard`
- `release_navigation_v1`
- `delivery_engine_v1`
- `scene_contract_standard_v1`

It does not reopen FR-1 to FR-5 business semantics and does not reuse the legacy tile-scene governance models as runtime source of truth.

## Layer Target

- Platform Layer: `addons/smart_core/models/scene_snapshot.py`
- Delivery Runtime Layer: `addons/smart_core/delivery/scene_snapshot_service.py`
- Product Policy Layer: `addons/smart_core/models/product_policy.py`

## Asset Model

Model: `sc.scene.snapshot`

Required fields:

- `scene_key`
- `product_key`
- `capability_key`
- `version`
- `channel`
- `contract_json`
- `is_active`

Optional fields:

- `label`
- `route`
- `source_type`
- `source_ref`
- `meta_json`
- `cloned_from_snapshot_id`
- `note`

Uniqueness:

- `(product_key, scene_key, version, channel)` must be unique

## Freeze Flow

```text
product policy scene entry
-> scene_contract_standard_v1
-> sc.scene.snapshot
```

Freeze is explicit. Runtime reads do not auto-write snapshots.

## Replication Flow

```text
existing snapshot
-> clone with target version/channel/product/capability overrides
-> new sc.scene.snapshot
```

Allowed overrides:

- `scene_key`
- `product_key`
- `capability_key`
- `version`
- `channel`
- `label`
- `route`

## Version Binding

`sc.product.policy.scene_version_bindings` maps released scene keys to active asset versions:

```json
{
  "project.management": {
    "version": "v1",
    "channel": "stable"
  }
}
```

Delivery runtime resolves:

```text
policy scene key
-> scene_version_bindings
-> sc.scene.snapshot
-> delivery_engine_v1.scenes[*].scene_contract_standard_v1
```

## Guard Baseline

- `make verify.scene.freeze_snapshot_guard`
- `make verify.scene.replication_guard`
- `make verify.scene.version_binding_guard`
- `make verify.release.scene_asset.v1`
