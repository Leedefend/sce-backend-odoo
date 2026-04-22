# Native Live Auth 401/403 Evidence v1

## Scope

- Task: `ITER-2026-04-07-1209`
- Objective: attempt live unauthenticated `/api/scenes/my` status evidence

## Live Probe Result (Escalated)

- Command (strict default):
  - `unset SCENE_LEGACY_AUTH_SMOKE_ALLOW_UNREACHABLE_FALLBACK && python3 scripts/verify/scene_legacy_auth_smoke.py`
- Result:
  - exit code `1`
  - endpoint reachable at connection layer but closes response unexpectedly
  - last error:
    - `RemoteDisconnected: Remote end closed connection without response`

## Interpretation

- This is **not** a strict-policy regression.
- Strict default still fails correctly on runtime-unreachable class errors.
- Live 401/403 evidence remains pending due runtime endpoint behavior (`RemoteDisconnected`).

## Guard Matrix

- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Next Action

- Keep current strict policy unchanged.
- Open dedicated runtime availability repair lane if live endpoint is expected to return 401/403 in this environment.
