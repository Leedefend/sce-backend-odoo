# ITER-2026-04-10-1782 Report

## Batch
- Batch: `FORM-Consumer-Align-R6`
- Mode: `implement`
- Stage: `layout tree dedup collapse fix`

## Architecture declaration
- Layer Target: `Frontend contract-consumer runtime`
- Module: `form layout tree projection`
- Module Ownership: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 用户持续反馈结构缺失，排查到 layoutTrees 的全局字段去重会导致 page/group 被剪枝。

## Change summary
- 在 `layoutTrees` 投影链路中移除全局字段去重（`used`）依赖：
  - `buildFieldNode` 不再因字段已出现而直接跳过；
  - 避免重复字段在后续 page/group 被吃掉，导致结构容器空化并被 prune。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1782.yaml` → `PASS`
- `rg` 探针检查 → `PASS`
- `make frontend.restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium-low`
- 风险说明：
  - 可能出现部分字段在不同结构区重复显示，这是对原生可重复字段语义的兼容性提升；
  - 不影响后端契约和业务执行。

## Rollback suggestion
- 文件级回滚：
  - `git restore frontend/apps/web/src/pages/ContractFormPage.vue`

## Next suggestion
- 请刷新并复测同一详情页结构可见性；
- 如仍异常，下一步输出“layout 节点投影审计 JSON（节点总数/投影数/丢弃原因）”。
