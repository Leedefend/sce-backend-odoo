# ITER-2026-04-03-915

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: customer seed materialization for entry context
- risk: high
- publishability: publishable

## Summary of Change

- updated:
  - `addons/smart_construction_custom/__manifest__.py`
- created:
  - `addons/smart_construction_custom/data/customer_project_seed.xml`
- implementation:
  - added install-time minimal `project.project` seed (`展厅-主线体验项目`) with `base.user_admin` ownership.
  - registered seed file into module data load list.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-915.yaml`: PASS
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_custom ... make mod.upgrade MODULE=smart_construction_custom DB_NAME=sc_demo`: PASS (upgrade run)
- `CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_custom ODOO_ARGS='-i smart_construction_custom' ... make mod.upgrade MODULE=smart_construction_custom DB_NAME=sc_demo`: PASS (install run to load seed)
- `docker exec sc-backend-odoo-prod-sim-db-1 psql -U odoo -d sc_demo -c "select count(*) from project_project;"`: PASS (`1`)
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.product.main_entry_convergence.v1`: PASS

## Key Evidence

- DB fact:
  - `project_project` count in `sc_demo` is `1`
- smoke artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T070112Z/summary.json`
- semantic result:
  - `backend_entry_route`: `/s/project.management`
  - `backend_project_context.project_id`: `1`

## Risk Analysis

- high-risk batch by policy path (Section 6.7) due manifest/data-load changes.
- change scope stayed within approved high-risk allowlist (`smart_construction_custom` manifest + data only).
- residual runtime note:
  - smoke still records unrelated frontend resource `500` console errors, but main entry semantic path is PASS.

## Rollback Suggestion

- code rollback:
  - `git restore addons/smart_construction_custom/__manifest__.py`
  - `git restore addons/smart_construction_custom/data/customer_project_seed.xml`
- runtime rollback (if needed):
  - uninstall `smart_construction_custom` from `sc_demo` or remove seeded project record by xmlid
    `smart_construction_custom.project_sc_demo_seed_primary`
- governance rollback:
  - `git restore agent_ops/tasks/ITER-2026-04-03-915.yaml`
  - `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-915.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-03-915.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- open low-risk verify-focused batch to classify and remove remaining frontend resource `500` console noise without changing entry semantic contract.
