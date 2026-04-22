# Native Runtime Environment Repair Lane Batch3 8070 Root-Cause Evidence v1

## Scope

- Task: `ITER-2026-04-07-1216`
- Objective: narrow root-cause signals for `localhost:8070` timeout

## Evidence Captured

- Listener snapshot (`ss -ltn`):
  - observed `*:8069` LISTEN
  - no `*:8070` LISTEN observed

- Escalated probe (8070 only):
  - `SCENE_LEGACY_AUTH_RUNTIME_PROBE_BASE_URLS=http://localhost:8070`
  - result: retries exhausted with timeout (`URLError: timed out`)

## Root-Cause Direction

- 8070 timeout is consistent with missing listener/forward chain on local runtime.
- 8069 and 8070 are not equivalent surfaces in current environment.

## Verification

- `make verify.scene.legacy_auth.runtime_probe`: PASS (WARN evidence)
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Conclusion

- Batch3 confirms 8070 issue is environment listener/forward path, not auth-smoke semantic logic.
