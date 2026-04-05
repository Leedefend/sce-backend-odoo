# ITER-2026-04-03-920

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: project decision engine fallback
- risk: low
- publishability: publishable

## Summary of Change

- updated:
  - `addons/smart_construction_core/services/project_decision_engine_service.py`
- implementation:
  - added fallback payload builders for `analyze` and `decide`.
  - replaced hard dependency path on `sc.evidence.risk.engine` / `sc.evidence.action.engine` with safe model resolution + exception fallback.
  - keeps returned decision contract shape available when engines are missing.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-920.yaml`: PASS
- `python3 -m py_compile addons/smart_construction_core/services/project_decision_engine_service.py`: PASS
- `ENV=test ... make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_demo CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core`: PASS
- direct probe:
  - `project.dashboard.enter` changed from 500 -> 200 after service restart
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: PASS

## Key Evidence

- smoke summary:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T074321Z/summary.json`
- result:
  - `console_errors`: empty
  - `http_5xx_resources`: empty
  - route remains `/s/project.management`

## Risk Analysis

- low code risk: additive fallback only; no contract field removal.
- operational note:
  - one mis-targeted upgrade command initially touched `sc_prod_sim` path and failed due pre-existing duplicate user in custom module data; corrected by rerunning explicit `DB_NAME=sc_demo` make-variable form.

## Rollback Suggestion

- `git restore addons/smart_construction_core/services/project_decision_engine_service.py`
- `git restore agent_ops/tasks/ITER-2026-04-03-920.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-920.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-920.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- open optional cleanup batch to remove/triage unrelated `sc_prod_sim` custom-user duplicate seed issue observed in mis-targeted upgrade command path.
