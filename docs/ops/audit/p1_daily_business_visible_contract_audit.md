# P1 Daily Business Visible Contract Audit

- audit_login: wutao
- entry_count: 36
- contract_entry_count: 36
- no_contract_count: 0
- aligned_count: 0
- gap_count: 36
- missing_list_field_count: 452

| id | old entry | domain | selected model | status | missing list fields | missing filters | attachment | chatter |
|---|---|---|---|---|---:|---:|---|---|
| DBS-019 | 投标报名管理 | 投标 | tender.bid | gap | 5 | 1 | Y | Y |
| DBS-020 | 投标报名费申请 | 投标/付款 | tender.bid | gap | 12 | 0 | Y | Y |
| DBS-021 | 承包人借项目款 | 借款 | sc.financing.loan | gap | 12 | 0 | Y | Y |
| DBS-022 | 承包人还项目款 | 还款 | sc.financing.loan | gap | 13 | 0 | Y | Y |
| DBS-023 | 支付申请 | 付款 | payment.request | gap | 18 | 0 | Y | Y |
| DBS-024 | 扣款单 | 扣款 | sc.tax.deduction.registration | gap | 6 | 0 | Y | Y |
| DBS-025 | 往来单位付款 | 付款 | sc.payment.execution | gap | 15 | 0 | Y | Y |
| DBS-026 | 账户间资金往来 | 资金账户 | sc.fund.account.operation | gap | 10 | 0 | Y | Y |
| DBS-027 | 扣款实缴登记 | 扣款 | sc.tax.deduction.registration | gap | 7 | 0 | Y | Y |
| DBS-028 | 扣款实缴退回 | 扣款 | sc.tax.deduction.registration | gap | 7 | 0 | Y | Y |
| DBS-029 | 到款确认表 | 收款 | sc.receipt.income | gap | 16 | 0 | Y | Y |
| DBS-030 | 资金日报表 | 资金报表 | sc.legacy.fund.daily.snapshot.fact | gap | 14 | 0 | Y | Y |
| DBS-031 | 项目借公司款登记 | 借款 | sc.financing.loan | gap | 17 | 0 | Y | Y |
| DBS-032 | 项目还公司款登记 | 还款 | sc.financing.loan | gap | 14 | 0 | Y | Y |
| DBS-033 | 开票申请 | 发票税务 | sc.invoice.registration | gap | 16 | 0 | Y | Y |
| DBS-034 | 开票登记 | 发票税务 | sc.invoice.registration | gap | 16 | 0 | Y | Y |
| DBS-035 | 预缴税款 | 发票税务 | sc.tax.deduction.registration | gap | 8 | 0 | Y | Y |
| DBS-036 | 抵扣登记 | 发票税务 | sc.tax.deduction.registration | gap | 7 | 0 | Y | Y |
| DBS-037 | 账户 | 资金账户基础 | sc.fund.account | gap | 9 | 0 | Y | Y |
| DBS-038 | 进项上报 | 进项税务 | sc.tax.deduction.registration | gap | 13 | 0 | Y | Y |
| DBS-039 | 供货合同 | 材料合同 | sc.material.purchase.request | gap | 13 | 0 | Y | Y |
| DBS-040 | 入库 | 材料入库 | sc.material.inbound | gap | 15 | 0 | Y | Y |
| DBS-041 | 材料结算单 | 材料结算 | sc.material.settlement | gap | 13 | 0 | Y | Y |
| DBS-042 | 劳务合同 | 劳务合同 | sc.labor.request | gap | 19 | 0 | Y | Y |
| DBS-043 | 劳务方单 | 劳务方单 | sc.labor.usage | gap | 10 | 0 | Y | Y |
| DBS-044 | 劳务结算 | 劳务结算 | sc.labor.settlement | gap | 14 | 0 | Y | Y |
| DBS-045 | 分包合同 | 分包合同 | sc.subcontract.register | gap | 14 | 0 | Y | Y |
| DBS-046 | 分包方单 | 分包方单 | sc.subcontract.request | gap | 13 | 0 | Y | Y |
| DBS-047 | 分包结算单 | 分包结算 | sc.subcontract.settlement | gap | 15 | 0 | Y | Y |
| DBS-048 | 机械合同 | 机械合同 | sc.equipment.request | gap | 19 | 0 | Y | Y |
| DBS-049 | 机械台班记录 | 机械台班 | sc.equipment.usage | gap | 14 | 0 | Y | Y |
| DBS-050 | 机械结算单 | 机械结算 | sc.equipment.settlement | gap | 14 | 0 | Y | Y |
| DBS-051 | 租赁合同 | 租赁合同 | sc.material.rental.order | gap | 17 | 0 | Y | Y |
| DBS-052 | 租赁结算单 | 租赁结算 | sc.material.rental.settlement | gap | 5 | 0 | Y | Y |
| DBS-053 | 租入 | 租赁入库/租入 | sc.material.rental.order | gap | 13 | 0 | Y | Y |
| DBS-054 | 施工日志（新） | 施工 | sc.construction.diary | gap | 9 | 0 | Y | Y |

