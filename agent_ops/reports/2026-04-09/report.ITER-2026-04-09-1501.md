# ITER-2026-04-09-1501 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Batch 4 - 菜单事实统一出口`

## Architecture declaration
- Layer Target: `Platform fact layer`
- Module: `Platform menu facts API`
- Module Ownership: `smart_core controllers`
- Kernel or Scenario: `kernel`
- Reason: 将菜单事实统一从 `/api/menu/tree` 发布为 facts-only 口径。

## Change summary
- 更新 `addons/smart_core/controllers/platform_menu_api.py`
  - `/api/menu/tree` 改为调用 `MenuFactService` 输出 `nav_fact`。
  - 返回结构包含 `flat` 与 `tree` 两类事实节点。
  - 节点字段固定包含：
    - `menu_id/key/name/parent_id/complete_name/sequence/groups/web_icon/has_children`
    - `action_raw/action_type/action_id/action_exists/action_meta`
    - `children`（树形）或 `child_ids`（扁平）
  - 不返回 `route/scene_key/target_type/delivery_mode/active_match`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1501.yaml` ✅
- `rg -n "MenuFactService|nav_fact|action_meta|has_children" addons/smart_core/controllers/platform_menu_api.py` ✅
- `python3 -c "... forbidden_hits ..."` ✅（结果为空）

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅菜单事实 API 出口收敛，不涉及前端与权限数据写入。

## Rollback suggestion
- `git restore addons/smart_core/controllers/platform_menu_api.py`

## Next suggestion
- 进入 Batch 5：角色可见性样本校验（管理/项目/财务）。
