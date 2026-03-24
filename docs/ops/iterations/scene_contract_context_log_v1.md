# Scene Contract Context Log v1

## 2026-03-24

- batch: `Scene Contract Standardization v1`
- status: `completed`
- scope:
  - released scene contract audit
  - released scene standard doc
  - additive released scene contract adapter
  - scene contract guard
  - release gate integration

## Facts Frozen

- `projects.intake` is a released route-entry scene, not a backend `*.enter` payload
- FR-2 to FR-5 released runtime scenes are standardized by wrapping existing `*.enter` payloads
- `my_work.workspace` is standardized by wrapping `page.contract`
- released standard field is `scene_contract_standard_v1`

## Key Runtime Touchpoints

- `addons/smart_core/core/scene_contract_builder.py`
- `addons/smart_core/delivery/scene_service.py`
- `addons/smart_core/core/runtime_page_contract_builder.py`
- `addons/smart_construction_core/handlers/project_*_enter.py`
- `addons/smart_construction_core/handlers/cost_tracking_enter.py`
- `addons/smart_construction_core/handlers/payment_slice_enter.py`
- `addons/smart_construction_core/handlers/settlement_slice_enter.py`
- `scripts/verify/product_scene_contract_guard.py`

## Guard Baseline

- `make verify.product.scene_contract_guard`
- `make verify.release.delivery_engine.v1`
- `pnpm -C frontend/apps/web build`

## Next Recommended Batch

Do not reopen slices.

Preferred next step:

- `scene-level freeze/governance strengthening`

Possible directions:

- standardize more frontend scene VM consumption on `scene_contract_standard_v1`
- define scene-level freeze criteria for future released slices
- extend role-level scene contract guards without changing released product policy

## 2026-03-24 (Scene Freeze & Replication v1)

- batch: `Scene Freeze & Replication v1`
- status: `in_progress`
- scope:
  - released scene snapshot model
  - explicit freeze service
  - replication service
  - product policy scene version binding
  - guard baseline

## Facts Frozen For This Batch

- snapshot writes are explicit operations, not implicit runtime side effects
- released scene asset truth lives in `addons/smart_core`, not in the legacy tile-scene support models
- `sc.product.policy.scene_version_bindings` is the released product selector for active scene asset versions
