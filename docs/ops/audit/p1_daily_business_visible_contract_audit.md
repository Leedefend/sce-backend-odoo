# P1 Daily Business Visible Contract Audit

- audit_login: wutao
- entry_count: 36
- contract_entry_count: 10
- no_contract_count: 26
- aligned_count: 0
- gap_count: 10
- missing_list_field_count: 530

| id | old entry | domain | selected model | status | missing list fields | missing filters | attachment | chatter |
|---|---|---|---|---|---:|---:|---|---|
| DBS-019 | 投标报名管理 | 投标 | sc.legacy.tender.registration.fact | gap | 6 | 1 | Y | Y |
| DBS-020 | 投标报名费申请 | 投标/付款 | payment.request | gap | 13 | 0 | Y | Y |
| DBS-021 | 承包人借项目款 | 借款 | sc.legacy.financing.loan.fact | gap | 12 | 0 | Y | Y |
| DBS-022 | 承包人还项目款 | 还款 | - | no_contract | 13 | 0 | N | N |
| DBS-023 | 支付申请 | 付款 | payment.request | gap | 18 | 0 | Y | Y |
| DBS-024 | 扣款单 | 扣款 | sc.legacy.deduction.adjustment.line | gap | 10 | 0 | Y | Y |
| DBS-025 | 往来单位付款 | 付款 | - | no_contract | 17 | 0 | N | N |
| DBS-026 | 账户间资金往来 | 资金账户 | sc.legacy.account.transaction.line | gap | 10 | 0 | Y | Y |
| DBS-027 | 扣款实缴登记 | 扣款 | - | no_contract | 11 | 0 | N | N |
| DBS-028 | 扣款实缴退回 | 扣款 | - | no_contract | 10 | 0 | N | N |
| DBS-029 | 到款确认表 | 收款 | sc.legacy.fund.confirmation.line | gap | 16 | 0 | Y | Y |
| DBS-030 | 资金日报表 | 资金报表 | - | no_contract | 14 | 0 | N | N |
| DBS-031 | 项目借公司款登记 | 借款 | sc.legacy.project.fund.balance.fact | gap | 16 | 0 | Y | Y |
| DBS-032 | 项目还公司款登记 | 还款 | - | no_contract | 14 | 0 | N | N |
| DBS-033 | 开票申请 | 发票税务 | - | no_contract | 17 | 0 | N | N |
| DBS-034 | 开票登记 | 发票税务 | sc.legacy.income.invoice.fact | gap | 16 | 0 | Y | Y |
| DBS-035 | 预缴税款 | 发票税务 | - | no_contract | 11 | 0 | N | N |
| DBS-036 | 抵扣登记 | 发票税务 | - | no_contract | 12 | 0 | N | N |
| DBS-037 | 账户 | 资金账户基础 | - | no_contract | 13 | 0 | N | N |
| DBS-038 | 进项上报 | 进项税务 | - | no_contract | 18 | 0 | N | N |
| DBS-039 | 供货合同 | 材料合同 | purchase.order | gap | 14 | 0 | Y | Y |
| DBS-040 | 入库 | 材料入库 | - | no_contract | 22 | 0 | N | N |
| DBS-041 | 材料结算单 | 材料结算 | - | no_contract | 17 | 0 | N | N |
| DBS-042 | 劳务合同 | 劳务合同 | - | no_contract | 20 | 0 | N | N |
| DBS-043 | 劳务方单 | 劳务方单 | - | no_contract | 13 | 0 | N | N |
| DBS-044 | 劳务结算 | 劳务结算 | - | no_contract | 18 | 0 | N | N |
| DBS-045 | 分包合同 | 分包合同 | - | no_contract | 18 | 0 | N | N |
| DBS-046 | 分包方单 | 分包方单 | - | no_contract | 15 | 0 | N | N |
| DBS-047 | 分包结算单 | 分包结算 | - | no_contract | 20 | 0 | N | N |
| DBS-048 | 机械合同 | 机械合同 | - | no_contract | 21 | 0 | N | N |
| DBS-049 | 机械台班记录 | 机械台班 | - | no_contract | 16 | 0 | N | N |
| DBS-050 | 机械结算单 | 机械结算 | - | no_contract | 16 | 0 | N | N |
| DBS-051 | 租赁合同 | 租赁合同 | - | no_contract | 18 | 0 | N | N |
| DBS-052 | 租赁结算单 | 租赁结算 | - | no_contract | 9 | 0 | N | N |
| DBS-053 | 租入 | 租赁入库/租入 | - | no_contract | 15 | 0 | N | N |
| DBS-054 | 施工日志（新） | 施工 | - | no_contract | 11 | 0 | N | N |

