# Native Runtime Availability Evidence v1

## Scope

- Task: `ITER-2026-04-07-1206`
- Focus: strict-default legacy auth smoke runtime behavior in current environment

## Runtime Observation

- Command A (strict default):
  - `unset SCENE_LEGACY_AUTH_SMOKE_ALLOW_UNREACHABLE_FALLBACK && python3 scripts/verify/scene_legacy_auth_smoke.py`
  - exit code: `1` (FAIL as expected)
  - error contains:
    - `runtime unreachable in strict mode`
    - `base_url=http://localhost:8069`
    - `endpoint=http://localhost:8069/api/scenes/my`
    - original retry exception (`Operation not permitted`)

- Command B (explicit fallback enabled):
  - `SCENE_LEGACY_AUTH_SMOKE_ALLOW_UNREACHABLE_FALLBACK=true python3 scripts/verify/scene_legacy_auth_smoke.py`
  - exit code: `0`
  - output contains `WARN runtime unreachable; fallback PASS`

## Guard Matrix

- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Conclusion

- Runtime evidence matches expected policy:
  - strict default mode fails on runtime unreachable
  - fallback path requires explicit environment opt-in

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.
