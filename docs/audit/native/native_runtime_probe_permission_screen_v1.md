# Native Runtime Probe Permission Screen v1

## Scope

- Task: `ITER-2026-04-07-1208`
- Mode: `screen`
- Objective: classify runtime probe permission blocker and define recovery trigger

## Screen Result

- Blocker class: environment capability constraint (not business logic defect)
- Evidence basis:
  - previous probe shows `PermissionError: [Errno 1] Operation not permitted`
  - semantic gate still passes for strict/fallback policy behavior

## Impact Classification

- Severity: medium (blocks reachable-window live 401/403 evidence)
- Scope: runtime verification path only
- Business-fact risk: none

## Recovery Trigger (Non-Invasive)

- When host/network policy allows active socket probe, execute:
  - `python3 scripts/verify/scene_legacy_auth_smoke.py` (strict default)
  - optional reachable-window HTTP check for `/api/scenes/my` expecting `401/403`
- Keep existing short-chain guards as baseline:
  - `make verify.scene.legacy_contract.guard`
  - `make verify.test_seed_dependency.guard`
  - `make verify.scene.legacy_auth.smoke.semantic`

## Conclusion

- Screen PASS: blocker is external runtime permission boundary.
- Next eligible step is gated by runtime capability availability, not code mutation.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.