## Gap Details

### DBS-019 投标报名管理
- selected_model: `tender.bid`
- missing_list_fields: 单据状态, 推送结果, 单据编号, 项目名称, 登记时间
- missing_filters: 投标项目名称

### DBS-020 投标报名费申请
- selected_model: `tender.bid`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 申请人, 申请日期, 收款账号, 开户行, 金额, 备注, 收款人, 付款方式, 附件

### DBS-021 承包人借项目款
- selected_model: `sc.financing.loan`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 借款人, 借款金额, 用途, 约定期限, 借款利息, 备注, 附件, 录入人, 录入时间

### DBS-022 承包人还项目款
- selected_model: `sc.financing.loan`
- missing_list_fields: 单据编号, 项目名称, 借款人, 借款金额, 还款金额, 用途, 借款利率, 利息, 还款时间, 备注, 附件, 录入人, 录入时间

### DBS-023 支付申请
- selected_model: `payment.request`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 收款单位, 申请付款金额, 实际付款金额, 可用余额, 成本分类名称, 备注, 是否关联单据, 付款账号, 金额大写, 户名, 开户行, 账号, 填写人, 附件, 录入时间

### DBS-024 扣款单
- selected_model: `sc.tax.deduction.registration`
- missing_list_fields: 单据状态, 项目名称, 扣款单位, 扣款金额, 扣款事由, 附件

### DBS-025 往来单位付款
- selected_model: `sc.payment.execution`
- missing_list_fields: 推送结果, 金蝶单据编号, 单据编号, 项目名称, 供应商名称, 付款日期, 付款金额, 备注, 其它备注, 付款方式名称, 填写人, 开户行, 账户, 支付申请单号, 附件

### DBS-026 账户间资金往来
- selected_model: `sc.fund.account.operation`
- missing_list_fields: 单据状态, 项目名称, 发生时间, 账户号码, 转账类别, 事由, 备注, 附件, 录入人, 录入时间

### DBS-027 扣款实缴登记
- selected_model: `sc.tax.deduction.registration`
- missing_list_fields: 单据状态, 项目名称, 标题, 本次实缴数, 是否退回, 上缴内容, 本次计划已缴数

### DBS-028 扣款实缴退回
- selected_model: `sc.tax.deduction.registration`
- missing_list_fields: 单据状态, 项目名称, 本次实缴数, 本次退回数, 上缴内容, 备注, 附件

### DBS-029 到款确认表
- selected_model: `sc.receipt.income`
- missing_list_fields: 单据状态, 单据编号, 时间, 项目名称, 期数, 本期收款, 本期代扣代缴合计, 本期拨付金额合计, 附件, 施工单位, 合同金额, 目前形象进度, 累计开票金额, 上期留存余额, 录入人, 录入时间

### DBS-030 资金日报表
- selected_model: `sc.legacy.fund.daily.snapshot.fact`
- missing_list_fields: 单据状态, 单据编号, 单据日期, 账号名称, 银行账号, 当前账户余额, 当前账户银行余额, 银行系统差额, 当日累计收入, 当日累计支出, 账户往来, 备注, 录入人, 录入时间

### DBS-031 项目借公司款登记
- selected_model: `sc.financing.loan`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 贷款金额, 到期利息, 还款金额, 未还款金额, 贷款日期, 还款日期, 贷款天数, 年利率, 贷款账户, 贷款银行, 备注, 附件, 录入人, 录入时间

### DBS-032 项目还公司款登记
- selected_model: `sc.financing.loan`
- missing_list_fields: 单据编号, 项目名称, 还款金额, 实际还款天数, 实际年利率, 贷款利息, 贷款银行, 贷款账户, 还款账户, 填写人, 备注, 附件, 录入人, 录入时间

### DBS-033 开票申请
- selected_model: `sc.invoice.registration`
- missing_list_fields: 开票状态, 合同编号, 项目名称, 单据编号, 申请人, 预计回款日期, 申请日期, 受票方名称, 累计开票金额, 合同额, 本次开票张数, 本次开票金额, 附件, 备注, 录入人, 录入时间

### DBS-034 开票登记
- selected_model: `sc.invoice.registration`
- missing_list_fields: 单据状态, 推送结果, 金蝶单据编号, 单据编号, 项目名称, 受票方名称, 含税金额, 附加税, 开票张数, 关联回款金额, 发票号, 发票种类, 开票单位, 附件, 录入人, 开票日期

### DBS-035 预缴税款
- selected_model: `sc.tax.deduction.registration`
- missing_list_fields: 项目名称, 受票方名称, 交税类型, 金额, 发票开具日期, 预缴税款日期, 完税凭证号码, 附件

