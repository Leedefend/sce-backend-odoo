# Project Dashboard Auth Bridge Recovery CG

## Goal

Recover the verifier-side auth bridge after `/web/login` fallback so the smoke
continues with a valid frontend bearer token instead of stalling on tokenless
post-login API calls.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-VERIFY-PROJECT-DASHBOARD-AUTH-BRIDGE-RECOVERY-CG.yaml`
   - PASS
2. `git diff --check -- agent_ops/tasks/ITER-2026-04-20-VERIFY-PROJECT-DASHBOARD-AUTH-BRIDGE-RECOVERY-CG.yaml docs/verify/project_dashboard_auth_bridge_recovery_cg_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
   - PASS
3. `make verify.portal.project_dashboard_primary_entry_browser_smoke.host BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`
   - FAIL
   - Artifact: `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T062904Z/`
   - But the failure frontier moved materially:
     - `login_intent:done` now succeeds at attempt 1
     - `backend_entry:resolve:done` returns `/s/project.management`
     - `login_mode` converges to `token_bootstrap`
     - `login_form_fallback_used` is now `false`
     - the verifier reaches `dashboard_wait:start` directly
   - Final error:
     - `page.waitForFunction: Timeout 10000ms exceeded.`

## Conclusion

This batch repaired the verifier auth bridge. The remaining failure is no
longer caused by tokenless post-login API calls or by `/web/login` fallback.
The next blocker is the real project dashboard semantic/runtime surface after
successful token bootstrap and scene entry.
