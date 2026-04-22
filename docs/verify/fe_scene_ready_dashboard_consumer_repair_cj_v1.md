# FE Scene-Ready Dashboard Consumer Repair CJ

## Goal

Repair the frontend generic scene consumer so a self-routed workspace scene can
render its dashboard surface when the startup contract provides dashboard page
semantics.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-SCENE-READY-DASHBOARD-CONSUMER-REPAIR-CJ.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing chunk-size warning only
4. `make verify.portal.project_dashboard_primary_entry_browser_smoke.host BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`
   - FAIL
   - Artifact: `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T065042Z/`
   - The page no longer shows the earlier `0 条记录 / 正在加载看板...` stall
   - But it still resolves to `ActionView` list/kanban content with
     `视图切换 看板 列表 表单` and `项目驾驶舱 40 条记录 · 当前排序：Sequence`
   - The verifier still times out waiting for dashboard semantic markers
5. Direct `system.init` scene-ready diagnosis against `http://127.0.0.1:5174/api/v1/intent?db=sc_demo`
   - FAIL
   - The `project.management` scene row currently contains:
     - `scene.key=project.management`
     - `page.route=/s/project.management`
     - minimal `zones`
     - toolbar actions targeting `action_id=520`, `menu_id=315`
   - It does not contain dashboard `page_type/layout_mode` semantics

## Conclusion

This batch is `FAIL`, but the failure is not a frontend code defect in
isolation.

The frontend consumer can only choose a dashboard surface generically if the
startup contract supplies dashboard page semantics. The real blocker is that
`system.init.scene_ready_contract_v1` currently emits a minimal
`project.management` row without those semantics. Continuing with a
frontend-only fix would require a scene-specific patch, which violates the
current battlefield rule.

The next valid batch must move back to backend scene-orchestration semantic
supply for `project.management`, specifically the startup contract path that
feeds `scene_ready_contract_v1`.
