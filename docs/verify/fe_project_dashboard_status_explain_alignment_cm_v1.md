# FE Project Dashboard Status Explain Alignment CM

## Goal

Align the restored `project.management` dashboard surface with the verifier's
expected `当前状态说明` semantics by consuming
`state_explain.status_explain` directly.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-PROJECT-DASHBOARD-STATUS-EXPLAIN-ALIGNMENT-CM.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing chunk-size warning only
4. `make verify.portal.project_dashboard_primary_entry_browser_smoke.host BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`
   - FAIL
   - The prior `dashboard missing status explain` assertion is cleared
   - The failure frontier moved to:
     - `project switcher should expose at least 2 projects, got 1`

## Conclusion

This batch successfully aligned the dashboard explain label and field
consumption:

- explain card label is now `当前状态说明`
- dashboard explain content now prefers backend `status_explain`

The batch result still remains `FAIL` because the required live browser smoke
did not fully pass. The remaining blocker has moved away from status-explain
rendering and narrowed to project-switcher option supply.

The next valid batch should stop touching frontend explain rendering and reopen
the backend `project.entry.context.options` supply path.
