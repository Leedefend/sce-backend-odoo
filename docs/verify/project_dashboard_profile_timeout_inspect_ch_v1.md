# Project Dashboard Profile Timeout Inspect CH

## Goal

Capture a bounded semantic snapshot when `dashboard_wait` times out on
`/s/project.management`, so the next repair batch can target the actual page
surface instead of a generic timeout.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-VERIFY-PROJECT-DASHBOARD-PROFILE-TIMEOUT-INSPECT-CH.yaml`
   - PASS
2. `git diff --check -- agent_ops/tasks/ITER-2026-04-20-VERIFY-PROJECT-DASHBOARD-PROFILE-TIMEOUT-INSPECT-CH.yaml docs/verify/project_dashboard_profile_timeout_inspect_ch_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
   - PASS
3. `make verify.portal.project_dashboard_primary_entry_browser_smoke.host BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`
   - FAIL
   - Artifact: `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T063353Z/`
   - New evidence:
     - `dashboard_timeout_snapshot.json` is now emitted on timeout
     - the page is already on `/s/project.management`
     - `has_native_navbar=false`
     - `has_scene_eyebrow=true`
     - `has_menu_tree=true`
     - visible text excerpt shows:
       - `导航菜单 ... 8 项`
       - `项目驾驶舱 0 条记录`
       - `加载中`
       - `正在加载看板...`

## Conclusion

This batch replaced the generic dashboard timeout with a concrete runtime
surface snapshot. The remaining blocker is now clearly inside the real
`project.management` dashboard data/semantic loading path, not login, token
bootstrap, or native Odoo surface fallback.
