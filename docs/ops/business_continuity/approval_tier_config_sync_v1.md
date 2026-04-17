# Approval Tier Config Sync v1

## Purpose

Payment submit can now reach `submit`, but approval cannot proceed because no
`tier.definition` records exist and no `tier.review` records are generated.

This batch configures one runtime approval tier definition for the payable
request lifecycle.

## Config

- model: `payment.request`
- reviewer type: group
- reviewer group: `smart_construction_core.group_sc_cap_finance_manager`
- approved callback: runtime-compatible `ir.actions.server`
- rejected callback: runtime-compatible `ir.actions.server`
- notifications: disabled for this dev/demo config replay

## Boundaries

This batch does not change payment model code, ACL, settlement/account rules, or
frontend behavior.

## Evidence

The script writes:

- `artifacts/ops/approval_tier_config_sync_result_v1.json`
- `artifacts/ops/approval_tier_config_sync_rollback_v1.json`

## 2026-04-17 Execution

Write mode created/updated:

- one active `tier.definition` for `payment.request`
- two runtime-compatible server actions for approved/rejected callbacks
- reviewer group bound to finance manager capability

Rollback-only lifecycle verification passed:

- submit generated one `tier.review`
- review status after submit: `pending`
- manager approval changed review status to `approved`
- request state after approval: `approved`
- request validation status after approval: `validated`
