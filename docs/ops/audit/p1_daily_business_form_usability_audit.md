# P1 Daily Business Form Usability Audit

- audit_login: wutao
- entry_count: 36
- usable_contract_ready_count: 30
- needs_usability_attention_count: 6
- no_contract_count: 0
- create_contract_ok_count: 36
- create_allowed_count: 31
- edit_contract_ok_count: 36
- edit_allowed_count: 31
- attachment_signal_count: 36
- chatter_signal_count: 36

| id | old entry | model | status | create | edit | attachment | chatter | missing sections | missing fields | required fields | gaps |
|---|---|---|---|---|---|---|---|---:|---:|---:|---|
| DBS-019 | 投标报名管理 | tender.bid | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 3 |  |
| DBS-020 | 投标报名费申请 | tender.bid | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 3 |  |
| DBS-021 | 承包人借项目款 | sc.financing.loan | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 8 |  |
| DBS-022 | 承包人还项目款 | sc.financing.loan | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 8 |  |
| DBS-023 | 支付申请 | payment.request | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 6 |  |
| DBS-024 | 扣款单 | sc.tax.deduction.registration | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-025 | 往来单位付款 | sc.payment.execution | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 6 |  |
| DBS-026 | 账户间资金往来 | sc.fund.account.operation | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 7 |  |
| DBS-027 | 扣款实缴登记 | sc.tax.deduction.registration | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-028 | 扣款实缴退回 | sc.tax.deduction.registration | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-029 | 到款确认表 | sc.receipt.income | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 7 |  |
| DBS-030 | 资金日报表 | sc.legacy.fund.daily.snapshot.fact | needs_usability_attention | N | N | Y | Y | 0 | 0 | 6 | create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user |
| DBS-031 | 项目借公司款登记 | sc.financing.loan | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 8 |  |
| DBS-032 | 项目还公司款登记 | sc.financing.loan | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 8 |  |
| DBS-033 | 开票申请 | sc.invoice.registration | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 7 |  |
| DBS-034 | 开票登记 | sc.invoice.registration | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 7 |  |
| DBS-035 | 预缴税款 | sc.tax.deduction.registration | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-036 | 抵扣登记 | sc.tax.deduction.registration | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-037 | 账户 | sc.fund.account | needs_usability_attention | N | N | Y | Y | 0 | 1 | 4 | create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user, missing_expected_form_fields |
| DBS-038 | 进项上报 | sc.tax.deduction.registration | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-039 | 供货合同 | sc.material.purchase.request | needs_usability_attention | N | N | Y | Y | 0 | 0 | 2 | create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user |
| DBS-040 | 入库 | sc.material.inbound | needs_usability_attention | N | N | Y | Y | 0 | 0 | 4 | create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user |
| DBS-041 | 材料结算单 | sc.material.settlement | needs_usability_attention | N | N | Y | Y | 0 | 0 | 4 | create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user |
| DBS-042 | 劳务合同 | sc.labor.request | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 3 |  |
| DBS-043 | 劳务方单 | sc.labor.usage | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 6 |  |
| DBS-044 | 劳务结算 | sc.labor.settlement | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-045 | 分包合同 | sc.subcontract.register | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-046 | 分包方单 | sc.subcontract.request | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 6 |  |
| DBS-047 | 分包结算单 | sc.subcontract.settlement | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-048 | 机械合同 | sc.equipment.request | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 3 |  |
| DBS-049 | 机械台班记录 | sc.equipment.usage | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 8 |  |
| DBS-050 | 机械结算单 | sc.equipment.settlement | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 5 |  |
| DBS-051 | 租赁合同 | sc.material.rental.order | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 6 |  |
| DBS-052 | 租赁结算单 | sc.material.rental.settlement | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 6 |  |
| DBS-053 | 租入 | sc.material.rental.order | usable_contract_ready | Y | Y | Y | Y | 0 | 0 | 6 |  |
| DBS-054 | 施工日志（新） | sc.construction.diary | needs_usability_attention | Y | Y | Y | Y | 0 | 5 | 4 | missing_expected_form_fields |

## Attention Details

### DBS-030 资金日报表
- selected_model: `sc.legacy.fund.daily.snapshot.fact`
- gaps: create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user
- required_create_fields: 隔离公司, 单据口径, 导入批次, 来源记录, 来源表, 日期

### DBS-037 账户
- selected_model: `sc.fund.account`
- missing_form_fields: 排序号
- gaps: create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user, missing_expected_form_fields
- required_create_fields: 公司, 币种, 账户名称, 状态

### DBS-039 供货合同
- selected_model: `sc.material.purchase.request`
- gaps: create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user
- required_create_fields: 申请单号, 项目

### DBS-040 入库
- selected_model: `sc.material.inbound`
- gaps: create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user
- required_create_fields: 入库库位, 入库单号, 项目, 入库仓库

### DBS-041 材料结算单
- selected_model: `sc.material.settlement`
- gaps: create_not_allowed_for_audit_user, edit_not_allowed_for_audit_user
- required_create_fields: 币种, 结算单号, 项目, 供应商

### DBS-054 施工日志（新）
- selected_model: `sc.construction.diary`
- missing_form_fields: 材料进场/送检情况, 设计变更或技术核定, 试块制作, 安全情况, 隐蔽工程验收
- gaps: missing_expected_form_fields
- required_create_fields: 日志编号, 项目, 来源, 状态
