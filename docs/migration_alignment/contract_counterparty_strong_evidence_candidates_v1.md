# 合同相对方强证据候选表 v1

任务：`ITER-2026-04-13-1845`

## 产物

- 候选表：`artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv`
- 汇总：`artifacts/migration/contract_counterparty_strong_evidence_summary_v1.json`

本轮只读旧库并生成本地候选表，不创建 partner，不导入合同。

## 证据来源

候选逻辑：

- `C_JFHKLR.SGHTID -> T_ProjectContract_Out.Id`
- `C_JFHKLR.WLDWID -> T_Base_CooperatCompany.Id`
- 同一合同下 `COUNT(DISTINCT WLDWID) = 1`

这代表该合同在回款记录中只有一个往来单位，可作为强证据候选。

## 结果

| 指标 | 数量 |
|---|---:|
| 强证据候选合同 | 628 |
| 合同删除态 `DEL=0` | 616 |
| 合同删除态 `DEL=1` | 12 |
| company 删除态 `DEL=0` | 622 |
| company 删除态 `DEL=1` | 6 |

## CSV 字段

| 字段 | 含义 |
|---|---|
| `legacy_contract_id` | 旧合同 ID |
| `legacy_document_no` | 旧单据编号 |
| `legacy_contract_no` | 旧合同编号 |
| `legacy_project_id` | 旧项目 ID |
| `contract_title` | 旧合同标题 |
| `fbf_text` | 合同 `FBF` 文本 |
| `cbf_text` | 合同 `CBF` 文本 |
| `legacy_contract_deleted_flag` | 旧合同删除标志 |
| `repayment_partner_id` | 回款记录往来单位 ID |
| `repayment_partner_name` | 回款记录往来单位名称 |
| `repayment_rows` | 该合同回款记录数 |
| `company_name` | company 主源单位名称 |
| `company_credit_code` | company 统一社会信用代码 |
| `company_tax_no` | company 税号 |
| `company_deleted_flag` | company 删除标志 |
| `evidence_type` | 证据类型 |
| `evidence_strength` | 证据强度 |
| `manual_confirm_required` | 是否需要人工确认 |
| `confirmed_partner_action` | 人工确认后的动作 |
| `review_note` | 人工备注 |

## 初步使用规则

可进入人工确认优先队列：

- `legacy_contract_deleted_flag = 0`
- `company_deleted_flag = 0`
- `evidence_type = repayment_single_counterparty`

暂不进入写入候选：

- 合同删除态 12 行；
- company 删除态 6 行；
- 人工确认未完成的所有行。