## Gap Details

### DBS-019 投标报名管理
- selected_model: `sc.legacy.tender.registration.fact`
- missing_list_fields: 单据状态, 推送结果, 单据编号, 项目名称, 登记时间, 录入人
- missing_filters: 投标项目名称

### DBS-020 投标报名费申请
- selected_model: `payment.request`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 申请人, 收款账号, 开户行, 金额, 备注, 收款人, 付款方式, 附件, 录入人, 录入时间

### DBS-021 承包人借项目款
- selected_model: `sc.legacy.financing.loan.fact`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 借款人, 借款金额, 用途, 约定期限, 借款利息, 备注, 附件, 录入人, 录入时间

### DBS-022 承包人还项目款
- selected_model: `-`
- missing_list_fields: 单据编号, 项目名称, 借款人, 借款金额, 还款金额, 用途, 借款利率, 利息, 还款时间, 备注, 附件, 录入人, 录入时间
- attempts: sc.financing.loan(500 内部错误), sc.fund.account.operation(500 内部错误)

### DBS-023 支付申请
- selected_model: `payment.request`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 收款单位, 申请付款金额, 实际付款金额, 可用余额, 成本分类名称, 备注, 是否关联单据, 付款账号, 金额大写, 户名, 开户行, 账号, 填写人, 附件, 录入时间

### DBS-024 扣款单
- selected_model: `sc.legacy.deduction.adjustment.line`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 扣款单位, 扣款金额, 扣款事由, 单据日期, 附件, 录入人, 录入时间

### DBS-025 往来单位付款
- selected_model: `-`
- missing_list_fields: 推送结果, 金蝶单据编号, 单据编号, 项目名称, 供应商名称, 付款日期, 付款金额, 备注, 其它备注, 付款方式名称, 填写人, 开户行, 账户, 付款账户, 付款账户名称, 支付申请单号, 附件
- attempts: sc.payment.execution(500 内部错误)

### DBS-026 账户间资金往来
- selected_model: `sc.legacy.account.transaction.line`
- missing_list_fields: 项目名称, 发生时间, 账户号码, 收款账户, 转账类别, 事由, 备注, 附件, 录入人, 录入时间

### DBS-027 扣款实缴登记
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 单据日期, 标题, 本次实缴数, 是否退回, 上缴内容, 本次计划已缴数, 录入人, 录入时间
- attempts: sc.tax.deduction.registration(500 内部错误), sc.fund.account.operation(500 内部错误)

### DBS-028 扣款实缴退回
- selected_model: `-`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 本次实缴数, 本次退回数, 上缴内容, 备注, 附件, 录入人, 单据日期
- attempts: sc.tax.deduction.registration(500 内部错误), sc.fund.account.operation(500 内部错误)

### DBS-029 到款确认表
- selected_model: `sc.legacy.fund.confirmation.line`
- missing_list_fields: 单据状态, 单据编号, 时间, 项目名称, 期数, 本期收款, 本期代扣代缴合计, 本期拨付金额合计, 附件, 施工单位, 合同金额, 目前形象进度, 累计开票金额, 上期留存余额, 录入人, 录入时间

### DBS-030 资金日报表
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 单据日期, 账号名称, 银行账号, 当前账户余额, 当前账户银行余额, 银行系统差额, 当日累计收入, 当日累计支出, 账户往来, 备注, 录入人, 录入时间
- attempts: sc.legacy.fund.daily.snapshot.fact(500 内部错误)

