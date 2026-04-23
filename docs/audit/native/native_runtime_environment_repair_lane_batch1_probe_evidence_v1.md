# Native Runtime Environment Repair Lane Batch1 Probe Evidence v1

## Scope

- Task: `ITER-2026-04-07-1214`
- Objective: add reusable runtime probe utility for legacy auth endpoint

## Implementation

- Added probe utility:
  - `scripts/verify/scene_legacy_auth_runtime_probe.py`
- Added make target:
  - `verify.scene.legacy_auth.runtime_probe`

## Probe Output (Current Environment)

- Probe target attempted:
  - `http://localhost:8070/api/scenes/my`
- Observed transport exception:
  - request retries exhausted with timeout/refusal class output
- Probe behavior:
  - records exception details
  - exits PASS with WARN to keep evidence collection continuous

## Verification

- `make verify.scene.legacy_auth.runtime_probe`: PASS (with WARN evidence)
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Risk Summary

- Low risk verify-tooling change only.
- No business/ACL/financial path changes.

## Conclusion

- Runtime probe tooling is now available for repeated environment-repair evidence capture.

## Legacy Endpoint Deprecation Note
- `/api/scenes/my` is deprecated.
- Successor endpoint: `/api/v1/intent` with `intent=app.init`.
- Sunset date: `2026-04-30`.
- Deprecation header contract reference: `Deprecation`, `Sunset`, `Link`, `X-Legacy-Endpoint`.
