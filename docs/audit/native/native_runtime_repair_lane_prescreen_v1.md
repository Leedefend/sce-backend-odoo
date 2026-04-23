# Native Runtime Repair Lane Pre-Screen v1

## Objective

Define a bounded runtime-repair lane for `/api/scenes/my` `RemoteDisconnected`
behavior observed in live probe, without touching business facts or ACL/rules.

## Allowed Candidate Scope (Future Execute Lane)

- `scripts/verify/python_http_smoke_utils.py` (retry/error classification only)
- `scripts/verify/scene_legacy_auth_smoke.py` (runtime error detection envelope only)
- runtime environment docs/evidence under `docs/audit/native/**`

## Forbidden Scope

- `addons/**` business model/controller mutations
- `security/**`, `record_rules/**`, `ir.model.access.csv`
- `__manifest__.py` dependency order change
- any payment/settlement/accounting semantic changes

## Minimal Gate Set

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.scene.legacy_contract.guard`
- `make verify.test_seed_dependency.guard`
- `make verify.scene.legacy_auth.smoke.semantic`

## Entry Criteria

- Confirm live probe evidence still shows non-401/403 runtime anomaly.
- Keep changes inside verify/runtime helper boundary only.

## Stop Criteria

- Any spillover into forbidden path.
- Any gate failure.
- Any proposal requiring business controller logic mutation.

## Decision

- Pre-screen PASS: runtime repair lane can be opened as low-risk verify-helper lane.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.
