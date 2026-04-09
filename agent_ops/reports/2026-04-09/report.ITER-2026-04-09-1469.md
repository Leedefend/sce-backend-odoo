# ITER-2026-04-09-1469 Report

## Batch
- Batch: `1/1`
- Mode: `implement`

## Change summary
- `frontend/apps/web/src/views/ActionView.vue`
  - 新增 `dedupeToolbarChipsByKey`，对 saved/group toolbar 芯片按 `key` 去重，避免重复候选导致计数偏差。
  - `listSavedFilterCountLabel` 改为基于 `listSavedFilterOptions`（即实际传给 `ListPage/PageToolbar` 的集合）计算。
  - `listGroupByCountLabel` 改为基于 `listGroupByToolbarOptions`（即实际可用分组选项）计算。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-09-1469.yaml` ✅
- `rg -n "listSavedFilterCountLabel|listGroupByCountLabel|listSearchPanelCountLabel" frontend/apps/web/src/views/ActionView.vue` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 说明：仅前端消费口径收敛，不触达后端契约、业务事实、ACL。

## Rollback suggestion
- `git restore frontend/apps/web/src/views/ActionView.vue`

## Next suggestion
- 进入同家族下一批：收敛 `PageToolbar/ListPage` 的搜索/分类/排序显隐与交互结构（active chips + advanced filters）到原生表达口径。
