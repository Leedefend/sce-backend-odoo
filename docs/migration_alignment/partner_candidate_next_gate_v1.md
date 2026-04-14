# Partner 候选下一轮门禁 v1

任务：`ITER-2026-04-13-1843`

## 当前状态

状态：`PASS_WITH_IMPORT_BLOCKED`

候选确认表已经生成，但 partner 写入仍未放行。

## 写入前必须满足

进入 partner 创建 dry-run 前，必须完成：

1. `company_single` 的人工确认；
2. 高频 `company_multiple` 的选主或合并策略；
3. 高频 `cross_source_conflict` 的来源优先级确认；
4. `defer` 的补源或拒绝策略；
5. partner legacy identity 字段或外部 ID 对照策略；
6. partner rollback 锁定策略；
7. partner 写入 dry-run 脚本设计。

## 推荐下一批

下一批建议为：

`ITER-2026-04-13-1844 Partner company_single 人工确认切片与 dry-run 设计专项`

建议只处理 `company_single=419` 这一组，不处理重复、跨源冲突和未覆盖值。

## 明确禁止

- 不直接创建 568 个 partner；
- 不直接写 419 个 `company_single`；
- 不回填合同；
- 不把 supplier 冲突记录自动覆盖 company；
- 不做合同正式导入。

