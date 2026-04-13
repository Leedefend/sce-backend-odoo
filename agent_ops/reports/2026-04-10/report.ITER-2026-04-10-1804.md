# ITER-2026-04-10-1804 Report

## Batch
- Batch: `FORM-Diagnose-R2`
- Mode: `implement`
- Stage: `tab projection root fix`

## Architecture declaration
- Layer Target: `Frontend contract-consumer runtime`
- Module: `detailLayoutRuntime layout->shell projection`
- Module Ownership: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: `layout_tree` 已含 notebook/page，但 `detail_shell_raw tab=0`，需修复前端投影根因。

## Change summary
- 在 `buildNotebookShell` 中增加递归 page 回收，避免仅依赖 notebook 直接子节点导致丢 tab。
- notebook tab 生成增加 key 去重，避免重复页签再次出现。
- synthetic notebook 的 orphan pages 来源改为全树递归收集，不再仅限 top-level page。
- 保持 single-source：仍只消费 `views.form.layout`，未引入语义层二次真值。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1804.yaml` → `PASS`
- `rg -n "collectPageNodesRecursively|buildDetailShellViewsFromTree|detail_shell_notebook_orphan_pages" frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts` → `PASS`
- `make frontend.restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`low`
- 风险说明：仅调整前端布局投影逻辑，不改变后端契约与业务事实。

## Rollback suggestion
- `git restore frontend/apps/web/src/app/runtime/detailLayoutRuntime.ts`

## Next suggestion
- 刷新同一记录并回传结构摘要，目标应满足：`pipeline(detail_shell_raw) tab > 0` 且 `delta(layout-page - projected)=0`。