### DBS-036 抵扣登记
- selected_model: `sc.tax.deduction.registration`
- missing_list_fields: 单据状态, 是否转出, 项目名称, 开票单位, 发票号, 抵扣总额, 备注

### DBS-037 账户
- selected_model: `sc.fund.account`
- missing_list_fields: 推送结果, 账户状态, 账户操作, 录入来源, 项目名称, 单据编号, 账号名称, 账号户名, 初期余额

### DBS-038 进项上报
- selected_model: `sc.tax.deduction.registration`
- missing_list_fields: 项目名称, 发票开具日期, 受票单位, 开票单位, 实际开票单位, 价税合计, 税额, 不含税金额, 数量, 税率, 发票类型, 备注, 附件

### DBS-039 供货合同
- selected_model: `sc.material.purchase.request`
- missing_list_fields: 单据状态, 合同编号, 标题, 供应商, 购货单位, 总金额, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 项目名称, 税率, 附件

### DBS-040 入库
- selected_model: `sc.material.inbound`
- missing_list_fields: 单据状态, 单据日期, 供应商名称, 数量, 税率, 含税金额, 入库总数量, 付款状态, 已付款金额, 未付款金额, 结算状态, 已结算金额, 项目名称, 附件, 采购人

### DBS-041 材料结算单
- selected_model: `sc.material.settlement`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 标题, 结算单位, 付款状态, 已付款金额, 未付款金额, 支付申请状态, 已申请金额, 未申请金额, 结算说明, 附件

### DBS-042 劳务合同
- selected_model: `sc.labor.request`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 签订日期, 标题, 劳务单位, 施工队负责人, 总含税金额, 结算比例, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 计价方式, 施工部位, 合同编号, 附件, 支付条款, 推送项目名称

### DBS-043 劳务方单
- selected_model: `sc.labor.usage`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 单据日期, 标题, 施工部位, 结算状态, 总金额, 备注, 附件

### DBS-044 劳务结算
- selected_model: `sc.labor.settlement`
- missing_list_fields: 单据编号, 项目名称, 单据日期, 标题, 结算单位, 付款状态, 已付款金额, 未付款金额, 支付申请状态, 已申请金额, 未申请金额, 结算说明, 附件, 合同编号

### DBS-045 分包合同
- selected_model: `sc.subcontract.register`
- missing_list_fields: 单据编号, 签订时间, 标题, 分包内容, 总数量, 金额, 合同编号, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 项目名称, 备注, 附件

### DBS-046 分包方单
- selected_model: `sc.subcontract.request`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 标题, 分包商, 分包类型, 分包内容, 数量, 单价, 金额, 本月合价, 备注, 附件

### DBS-047 分包结算单
- selected_model: `sc.subcontract.settlement`
- missing_list_fields: 项目名称, 单据编号, 标题, 结算单位, 付款状态, 已付款金额, 未付款金额, 支付申请状态, 已申请金额, 未申请金额, 合同编号, 起始结算日期, 终止结算日期, 结算说明, 附件

### DBS-048 机械合同
- selected_model: `sc.equipment.request`
- missing_list_fields: 单据状态, 单据编号, 合同编号, 项目名称, 合同标题, 租赁单位, 租赁内容, 总数量, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 总金额, 签订时间, 经办人及电话, 税率, 增值税类型, 备注, 附件

### DBS-049 机械台班记录
- selected_model: `sc.equipment.usage`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 单据日期, 租赁单位, 曾用名单, 机械名称, 规格型号, 单位, 工作时间, 单价, 金额, 附件, 备注

### DBS-050 机械结算单
- selected_model: `sc.equipment.settlement`
- missing_list_fields: 单据状态, 单据编号, 项目名称, 单据日期, 结算单位, 结算内容, 总金额, 付款状态, 已付款金额, 未付款金额, 支付申请状态, 已申请金额, 未申请金额, 附件

### DBS-051 租赁合同
- selected_model: `sc.material.rental.order`
- missing_list_fields: 单据编号, 合同编号, 项目名称, 合同标题, 租赁单位, 单据金额, 租赁内容, 总金额, 已开票金额, 已付款金额, 未付款金额, 未开票金额, 开户行, 银行账号, 开户人姓名, 附件, 签订时间

### DBS-052 租赁结算单
- selected_model: `sc.material.rental.settlement`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 结算单位, 附件

### DBS-053 租入
- selected_model: `sc.material.rental.order`
- missing_list_fields: 单据状态, 单据编号, 单据日期, 租赁单位, 使用单位名称, 材料名称, 规格型号, 数量, 单价, 租赁押金, 备注, 附件, 项目名称

### DBS-054 施工日志（新）
- selected_model: `sc.construction.diary`
- missing_list_fields: 单据状态, 项目名称, 单据编号, 日期, 施工部位, 出勤人数, 出勤机械, 备注, 附件