### DBS-031 项目借公司款登记
- selected_model: `sc.legacy.project.fund.balance.fact`
- missing_list_fields: 单据状态, 单据编号, 贷款金额, 到期利息, 还款金额, 未还款金额, 贷款日期, 还款日期, 贷款天数, 年利率, 贷款账户, 贷款银行, 备注, 附件, 录入人, 录入时间

### DBS-032 项目还公司款登记
- selected_model: `-`
- missing_list_fields: 单据编号, 项目名称, 还款金额, 实际还款天数, 实际年利率, 贷款利息, 贷款银行, 贷款账户, 还款账户, 填写人, 备注, 附件, 录入人, 录入时间
- attempts: sc.financing.loan(500 内部错误), sc.fund.account.operation(500 内部错误)

### DBS-033 开票申请
- selected_model: `-`
- missing_list_fields: 状态, 开票状态, 合同编号, 项目名称, 单据编号, 申请人, 预计回款日期, 申请日期, 受票方名称, 累计开票金额, 合同额, 本次开票张数, 本次开票金额, 附件, 备注, 录入人, 录入时间
- attempts: sc.invoice.registration(500 内部错误)

### DBS-034 开票登记
- selected_model: `sc.legacy.income.invoice.fact`
- missing_list_fields: 单据状态, 推送结果, 金蝶单据编号, 单据编号, 受票方名称, 含税金额, 附加税, 开票张数, 税率, 关联回款金额, 发票号, 发票种类, 开票单位, 附件, 录入人, 开票日期

### DBS-035 预缴税款
- selected_model: `-`
- missing_list_fields: 状态, 项目名称, 单据编号, 受票方名称, 交税类型, 金额, 发票开具日期, 预缴税款日期, 完税凭证号码, 附件, 录入人
- attempts: sc.tax.deduction.registration(500 内部错误)

### DBS-036 抵扣登记
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 是否转出, 项目名称, 开票单位, 发票号, 抵扣税额, 抵扣总额, 抵扣附加税, 备注, 录入人, 单据日期
- attempts: sc.tax.deduction.registration(500 内部错误)

### DBS-037 账户
- selected_model: `-`
- missing_list_fields: 推送结果, 账户状态, 账户操作, 录入来源, 项目名称, 单据编号, 账户类型, 账号名称, 账号户名, 开户行, 初期余额, 录入人, 录入时间
- attempts: sc.fund.account(500 内部错误)

### DBS-038 进项上报
- selected_model: `-`
- missing_list_fields: 状态, 单据编号, 项目名称, 发票开具日期, 受票单位, 开票单位, 实际开票单位, 价税合计, 税额, 不含税金额, 发票号码, 数量, 税率, 发票类型, 备注, 录入人, 附件, 录入时间
- attempts: sc.tax.deduction.registration(500 内部错误)

### DBS-039 供货合同
- selected_model: `purchase.order`
- missing_list_fields: 单据状态, 合同编号, 标题, 购货单位, 总金额, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 项目名称, 录入时间, 税率, 录入人, 附件

### DBS-040 入库
- selected_model: `-`
- missing_list_fields: 单据状态, 入库单号, 单据日期, 供应商名称, 材料名称, 规格型号, 数量, 单价, 税率, 含税金额, 入库总数量, 付款状态, 已付款金额, 未付款金额, 结算状态, 已结算金额, 项目名称, 备注, 附件, 录入人, 录入时间, 采购人
- attempts: sc.material.inbound(500 内部错误)

### DBS-041 材料结算单
- selected_model: `-`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 标题, 结算单位, 结算日期, 结算金额, 付款状态, 已付款金额, 未付款金额, 支付申请状态, 已申请金额, 未申请金额, 结算说明, 附件, 录入人, 录入时间
- attempts: sc.material.settlement(500 内部错误)

