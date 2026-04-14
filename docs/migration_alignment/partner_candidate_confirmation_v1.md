# Partner 候选确认表 v1

任务：`ITER-2026-04-13-1843`

## 产物

- 候选确认表：`artifacts/migration/partner_candidate_confirmation_v1.csv`
- 汇总结果：`artifacts/migration/partner_candidate_confirmation_summary_v1.json`

本轮只生成候选表，不创建 `res.partner`，不写合同。

## 候选规模

| 指标 | 数量 |
|---|---:|
| 合同相对方文本 | 568 |
| 覆盖合同行数 | 1554 |
| company_single | 419 |
| company_multiple | 78 |
| cross_source_conflict | 8 |
| defer | 63 |

按合同行数：

| 类型 | 合同行数 |
|---|---:|
| company_single | 738 |
| company_multiple | 614 |
| cross_source_conflict | 123 |
| defer | 79 |

## CSV 字段

| 字段 | 含义 |
|---|---|
| `counterparty_text` | 合同中推断出的相对方文本 |
| `normalized_name` | 用于匹配的归一化名称 |
| `contract_rows` | 该相对方覆盖的合同行数 |
| `match_type` | 匹配类型 |
| `recommended_action` | 推荐人工处理动作 |
| `manual_confirm_required` | 是否需要人工确认，本轮固定为 `yes` |
| `auto_create_allowed` | 是否允许自动创建，本轮固定为 `no` |
| `existing_partner_hint` | 当前 partner baseline 中是否疑似已有 |
| `company_candidate_count` | company 源候选数 |
| `supplier_candidate_count` | supplier 源候选数 |
| `source` / `source_id` | 默认展示的候选来源与旧源 ID |
| `source_name` / `source_short_name` | 旧源名称与简称 |
| `source_code` | 旧源编码或统一社会信用代码候选 |
| `source_address` | 旧源地址 |
| `source_contact` / `source_phone` | 旧源联系人与电话 |
| `confirm_result` | 人工确认结果，待填 |
| `confirmed_partner_action` | 人工确认后的动作，待填 |
| `confirmed_source` / `confirmed_source_id` | 人工确认后的来源，待填 |
| `review_note` | 人工备注 |

## 使用结论

`company_single` 可作为下一轮人工确认优先队列，但仍不等于自动创建。`company_multiple`、`cross_source_conflict`、`defer` 均需要人工确认或补源后才能进入 partner 写入 dry-run。

