# Project Dashboard Wait Condition Isolation CD

## Goal

Bound the remaining in-browser wait condition inside
`project_dashboard_primary_entry_browser_smoke.mjs` so the verifier emits a
clean PASS/FAIL result instead of hanging after browser bootstrap.

## Planned Change

1. Add stage-level observability around semantic entry, login fallback, and
   dashboard readiness waits.
2. Convert the longest in-page waits into bounded failures with artifacts.
3. Re-run the host smoke and confirm it now ends with a deterministic verdict.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-VERIFY-PROJECT-DASHBOARD-WAIT-CONDITION-ISOLATION-CD.yaml`
   - PASS
2. `git diff --check -- agent_ops/tasks/ITER-2026-04-20-VERIFY-PROJECT-DASHBOARD-WAIT-CONDITION-ISOLATION-CD.yaml docs/verify/project_dashboard_wait_condition_isolation_cd_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
   - PASS
3. `make restart`
   - PASS
   - Restored the missing `odoo` service; `http://127.0.0.1:8069/web/login?db=sc_demo` returned `200 OK` afterward.
4. `make verify.portal.project_dashboard_primary_entry_browser_smoke.host BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`
   - FAIL
   - Artifact: `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T061244Z/`
   - The verifier now emits a deterministic failure instead of hanging:
     - `login_submit_result.json` shows the custom login page submitted successfully and navigated to `/s/project.management`.
     - The first post-login scene snapshot already reports `暂无导航数据` and `菜单树为空，请尝试刷新初始化。`
     - Final process error: `Error: native_odoo_surface_detected`

## Conclusion

This batch completed the wait-condition isolation goal on the verifier side.
The residual failure is no longer an unbounded browser wait and no longer a
missing-backend runtime. The remaining blocker is a post-login scene/runtime
issue after the browser reaches `/s/project.management`, not the login submit
path itself.
