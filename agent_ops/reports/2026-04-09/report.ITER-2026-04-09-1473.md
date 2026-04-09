# ITER-2026-04-09-1473 Report

## Batch
- Batch: `1/1`
- Mode: `implement`

## Change summary
- `frontend/apps/web/src/pages/ListPage.vue`
  - 调整 `showBatchBar` 判定：仅在 `showSelectionColumn` 且 `groupedRows.length === 0` 时显示批量操作条。
  - 分组模式下隐藏 batch bar，避免“不可勾选但可批量操作”的交互冲突。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1473.yaml` ✅
- `rg -n "const showBatchBar = computed" frontend/apps/web/src/pages/ListPage.vue` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅前端显示门控收敛，不涉及业务数据与权限。

## Rollback suggestion
- `git restore frontend/apps/web/src/pages/ListPage.vue`

## Next suggestion
- 下一批继续收敛列表交互：搜索/筛选/排序分区顺序与显隐规则，随后再跑一次阶段 verify。
