# Native Runtime Environment Repair Lane Batch2 Matrix Evidence v1

## Scope

- Task: `ITER-2026-04-07-1215`
- Objective: compare runtime behavior on `localhost:8069` vs `localhost:8070`

## Escalated Matrix Sampling

- Probe command:
  - `SCENE_LEGACY_AUTH_RUNTIME_PROBE_BASE_URLS=http://localhost:8069,http://localhost:8070 python3 scripts/verify/scene_legacy_auth_runtime_probe.py`

- Observed endpoint outcomes:
  - `http://localhost:8069/api/scenes/my` -> `RemoteDisconnected`
  - `http://localhost:8070/api/scenes/my` -> timeout (`URLError: timed out`)

## Interpretation

- Two distinct transport failures exist across local base URLs.
- No evidence yet of stable unauthenticated `401/403` response surface.
- Environment/service/proxy lane remains the correct next repair direction.

## Verification

- `make verify.scene.legacy_auth.runtime_probe`: PASS (WARN evidence)
- `make verify.scene.legacy_contract.guard`: PASS
- `make verify.test_seed_dependency.guard`: PASS
- `make verify.scene.legacy_auth.smoke.semantic`: PASS

## Conclusion

- Matrix sampling PASS and confirms environment-level divergence (`RemoteDisconnected` vs timeout).
