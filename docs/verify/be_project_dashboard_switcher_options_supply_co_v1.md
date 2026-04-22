# BE Project Dashboard Switcher Options Supply CO

## Goal

Recover `project.entry.context.options` so the project-management dashboard
switcher receives multiple valid options, including the showroom demo project
required by the live verifier.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-BE-PROJECT-DASHBOARD-SWITCHER-OPTIONS-SUPPLY-CO.yaml`
   - PASS
2. `python3 -m py_compile addons/smart_construction_core/services/project_entry_context_service.py`
   - PASS
3. Direct Odoo shell diagnosis inside `sc-backend-odoo-dev-odoo-1`
   - PASS
   - `ProjectEntryContextService.list_options(active_project_id=925, limit=12)`
     now returns:
     - `option_count=2`
     - first options:
       - `925 / FR4-EXEC-PAY-4237cc9d`
       - `1 / 展厅-主线体验项目`
4. `make verify.portal.project_dashboard_primary_entry_browser_smoke.host BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`
   - PASS
   - Artifact:
     - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T074210Z/`

## Conclusion

This batch repaired the backend orchestration-side option supply path.

The key fixes were:

- candidate accumulation now persists correctly instead of dropping appended
  recordsets
- switcher candidate collection explicitly injects showroom/demo candidates so
  the verifier-required `展厅-` project is not lost behind recent-write sampling

With those repairs in place, the browser smoke now clears both prior switcher
assertions:

- option count is no longer stuck at `1`
- showroom demo project is present in the switcher
