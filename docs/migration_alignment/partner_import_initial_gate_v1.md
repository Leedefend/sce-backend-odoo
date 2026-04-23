# Partner 导入初始门禁 v1

任务：`ITER-2026-04-13-1842`

## 当前结论

状态：`PASS_WITH_IMPORT_BLOCKED`

本轮不允许直接导入 partner，也不允许回填合同 `partner_id`。

## 允许进入下一轮的内容

- 生成 partner 候选确认表；
- 对 `company_single` 进行低风险候选分层；
- 对 `company_multiple`、`cross_source_conflict`、`defer` 输出人工确认清单；
- 设计 partner 创建/复用策略；
- 设计 legacy identity 字段或外部 ID 对照策略。

## 当前禁止内容

- 不创建 `res.partner`；
- 不写合同；
- 不回填 `construction.contract.partner_id`；
- 不按名称自动合并 partner；
- 不把 supplier 与 company 同名记录自动视为同一主体；
- 不处理合同、付款、结算、税务正式导入。

## 阻塞项

| 阻塞项 | 说明 |
|---|---|
| 重名 | company 源有 515 个重名名称，supplier 源有 80 个重名名称 |
| 跨源冲突 | 8 个合同相对方文本同时命中 company/supplier，覆盖 123 行合同 |
| 未覆盖 | 63 个合同相对方文本未被两个源覆盖，覆盖 79 行合同 |
| 方向待定 | 合同源中仍有 139 行方向待定，不进入 partner 安全回填 |

## 下一轮门槛

进入任何 partner 写入前，至少需要完成：

1. 候选表字段定义；
2. 唯一性策略；
3. 创建/复用判定规则；
4. 人工确认要求；
5. dry-run 写入结果格式；
6. 回滚锁定字段策略。

