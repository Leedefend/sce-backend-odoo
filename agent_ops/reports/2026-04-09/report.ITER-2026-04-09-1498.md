# ITER-2026-04-09-1498 Report

## Batch
- Batch: `1/1`
- Mode: `implement`
- Stage: `Batch 1 - 菜单事实扫描器`

## Architecture declaration
- Layer Target: `Platform fact layer`
- Module: `Menu fact scanner/export`
- Module Ownership: `addons/smart_core/delivery`
- Kernel or Scenario: `kernel`
- Reason: 以 `ir.ui.menu` 为唯一来源建立菜单事实扫描能力，隔离解释层字段。

## Change summary
- 新增 `addons/smart_core/delivery/menu_fact_service.py`
  - 提供 `MenuFactService.export_visible_menu_facts()`。
  - 输出同时包含 `flat` 与 `tree`。
  - 每个节点包含：`menu_id/name/parent_id/complete_name/sequence/action_raw/groups/web_icon/child_ids`。
  - `action_raw` 通过 SQL 读取 `ir_ui_menu.action` 原始值，不做 route/scene 推导。
- 新增 `scripts/verify/menu_fact_export.py`
  - 支持按 `--db/--user-login/--output` 导出菜单事实快照。
  - 默认输出：`artifacts/menu/menu_fact_snapshot_v1.json`。
  - 采用惰性加载 Odoo runtime，`--help` 可在非 Odoo Python 环境执行。
- 新增快照占位产物：`artifacts/menu/menu_fact_snapshot_v1.json`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1498.yaml` ✅
- `python3 scripts/verify/menu_fact_export.py --help` ✅
- `python3 -c "... snapshot_exists ..."` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅新增事实扫描与导出能力；未触及前端、ACL、manifest、财务域。

## Rollback suggestion
- `git restore addons/smart_core/delivery/menu_fact_service.py`
- `git restore scripts/verify/menu_fact_export.py`
- `git restore artifacts/menu/menu_fact_snapshot_v1.json`

## Next suggestion
- 进入 Batch 2：action 原始绑定解析器，在事实层补齐 `action_type/action_id/action_model/action_exists`。
