# ITER-2026-04-10-1796 Report

## Batch
- Batch: `FORM-Consumer-Align-R20`
- Mode: `implement`
- Stage: `tab duplication elimination and label fidelity fix`

## Architecture declaration
- Layer Target: `Frontend contract-consumer runtime`
- Module: `tab rendering/projection alignment`
- Module Ownership: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 页面仍不达标，存在重复 tab 和业务名丢失，本轮做消费链根因修复。

## Change summary
- `DetailShellLayout.vue`：tab 名称优先保留 contract 原始 label；仅对极少数通用占位标签（`page/tab/notebook/default`）做兜底替换。
- `ContractFormPage.vue`：新增 `tabSignature` + `dedupeTabs`，在投影后按内容签名去重，消除重复页签。
- 结合已有过滤规则，保留有语义标签的业务 tab，同时去掉同内容重复项。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1796.yaml` → `PASS`
- `rg -n "normalizeTabLabel|dedupeTabs|tabSignature" frontend/apps/web/src/components/template/DetailShellLayout.vue frontend/apps/web/src/pages/ContractFormPage.vue` → `PASS`
- `make frontend.restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`low`
- 风险说明：仅前端投影/命名策略调整，不影响后端 contract 与业务写入。

## Rollback suggestion
- 文件级回滚：
  - `git restore frontend/apps/web/src/components/template/DetailShellLayout.vue frontend/apps/web/src/pages/ContractFormPage.vue`

## Next suggestion
- 刷新并回传新截图/摘要；若仍有缺失，下一轮直接做“tab->section 字段密度阈值”对齐。
