# ITER-2026-04-03-918

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: frontend runtime loopback normalization gate
- risk: low
- publishability: not_publishable

## Summary of Attempt

- attempted change:
  - `frontend/apps/web/src/main.ts` skip localhost→127 redirect in `test` env.
- runtime outcome:
  - no observable effect in host smoke artifact; 5xx resource remains `POST http://127.0.0.1/api/v1/intent?db=sc_demo`.
- action taken:
  - reverted `frontend/apps/web/src/main.ts` change in same batch to avoid unverified behavior drift.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-918.yaml`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: PASS
- objective convergence (`127` noise removal): FAIL

## Failure Analysis

- current evidence is insufficient to determine exact failing intent payload for the captured `127.0.0.1` 500 request.
- frontend runtime switch alone is not a deterministic fix path under current runtime delivery mode.

## Rollback Suggestion

- rollback already applied for this batch:
  - `frontend/apps/web/src/main.ts` restored
- governance rollback:
  - `git restore agent_ops/tasks/ITER-2026-04-03-918.yaml`
  - `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-918.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-03-918.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open low-risk observability batch to capture 5xx fetch request body snippet/intent hint in smoke summary, then execute deterministic fix.
