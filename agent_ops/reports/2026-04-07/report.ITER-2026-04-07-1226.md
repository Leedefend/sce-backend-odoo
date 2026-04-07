# ITER-2026-04-07-1226 Report

## Summary of change
- Corrected runtime probe URL selection for native access.
- `scripts/verify/scene_legacy_auth_runtime_probe.py` now defaults to native endpoint `/api/v1/intent` (POST with `intent=app.init`) instead of hardcoded legacy path.
- Added configurable endpoint override via `SCENE_LEGACY_AUTH_RUNTIME_PROBE_ENDPOINT_PATH`.
- Preserved legacy smoke gate semantics and added endpoint override in `scripts/verify/scene_legacy_auth_smoke.py` (`SCENE_LEGACY_AUTH_SMOKE_URL` / `SCENE_LEGACY_AUTH_SMOKE_ENDPOINT_PATH`) without relaxing strict-mode behavior.

## Changed files
- `agent_ops/tasks/ITER-2026-04-07-1226.yaml`
- `scripts/verify/scene_legacy_auth_runtime_probe.py`
- `scripts/verify/scene_legacy_auth_smoke.py`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1226.yaml`
- PASS: `python3 scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`
- PASS: `python3 scripts/verify/scene_legacy_auth_runtime_probe.py`
  - Runtime probe captured sandbox/network restricted exceptions (`Operation not permitted`) but exits PASS by design (evidence-mode probe).

## Risk analysis
- Low risk.
- Scope limited to verify scripts and task/report artifacts.
- No business model, ACL, record rules, or manifest touched.
- Legacy auth strict semantics preserved.

## Rollback suggestion
- `git restore scripts/verify/scene_legacy_auth_runtime_probe.py`
- `git restore scripts/verify/scene_legacy_auth_smoke.py`
- `git restore agent_ops/tasks/ITER-2026-04-07-1226.yaml`
- `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1226.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-07-1226.json`

## Next iteration suggestion
- Run next batch with explicit runtime base URL for your native lane (for example set `E2E_BASE_URL` to your expected native host/port) and re-capture app-entry evidence using the corrected native endpoint default.
