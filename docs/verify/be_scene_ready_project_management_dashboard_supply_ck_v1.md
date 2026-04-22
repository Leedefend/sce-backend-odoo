# BE Scene-Ready Project Management Dashboard Supply CK

## Goal

Restore `project.management` dashboard startup semantics on
`system.init.scene_ready_contract_v1` so the startup contract no longer emits a
route-only minimal scene row.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-BE-SCENE-READY-PROJECT-MANAGEMENT-DASHBOARD-SUPPLY-CK.yaml`
   - PASS
2. `python3 -m py_compile addons/smart_core/core/scene_merge_resolver.py addons/smart_construction_scene/bootstrap/register_scene_providers.py addons/smart_construction_scene/profiles/project_dashboard_scene_content.py addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py`
   - PASS
3. `python3 addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py`
   - PASS
   - `6` lightweight assertions passed
   - coverage now includes:
     - `project.management` provider export shape
     - provider merge of dashboard `page_type/layout_mode` into startup contract
4. Direct runtime diagnosis against `http://127.0.0.1:5174/api/v1/intent?db=sc_demo`
   - PASS
   - `system.init.scene_ready_contract_v1.scenes[*].project.management` now contains:
     - `scene.page=project.management.dashboard`
     - `page.key=project.management.dashboard`
     - `page.page_type=dashboard`
     - `page.layout_mode=dashboard`
5. `make verify.portal.project_dashboard_primary_entry_browser_smoke.host BASE_URL=http://127.0.0.1:5174 DB_NAME=sc_demo E2E_LOGIN=wutao E2E_PASSWORD=demo`
   - FAIL
   - Artifact: `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260420T070759Z/`
   - The verifier still times out in `detectDashboardProfile`
   - Latest timeout snapshot still shows:
     - `视图切换 看板 列表 表单`
     - `项目驾驶舱 0 条记录 · 排序：编号 升序`
     - `正在加载看板...`

## Conclusion

This batch restored the backend startup semantic supply successfully, but the
batch result is still `FAIL` because the required live browser verification did
not converge.

The backend battlefield result is now frozen:
`system.init.scene_ready_contract_v1` can supply dashboard startup semantics
for `project.management`.

The remaining blocker has shifted back to the frontend consumer/runtime path:
the browser still resolves `/s/project.management` into
`SceneView -> ActionView -> KanbanPage` content even after the startup contract
provides dashboard semantics.

The next valid batch should reopen the frontend generic consumer path and use
the newly restored startup semantics, rather than continuing to patch backend
scene supply.
