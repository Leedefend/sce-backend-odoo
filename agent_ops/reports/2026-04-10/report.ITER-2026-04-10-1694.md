# ITER-2026-04-10-1694 Report

## Batch
- Batch: `P1-Batch23`
- Mode: `implement`
- Stage: `budget menu INTERNAL_ERROR root-cause fix`

## Architecture declaration
- Layer Target: `Backend intent handler runtime`
- Module: `api.data list ordering guard`
- Module Ownership: `smart_core handlers`
- Kernel or Scenario: `scenario`
- Reason: 修复 `project.budget` 列表查询因无效排序字段导致的 500。

## Root cause
- 后端日志显示：`ValueError: Invalid field 'parent_path' on model 'project.budget'`。
- 触发点：`api.data` 的 `list` 查询直接把 `order=parent_path desc` 透传给 ORM。

## Change summary
- 更新 `addons/smart_core/handlers/api_data.py`
  - 新增 `_sanitize_order`：只保留模型存在的排序字段；非法字段丢弃。
  - 当全部排序项非法时回退到 `id desc`，避免抛异常。
  - `list` 与 `export_csv` 查询统一使用 `order_safe`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1694.yaml` ✅
- 定向复现（修复前同输入）✅
  - `api.data list model=project.budget order=parent_path desc` 返回 `ok=true`，不再 INTERNAL_ERROR。
- `python3 scripts/verify/v2_app_governance_gate_audit.py --json` ✅ (`27/27 PASS`)
- `node scripts/verify/unified_system_menu_click_usability_smoke.mjs` ✅
  - artifact: `artifacts/codex/unified-system-menu-click-usability-smoke/20260411T155113Z/summary.json`
  - result: `leaf_count=28`, `fail_count=0`

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：修复是通用防御型兜底，不改变业务语义，仅避免非法排序字段导致崩溃。

## Rollback suggestion
- `git restore addons/smart_core/handlers/api_data.py`

## Next suggestion
- 请你刷新前端后重试“预算/成本”；若仍异常，我继续按 trace_id 追单点入口链路。
