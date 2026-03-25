# Release Approval Policy Model v1

## Goal

Introduce minimal release policy and approval control on top of `sc.release.action` without changing released product semantics.

## Layer Target

- Platform Layer
- Delivery Runtime Layer
- Release Governance Layer

## Module

- `addons/smart_core/delivery/release_approval_policy_service.py`
- `addons/smart_core/models/release_action.py`
- `addons/smart_core/delivery/release_orchestrator.py`

## Policy Surface

Three minimal policies are governed:

1. `release.promote.preview.direct`
   - executor: `pm / executive / admin`
   - approval: not required
2. `release.promote.standard.approval_required`
   - executor: `pm / executive / admin`
   - approver: `executive / admin`
   - approval: required
3. `release.rollback.controlled`
   - executor: `executive / admin`
   - approver: `executive / admin`
   - approval: required

## Release Action Additions

`sc.release.action` now includes:

- `policy_key`
- `approval_required`
- `approval_state`
- `allowed_executor_role_codes_json`
- `required_approver_role_codes_json`
- `policy_snapshot_json`
- `approved_by_user_id`
- `approved_at`
- `approval_note`

## Orchestration Rules

- executor permission is enforced before execution
- approval-required action stays `pending` until approved
- admin/executive may self-approve during orchestration when policy allows it
- rollback remains restricted to controlled actors

## Verification

- `verify.release.policy_guard`
- `verify.release.approval_guard`
- `verify.release.approval.v1`
