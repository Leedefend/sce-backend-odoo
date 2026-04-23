# 完整新库重建流水线门禁 v1

任务：`ITER-2026-04-13-1847`

## 总门禁

后续任何真实写入批次都必须回答：

1. 是否可在空新库重复运行；
2. 是否有 legacy identity；
3. 是否幂等；
4. 是否可 dry-run；
5. 是否可回滚；
6. 是否有写后只读复核；
7. 是否不依赖一次性人工状态；
8. 是否不依赖当前演示库偶然数据。

## Partner 门禁

partner 写入前必须具备：

- `legacy_partner_id` 字段或可追踪外部 ID 策略；
- partner 创建/复用 dry-run；
- 删除态处理策略；
- supplier 补充资料合并策略；
- 回滚锁定策略；
- 小样本写入授权。

## Contract 门禁

合同写入前必须具备：

- partner readiness；
- project readiness；
- 合同 legacy identity；
- 合同方向策略；
- 合同删除态策略；
- 合同金额/税务/行项目处理策略；
- 合同状态是否回放的明确结论。

## 当前下一步

执行：

`no-DB-write partner dry-run importer for 369 strong-evidence candidates`

不执行：

- partner 真实创建；
- 合同真实创建；
- partner_id 回填；
- supplier 补充合并。

