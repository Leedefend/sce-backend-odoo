# 强证据 Partner 创建 Dry-Run 输入表 v1

任务：`ITER-2026-04-13-1846`

## 产物

- 输入表：`artifacts/migration/partner_strong_evidence_dry_run_input_v1.csv`
- 汇总：`artifacts/migration/partner_strong_evidence_dry_run_input_summary_v1.json`

本轮只生成 partner 创建 dry-run 输入，不创建 `res.partner`。

## 输入过滤

来源：

- `artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv`

过滤条件：

- `legacy_contract_deleted_flag = 0`
- `company_deleted_flag = 0`
- `repayment_partner_id` 非空

## 结果

| 指标 | 数量 |
|---|---:|
| 输入强证据合同候选 | 628 |
| 过滤后合格合同行 | 610 |
| 去重 partner 候选 | 369 |
| 有统一社会信用代码 | 28 |
| 缺统一社会信用代码 | 341 |
| 有税号 | 1 |
| 缺税号 | 368 |

## 关键判断

统一社会信用代码覆盖率较低，不能把信用代码作为本批次唯一主锁定键。下一轮 partner dry-run 应优先使用：

1. `legacy_partner_id` 即 `T_Base_CooperatCompany.Id`
2. `partner_name`
3. `company_credit_code` / `company_tax_no` 作为辅助校验

## CSV 字段

| 字段 | 含义 |
|---|---|
| `legacy_partner_id` | 旧 company ID |
| `partner_name` | partner 候选名称 |
| `company_credit_code` | 统一社会信用代码 |
| `company_tax_no` | 税号 |
| `source` | 来源表 |
| `source_evidence` | 强证据路径 |
| `linked_contract_count` | 关联强证据合同数 |
| `linked_repayment_rows` | 关联回款记录数 |
| `sample_legacy_contract_id` | 样例旧合同 ID |
| `sample_legacy_contract_no` | 样例旧合同编号 |
| `manual_confirm_required` | 是否需人工确认 |
| `auto_create_allowed` | 是否允许自动创建，本轮固定为 `no` |
| `dry_run_action` | 下一轮 dry-run 建议动作 |
| `review_note` | 人工备注 |

