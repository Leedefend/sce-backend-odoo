# 合同相对方强证据确认计划 v1

任务：`ITER-2026-04-13-1844`

## 目标

用旧库业务事实还原合同相对方，不再优先依赖纯名称文本匹配。

## 首批强证据来源

使用：

- `C_JFHKLR.SGHTID -> T_ProjectContract_Out.Id`
- `C_JFHKLR.WLDWID -> T_Base_CooperatCompany.Id`

当前聚合事实：

| 指标 | 数量 |
|---|---:|
| 可关联合同数 | 676 |
| 回款记录数 | 1857 |
| 单一回款相对方合同 | 628 |
| 多个回款相对方合同 | 48 |

## 下一批应生成的确认表

建议输出：

- `artifacts/migration/contract_counterparty_strong_evidence_candidates_v1.csv`
- `artifacts/migration/contract_counterparty_strong_evidence_summary_v1.json`

建议字段：

- `legacy_contract_id`
- `legacy_contract_no`
- `legacy_project_id`
- `contract_title`
- `fbf_text`
- `cbf_text`
- `repayment_partner_id`
- `repayment_partner_name`
- `repayment_rows`
- `evidence_type`
- `evidence_strength`
- `manual_confirm_required`
- `confirmed_partner_action`
- `review_note`

## 分批规则

第一批只允许：

- `SGHTID` 能关联到合同；
- 同一合同下 `WLDWID` 只有一个；
- `WLDWID` 能命中 `T_Base_CooperatCompany.Id`；
- company 记录未删除或删除态已人工确认可保留；
- 合同不属于旧系统删除态。

第一批禁止：

- 多回款相对方合同 48 个；
- 仅靠 `FBF` / `CBF` 文本命中的合同；
- supplier-only 命中；
- company/supplier 跨源同名自动合并；
- 直接写入 `res.partner` 或 `construction.contract`。

## 当前结论

具备进入“强证据候选表生成”下一批的条件；不具备 partner 或合同正式写入条件。

