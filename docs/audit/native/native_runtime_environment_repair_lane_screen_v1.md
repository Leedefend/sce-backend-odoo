# Native Runtime Environment Repair Lane Screen v1

## Objective

Establish a dedicated environment-repair lane for `/api/scenes/my` runtime
transport anomaly (`RemoteDisconnected`) observed across live probes.

## Screen Classification

- Class: runtime environment/service edge behavior
- Not classified as:
  - auth smoke semantic defect
  - business fact defect
  - permission model defect

## Candidate Repair Surface (Future Lane)

- runtime service startup/readiness settings
- local reverse-proxy/port forwarding behavior
- request path termination behavior before controller response

## Non-Goals / Forbidden Surface

- no business model/controller semantic changes in `addons/**`
- no ACL/rule modifications
- no financial semantics

## Minimal Gate Set

- `python3 agent_ops/scripts/validate_task.py <task.yaml>`
- `make verify.scene.legacy_contract.guard`
- `make verify.test_seed_dependency.guard`
- `make verify.scene.legacy_auth.smoke.semantic`

## Exit Signal For Lane

- Live probe against `/api/scenes/my` returns stable `401/403` (unauthenticated),
  with expected error envelope and deprecation headers.

## Decision

- Screen PASS: open dedicated runtime environment repair lane next.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.
