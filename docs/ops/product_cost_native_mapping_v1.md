# Phase 17-A: Cost Native Mapping v1

## Layer Target
- Domain Layer
- Platform Layer
- Verification Layer

## Native Carrier Freeze
- Primary carrier: `account.move`
- Secondary context: `project.project`
- Slice intent family: `cost.tracking.*`

## Field Mapping
- `project.project.id` -> project context anchor
- `account.move.project_id` -> project scoped native cost relation
- `account.move.move_type` -> supported native cost carrier type
  - `in_invoice`
  - `in_refund`
  - `entry`
- `account.move.state` -> posted / draft runtime status
- `account.move.date` -> cost fact effective date
- `account.move.partner_id.display_name` -> supplier / partner label
- `account.move.amount_total_signed` -> invoice/refund signed amount source
- `account.move.line.account_id.internal_group` + `debit` -> journal entry cost fallback

## Readonly Aggregation Boundary
- `cost_tracking_native_adapter` only reads:
  - `project.project`
  - `account.move`
  - `account.move.line`
- Adapter is forbidden to:
  - create cost ledgers
  - write project state
  - return scene contract
  - emit page / block structure

## Product Boundary
- This slice is `native-readonly`.
- Runtime output is limited to:
  - summary facts
  - recent native vouchers
  - suggested navigation actions
- No new business model is introduced.
- No execution side effect is introduced.

## Reason
- Cost slice must reuse Odoo native accounting truth instead of rebuilding project-scoped cost business objects.
- Scene contract ownership remains in platform orchestration, not in the adapter.
