# Real Usability Verify BV

## Task

- Task: `ITER-2026-04-20-REAL-USABILITY-WUTAO-VERIFY-BV`
- Date: `2026-04-20`
- Branch: `codex/next-round`
- Account: `wutao / demo`
- Target frontend: `http://127.0.0.1:5174`
- Target backend API: `http://127.0.0.1:8069`

## Scope

This batch is verify-only. It does not patch runtime code. It freezes the real
usability status of the active custom frontend and backend runtime under the
requested demo account.

## Commands

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-REAL-USABILITY-WUTAO-VERIFY-BV.yaml`
2. `DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo make verify.portal.project_dashboard_primary_entry_browser_smoke.host`
3. `DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo make verify.portal.unified_system_menu_click_usability_smoke.host`

## Code Result

- `FAIL`
- The project dashboard primary-entry browser smoke reaches the custom frontend
  and logs in with `wutao`, but fails on the runtime assertion
  `dashboard missing status explain`.
- Evidence:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T030147Z/summary.json`
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T030147Z/failure.png`

Key facts frozen by the artifact:

- `project_route_url_used`: `http://127.0.0.1:5174/s/project.management?db=sc_demo`
- `backend_scene_key`: `project.dashboard`
- `dashboard_profile`: `old`
- `backend_project_context` already exists, but the dashboard page still does
  not satisfy the required status-explain assertion.

## Contract Result

- `FAIL`
- The menu click usability smoke shows that the custom frontend can log in and
  fetch menus, but most menu leaves still fall into contract-context loss.
- Evidence:
  - `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T030241Z/summary.json`
  - `artifacts/codex/unified-system-menu-click-usability-smoke/20260420T030241Z/failed_cases.json`

Frozen totals:

- `leaf_count = 31`
- `fail_count = 28`
- `used_api_base = http://127.0.0.1:8069`

Failure classes observed:

1. Scene key exists, but navigation still degrades to workbench with
   `reason=CONTRACT_CONTEXT_MISSING`.
   Examples:
   - `我的工作` -> `scene=my_work.workspace`
   - `预算/成本` -> `scene=cost.project_budget`
   - `项目驾驶舱` under `看板中心` -> `scene=project.dashboard`
2. Scene identity is missing on menu delivery, so navigation degrades to
   `diag=menu_route_missing_scene_identity`.
   Examples:
   - `合同汇总` action `513`
   - `投标管理` action `515`
   - `待我审批（物资计划）` action `527`

Important contrast:

- `系统菜单/项目管理/项目驾驶舱` with `scene_key=project.management` and route
  `/s/project.management` is `PASS`.
- `系统菜单/看板中心/项目驾驶舱` with `scene_key=project.dashboard` is `FAIL` and
  degrades to workbench.

This means the current runtime is not uniformly scene-oriented even though part
of the project-management entry path already works.

## Environment Result

- `conditional`
- The first smoke invocation failed because the script defaulted to host target
  `8070`, which is not the active custom frontend requested by the user.
- After rebinding the browser smoke to `BASE_URL=http://127.0.0.1:5174`, both
  browser verifications executed against the requested custom frontend and
  produced business-relevant failures.
- Therefore the final failure conclusion is considered runtime-valid for the
  custom frontend path.

## Gate Result

- `validate_task`: `PASS`
- `project_dashboard_primary_entry_browser_smoke`: `FAIL`
- `unified_system_menu_click_usability_smoke`: `FAIL`
- Overall gate decision: `FAIL`

## Conclusion

The custom frontend route-boundary topic is not actually closed under real
`wutao / demo` usability verification.

The currently frozen backend/frontend misalignment is:

1. `project.management` entry is reachable, but the page still renders the old
   dashboard profile and misses the required status-explain semantic.
2. Most menu leaves still cannot uniquely consume scene-oriented contract
   output and degrade to workbench with `CONTRACT_CONTEXT_MISSING`.
3. A subset of menu nodes still lacks scene identity entirely and degrades with
   `menu_route_missing_scene_identity`.

## Next Batch Suggestion

Open a bounded backend-first repair batch for scene-oriented menu and dashboard
semantic supply:

1. Recheck why `project.management` still resolves to `dashboard_profile=old`
   under the custom frontend path.
2. Screen the backend scene/menu output for the 28 failing menu leaves and
   classify which ones are missing `scene_key/route/entry_target` versus which
   ones have a scene key but lack sufficient contract context.
3. Only after the backend semantic supply is repaired, run a frontend consumer
   fix batch if any residual consumer bug still remains.