### DBS-042 劳务合同
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 签订日期, 标题, 劳务单位, 施工队负责人, 总含税金额, 结算比例, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 计价方式, 施工部位, 合同编号, 附件, 录入人, 支付条款, 推送项目名称
- attempts: sc.labor.request(500 内部错误), sc.labor.settlement(500 内部错误)

### DBS-043 劳务方单
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 单据日期, 标题, 劳务单位, 施工部位, 结算状态, 总金额, 备注, 附件, 录入人, 录入时间
- attempts: sc.labor.usage(500 内部错误), sc.labor.settlement(500 内部错误)

### DBS-044 劳务结算
- selected_model: `-`
- missing_list_fields: 状态, 单据编号, 项目名称, 单据日期, 标题, 结算单位, 结算金额, 付款状态, 已付款金额, 未付款金额, 支付申请状态, 已申请金额, 未申请金额, 结算说明, 附件, 录入人, 录入时间, 合同编号
- attempts: sc.labor.settlement(500 内部错误)

### DBS-045 分包合同
- selected_model: `-`
- missing_list_fields: 状态, 单据编号, 签订时间, 标题, 分包单位, 分包内容, 总数量, 金额, 合同编号, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 项目名称, 备注, 附件, 录入人, 录入时间
- attempts: sc.subcontract.register(500 内部错误)

### DBS-046 分包方单
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 标题, 分包商, 分包类型, 分包内容, 数量, 单价, 金额, 本月合价, 备注, 附件, 录入人, 录入时间
- attempts: sc.subcontract.request(500 内部错误), sc.subcontract.register(500 内部错误)

### DBS-047 分包结算单
- selected_model: `-`
- missing_list_fields: 状态, 项目名称, 单据编号, 标题, 结算单位, 结算金额, 付款状态, 已付款金额, 未付款金额, 支付申请状态, 已申请金额, 未申请金额, 合同编号, 起始结算日期, 终止结算日期, 结算日期, 结算说明, 附件, 录入人, 录入时间
- attempts: sc.subcontract.settlement(500 内部错误)

### DBS-048 机械合同
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 合同编号, 项目名称, 合同标题, 租赁单位, 租赁内容, 总数量, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 总金额, 签订时间, 经办人及电话, 税率, 增值税类型, 备注, 附件, 录入人, 录入时间
- attempts: sc.equipment.request(500 内部错误), sc.equipment.settlement(500 内部错误)

### DBS-049 机械台班记录
- selected_model: `-`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 单据日期, 租赁单位, 曾用名单, 机械名称, 规格型号, 单位, 工作时间, 单价, 金额, 附件, 备注, 录入人, 录入时间
- attempts: sc.equipment.usage(500 内部错误)

### DBS-050 机械结算单
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 单据日期, 结算单位, 结算内容, 总金额, 付款状态, 已付款金额, 未付款金额, 支付申请状态, 已申请金额, 未申请金额, 附件, 录入人, 录入时间
- attempts: sc.equipment.settlement(500 内部错误)

### DBS-051 租赁合同
- selected_model: `-`
- missing_list_fields: 单据编号, 状态, 合同编号, 项目名称, 合同标题, 租赁单位, 单据金额, 租赁内容, 总金额, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 开户行, 银行账号, 开户人姓名, 附件, 签订时间
- attempts: sc.material.rental.order(500 内部错误)

### DBS-052 租赁结算单
- selected_model: `-`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 结算单位, 结算日期, 结算金额, 附件, 录入人, 录入时间
- attempts: sc.material.rental.settlement(500 内部错误)

### DBS-053 租入
- selected_model: `-`
- missing_list_fields: 单据状态, 单据编号, 单据日期, 租赁单位, 使用单位名称, 材料名称, 规格型号, 数量, 单价, 租赁押金, 备注, 附件, 录入人, 录入时间, 项目名称
- attempts: sc.material.rental.order(500 内部错误)

### DBS-054 施工日志（新）
- selected_model: `-`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 日期, 施工部位, 出勤人数, 出勤机械, 备注, 附件, 录入人, 录入时间
- attempts: sc.construction.diary(500 内部错误)
