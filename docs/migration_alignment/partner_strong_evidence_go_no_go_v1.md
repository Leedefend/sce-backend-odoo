# 强证据 Partner GO/NO-GO v1

任务：`ITER-2026-04-13-1848`

## 当前结论

真实 partner 创建：`NO-GO`

partner 小样本试写准备：`NOT_READY`

## 为什么仍然 NO-GO

虽然 dry-run 结果显示 369 个候选均为 `create_candidate`，但正式写入前还缺：

1. `res.partner` 上 legacy partner identity 的存储策略；
2. 强证据 partner 安全字段切片；
3. create-only 小样本范围；
4. rollback 精确锁定策略；
5. 写后只读复核方案；
6. 与 supplier 补充资料的后续合并边界。

## 可进入下一批

下一批应为：

`Partner 模型 legacy identity 与安全字段切片专项`

目标：

- 只围绕 `res.partner`；
- 评估是否新增 `legacy_partner_id` / `legacy_partner_source` 等对照字段；
- 定义首轮 partner create-only 安全字段；
- 不创建 partner。

## 禁止事项

- 不直接写入 369 个 partner；
- 不回填合同；
- 不处理 supplier 银行资料合并；
- 不处理付款/回款正式迁移；
- 不做合同写入。

