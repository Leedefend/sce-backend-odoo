# 合同相对方强证据下一轮门禁 v1

任务：`ITER-2026-04-13-1845`

## 当前状态

状态：`PASS_WITH_IMPORT_BLOCKED`

628 行强证据候选表已生成，但 partner 写入和合同写入仍未放行。

## 下一轮建议

下一轮建议：

`ITER-2026-04-13-1846 强证据 partner 创建 dry-run 设计专项`

范围只处理：

- `legacy_contract_deleted_flag = 0`
- `company_deleted_flag = 0`
- `evidence_type = repayment_single_counterparty`

按当前候选表，理论上最多 610 行可进入下一轮 dry-run 评估；实际数量需要下一轮按去重 partner ID 再计算。

## 必须继续阻断

禁止直接写入：

- 合同删除态 12 行；
- company 删除态 6 行；
- 多回款相对方合同 48 个；
- 仅靠 `FBF` / `CBF` 文本命中的合同；
- supplier-only 命中；
- 未经人工确认的任何 partner 或合同。

## 写入前仍需确定

- partner legacy ID 字段或外部 ID 存储位置；
- company 主源字段到 `res.partner` 的安全字段切片；
- 是否创建 company 侧 partner 时同步 supplier 银行资料；
- partner 回滚精确锁定键；
- 合同 `partner_id` 何时回填。

## 结论

具备进入 partner 创建 dry-run 设计条件，不具备真实 partner 创建或合同写入条件。

