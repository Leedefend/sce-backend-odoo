# ITER-2026-04-07-1228 Report

## Summary of change
- Executed native runtime accessibility evidence batch after URL correction.
- Verified runtime probe still targets native endpoint `/api/v1/intent` with `POST`.
- Collected direct host curl evidence for both native and legacy endpoints.

## Changed files
- `agent_ops/tasks/ITER-2026-04-07-1228.yaml`
- `agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1228.md`
- `agent_ops/state/task_results/ITER-2026-04-07-1228.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1228.yaml`
- PASS: `E2E_BASE_URL=http://localhost:8069 python3 scripts/verify/scene_legacy_auth_runtime_probe.py`
  - probe endpoint: `http://localhost:8069/api/v1/intent`
  - observed: `URLError [Errno 1] Operation not permitted` under current runtime policy
- PASS: `python3 scripts/verify/scene_legacy_auth_smoke_semantic_verify.py`

## Runtime evidence
- Direct curl probes:
  - `POST http://localhost:8069/api/v1/intent` -> `curl: (7) Couldn't connect to server`
  - `GET http://localhost:8069/api/scenes/my` -> `curl: (7) Couldn't connect to server`
- Host signal snapshot:
  - `ss -ltn` showed `*:8069` listener line but netlink socket access is restricted in this sandbox
  - `docker ps` not accessible due docker socket permission denied

## Risk analysis
- Low risk, evidence-only governance batch.
- No business-layer source mutation.
- Current blocker remains runtime connectivity policy/environment, not URL contract mismatch.

## Rollback suggestion
- `git restore agent_ops/tasks/ITER-2026-04-07-1228.yaml`
- `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1228.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-07-1228.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Run one host-approved, non-sandboxed probe window to capture decisive live response class (`401/403` vs transport close) on:
  - `POST /api/v1/intent` with `intent=app.init`
  - `GET /api/scenes/my`
