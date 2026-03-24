# Product Edition Lifecycle Context Log v1

## Batch

- batch: `Edition Lifecycle Governance v1`
- date: `2026-03-24`

## Layer Target / Module / Reason

- Layer Target: `Platform Layer / Delivery Runtime / Release Governance`
- Module: `addons/smart_core + scripts/verify + docs/ops/releases + docs/architecture`
- Reason: `在现有 product edition stratification 基础上，把 edition 从可解析分层升级为受控发布渠道，并补齐 access/promotion/rollback gate`

## Completed

- added edition lifecycle state on `sc.product.policy`
- added edition access control via `access_level + allowed_role_codes`
- added `ProductEditionPromotionService`
- added stable fallback and edition diagnostics in runtime
- added lifecycle / access / promotion guards
- added release gate `verify.release.edition_lifecycle.v1`

## Fixed Risks

- preview access is now role controlled
- runtime fallback no longer returns a fake preview policy when requested preview is unavailable
- stable fallback is constrained to public stable edition

## Next Natural Direction

- `Edition Runtime Routing v1`
  - explicitly route login/session to selected edition channel

or

- `Edition Freeze Surface v1`
  - freeze edition-level release evidence and rollback checkpoints
