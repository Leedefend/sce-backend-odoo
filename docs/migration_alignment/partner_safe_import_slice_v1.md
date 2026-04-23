# Partner 首轮安全导入字段切片 v1

任务：`ITER-2026-04-13-1849`

## 首轮允许导入

仅针对强证据 `T_Base_CooperatCompany` 候选：

| 输入字段 | 新系统字段 | 说明 |
|---|---|---|
| `legacy_partner_id` | `legacy_partner_id` | 旧 company ID，主锁定键 |
| 固定值 `cooperat_company` | `legacy_partner_source` | 来源表 |
| `partner_name` | `name` | partner 显示名称 |
| `partner_name` | `legacy_partner_name` | 旧名称快照 |
| `company_credit_code` | `legacy_credit_code` | 辅助校验 |
| `company_tax_no` | `legacy_tax_no` | 辅助校验 |
| 固定值 `0` | `legacy_deleted_flag` | 本切片已过滤删除态 |
| `source_evidence` | `legacy_source_evidence` | 证据路径 |
| 固定值 `company` | `company_type` | 公司类型 partner |

## 首轮禁止导入

- 银行账号；
- supplier 资质；
- supplier 分类；
- 跨源合并关系；
- 合同 `partner_id` 回填；
- 付款/回款/结算信息；
- 删除态 partner；
- 缺少旧系统 ID 的 partner。

## 待补字段

- supplier 银行资料；
- 联系人和电话；
- 地址；
- 发票类型；
- 纳税人类别；
- 资质附件；
- company/supplier 同名合并关系。

## 门禁

下一轮只能做 no-DB dry-run 或小样本 create-only 试写设计。真实写入前必须具备 rollback dry-run 和写后只读复核。

