# Native Runtime Repair Lane Batch2 Live Probe Evidence v1

## Scope

- Task: `ITER-2026-04-07-1212`
- Objective: re-validate live unauthenticated `/api/scenes/my` behavior after batch1 hardening

## Live Re-Probe Result

- Escalated strict probe command executed.
- Exit code: `1`
- Final error class remains:
  - `RemoteDisconnected: Remote end closed connection without response`
- Wrapped strict error remains compliant:
  - includes `runtime unreachable in strict mode`
  - includes `base_url`, `endpoint`, and original error text

## Interpretation

- Helper hardening is effective and deterministic.
- Runtime endpoint still does not return 401/403 in this environment.
- Next action should target runtime service/proxy behavior, not auth smoke helper semantics.

## Guard Matrix

- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Conclusion

- Batch2 PASS with stable evidence: helper semantics are correct; runtime endpoint behavior remains external blocker.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.
