# FE Scene-Ready Dashboard Consumer Implement CL

## Goal

Consume the restored `project.management` dashboard startup semantics from
`scene_ready_contract_v1` so the generic frontend scene path renders the
dashboard surface instead of collapsing into embedded `ActionView/KanbanPage`.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-SCENE-READY-DASHBOARD-CONSUMER-IMPLEMENT-CL.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing chunk-size warning only
4. `make verify.portal.project_dashboard_primary_entry_browser_smoke.host BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`
   - FAIL
   - Artifact: `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T071638Z/`
   - But the failure frontier moved materially:
     - `dashboard_wait:done` now completes
     - `summary.dashboard_profile` is now `old`
     - the browser is no longer failing on the earlier generic
       `ActionView/KanbanPage` loading stall
   - Current terminal assertion:
     - `dashboard missing status explain`

## Conclusion

This batch restored the frontend generic consumer path enough for
`/s/project.management` to resolve as the dashboard profile again.

The batch still ends as `FAIL` because the required live browser smoke did not
fully pass. The remaining issue is now a narrower dashboard-content assertion:
the current page does not satisfy the verifier's expected
`当前状态说明`/status-explain copy.

The next valid batch should stay scoped to the dashboard surface itself and
decide whether the missing status-explain token belongs to:

- frontend dashboard rendering text alignment, or
- backend dashboard entry semantic content for that specific explain field.
