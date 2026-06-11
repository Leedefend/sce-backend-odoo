# Finance Handling Chain Matrix - 2026-06-11

## Scope

本矩阵是 `business_handling_delivery_master_plan_2026-06-11.md` 的 Phase 1 执行拆解。目标不是继续扩展报表，而是把资金财务相关的登记、申请、审批、确认、执行、台账沉淀和历史追溯整理成可交付办理链路。

## Current Evidence

```text
DB_NAME=sc_demo scripts/ops/validate_business_flow_closure.sh
BUSINESS_FLOW_CLOSURE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_action_coverage.sh
BUSINESS_ACTION_COVERAGE_AUDIT: status=PASS
covered: payment_execution, receipt_income, expense_claim, invoice_registration, tax_deduction, hr_payroll, fund_account_operation
```

```text
DB_NAME=sc_demo python3 scripts/verify/p1_daily_business_form_usability_audit.py
[p1_daily_business_form_usability_audit] PASS
entry_count=36, usable_contract_ready_count=36, needs_usability_attention_count=0
```

```text
DB_NAME=sc_demo bash scripts/ops/validate_finance_handling_evidence.sh
FINANCE_HANDLING_EVIDENCE_AUDIT: status=PASS
covered: direct_payment_request, direct_receive_request, payment_execution, receipt_income, expense_claim
evidence: attachment, state closure, downstream ledger, audit event
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_relation_required.sh
FINANCE_RELATION_REQUIRED_AUDIT: status=PASS
covered: payment_execution, receipt_income, expense_claim
evidence: missing request/account relation is blocked before handling action
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_role_permissions.sh
FINANCE_ROLE_PERMISSION_AUDIT: status=PASS
covered: read, initiator, finance user, finance manager
evidence: read visibility, create block, submit/confirm, approval block/allow, finance confirmation block/allow
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_downstream_traceability.sh
FINANCE_DOWNSTREAM_TRACEABILITY_AUDIT: status=PASS
covered: direct_payment, direct_receive, payment_execution, receipt_income, expense_claim
evidence: ledger -> request/settlement/source document/attachment/audit trail
```

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_handling.http_surface.smoke
FINANCE_HANDLING_HTTP_SURFACE_SMOKE: status=PASS db=sc_demo entries=4
covered: 支付申请、往来单位付款、到款确认/项目收款、项目费用报销单
evidence: login, system.init navigation, ui.contract.v2 action_open, api.data list, handled sample; no browser runtime download
```

HTTP/API 可见面验收结论：

- 支付申请：用户可见入口 `smart_construction_core.menu_sc_user_payment_apply_acceptance` 打开 `payment.request`，本地用户数据 29,549 条，已办样本可追到 `payment.ledger`。
- 往来单位付款：用户可见入口 `smart_construction_core.menu_sc_partner_payment` 打开 `sc.payment.execution`，本地用户数据 24,049 条，入口和已办样本可读；旧样本未稳定追到 `payment.ledger`，后续作为旧数据台账补齐任务处理。
- 到款确认/项目收款：用户可见入口 `smart_construction_core.menu_sc_engineering_progress_income` 打开 `sc.receipt.income`，本地用户数据 15,905 条，入口和已办样本可读；旧样本未稳定追到 `sc.treasury.ledger`，后续进入项目收款状态约束和现金流台账补齐任务。
- 项目费用报销单：用户可见入口 `smart_construction_core.menu_sc_project_expense_claim` 打开 `sc.expense.claim`，本地用户数据 37,013 条，入口和已办样本可读；旧样本台账追踪缺口后续按资金台账口径单独闭环。

```text
scripts/ops/validate_finance_business_categories.sh
FINANCE_BUSINESS_CATEGORY_ACTION_AUDIT: status=PASS
covered: 21 finance category candidates
evidence: category -> action -> menu binding, context defaults, domain coverage for new records
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh
FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
covered: 21 finance category candidates
evidence: create temp record from runtime action context, then verify current runtime action domain can find it
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
covered: 34 business category template records
evidence: user-visible category, stable code, template version, bound action, target model, direction, required fields, downstream policy
```

```text
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_handling_evidence.sh
INVOICE_TAX_HANDLING_EVIDENCE_AUDIT: status=PASS
covered: invoice_registration, tax_deduction_registration
evidence: attachment, state closure, business anchor blocking, audit event
```

```text
DB_NAME=sc_demo scripts/ops/validate_invoice_tax_downstream_traceability.sh
INVOICE_TAX_DOWNSTREAM_TRACEABILITY_AUDIT: status=PASS
covered: output invoice registration, input invoice report, tax deduction
evidence: invoice category summary, noncash tax fact, project finance summary, project capital position
```

```text
DB_NAME=sc_demo scripts/ops/validate_material_business_category_runtime.sh
MATERIAL_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
covered: 7 material category candidates
evidence: create temp record from runtime action context, then verify current runtime action domain can find it
```

## User Entry Matrix

入口设计原则：

- 菜单可以按用户常用工作台整合，但每个入口必须带明确业务类别，不能只暴露泛化模型。
- 当前 `action domain/context` 是过渡实现，所有高频类别都应作为“业务分类字典候选项”记录。
- 同一正式模型内的不同事项，优先通过分类默认值、字段显隐、表单分组、按钮可见性和必填规则来降低办理噪音。
- 用户历史名称先保留为可见语义，再映射到标准分类编码；标准编码服务审计、权限、审批和下游台账。

| 用户入口 | 正式模型 | 当前办理动作 | 下游事实 | 当前结论 | 下一步 |
| --- | --- | --- | --- | --- | --- |
| 支付申请 | `payment.request` | `action_submit`、`action_approval_decision`、`action_set_approved`、`action_done`、`action_cancel` | `payment.ledger`、`sc.treasury.ledger`、审批记录、审计日志 | 办理证据闭环、角色权限、下游追溯通过 | 补浏览器级验收：合同/结算拦截、取消、附件 |
| 往来单位付款 | `sc.payment.execution` | `action_confirm`、`action_paid`、`action_cancel`、`action_on_tier_approved` | `payment.ledger`、关联付款申请完成 | 办理入口可见面已通过 HTTP/API；旧样本台账追踪仍需补齐 | 补旧数据台账追踪口径，再做浏览器级验收 |
| 到款确认表 | `sc.receipt.income` | `action_confirm`、`action_received`、`action_cancel`、`action_on_tier_approved` | `sc.treasury.ledger`、收款申请完成 | 办理入口可见面已通过 HTTP/API；旧样本台账追踪仍需补齐 | 补项目收款状态约束和现金流台账口径，再做浏览器级验收 |
| 报销/费用单据 | `sc.expense.claim` | `action_submit`、`action_approve`、`action_done`、`action_cancel`、审批回调 | 关联 `payment.request`、`payment.ledger`、`sc.treasury.ledger` | 办理入口可见面已通过 HTTP/API；旧样本台账追踪仍需补齐 | 补不同 `claim_type` 台账策略和浏览器级验收 |
| 扣款单/扣款实缴/退回 | `sc.tax.deduction.registration` | 确认、已抵扣、取消 | 税务事实、项目经营口径 | 办理证据闭环、角色权限、下游税务事实追溯通过 | Phase 2 继续补正式分类字段或业务分类字典绑定 |
| 账户间资金往来 | `sc.fund.account.operation` | 确认、完成、取消 | 账户资金往来事实、往来现金流台账 | 后端动作、关系必填、现金流追溯、历史回填就绪审计通过 | 补正式历史回填迁移脚本、浏览器级验收和账户余额回填策略 |
| 项目/承包人借还款 | `sc.financing.loan` | 借款登记、还款登记 | 资金往来事实、项目资金口径 | 表单契约通过 | 明确借出、借入、还款、利息和账户关系 |
| 资金日报表 | `sc.legacy.fund.daily.snapshot.fact` | 历史事实查看 | 来源事实明细 | 表单契约通过 | 暂不作为办理主线，后置到 Phase 6 |

## Finance Classification Dictionary Candidates

这些类别来自当前用户数据和已梳理菜单，是 Phase 1/Phase 2 的字典化候选项。短期可继续用 action/domain/context 实现，长期应进入可维护分类字典和行业模板。

| 分类编码候选 | 用户可见事项 | 正式模型 | 方向 | 建议必填关系 | 下游策略 |
| --- | --- | --- | --- | --- | --- |
| `finance.payment.apply.pay` | 付款申请 | `payment.request` | 付款 | 项目、合同、往来单位、金额、付款账户 | 完成后生成 `payment.ledger` |
| `finance.payment.apply.receive` | 收款申请 | `payment.request` | 收款 | 项目、合同、往来单位、金额、收款类别 | 完成后生成 `sc.treasury.ledger` |
| `finance.payment.execution.partner` | 往来单位付款 | `sc.payment.execution` | 付款执行 | 付款申请、项目、合同、往来单位、付款账户、收款账户、实付金额 | 同步付款申请，生成 `payment.ledger` |
| `finance.receipt.income.project` | 到款确认/项目收款 | `sc.receipt.income` | 收款确认 | 收款申请、项目、合同、往来单位、收款账户、收款金额 | 同步收款申请，生成 `sc.treasury.ledger` |
| `finance.expense.reimbursement` | 项目费用报销单 | `sc.expense.claim` | 付款 | 付款申请、项目、往来单位、报销金额、付款账户、收款账户 | 同步付款申请，生成 `payment.ledger` |
| `finance.deposit.bid.pay` | 投标保证金支付 | `sc.expense.claim` | 付款 | 项目/投标事项、往来单位、金额、付款账户、收款账户 | 生成付款台账或保证金事实 |
| `finance.deposit.bid.return` | 投标保证金退回 | `sc.expense.claim` | 收款/退回 | 项目/投标事项、往来单位、金额、收款账户 | 生成资金台账或保证金事实 |
| `finance.deposit.contract.pay` | 合同保证金支付 | `sc.expense.claim` | 付款 | 项目、合同、往来单位、金额、付款账户、收款账户 | 生成付款台账或保证金事实 |
| `finance.deposit.contract.return` | 合同保证金退回 | `sc.expense.claim` | 收款/退回 | 项目、合同、往来单位、金额、收款账户 | 生成资金台账或保证金事实 |
| `finance.deduction.bill` | 扣款单 | `sc.expense.claim` / `sc.tax.deduction.registration` | 非现金/扣款 | 项目、合同/发票、往来单位、扣款金额、扣款原因 | 进入税务/成本/往来抵扣事实 |
| `finance.deduction.paid` | 扣款实缴登记 | `sc.expense.claim` / `sc.tax.deduction.registration` | 付款/税务 | 项目、往来单位、金额、账户、税务依据 | 进入付款台账和税务事实 |
| `finance.deduction.refund` | 扣款实缴退回 | `sc.expense.claim` / `sc.tax.deduction.registration` | 收款/退回 | 项目、往来单位、金额、收款账户、退回原因 | 进入资金台账和税务事实 |
| `invoice.output.registration` | 销项开票登记 | `sc.invoice.registration` | 销项/税务 | 项目、合同、往来单位、发票号、金额、税额 | 进入发票分类汇总，作为收入合同和税务口径依据 |
| `invoice.input.report` | 进项税额上报 | `sc.invoice.registration` | 进项/税务 | 项目、合同、往来单位、发票号、金额、税额 | 进入发票分类汇总，作为成本和抵扣来源候选 |
| `tax.deduction.registration` | 抵扣登记 | `sc.tax.deduction.registration` | 非现金税务 | 项目、往来单位、发票号、认证日期、抵扣金额、抵扣税额 | 以 `noncash_tax` 进入项目税务事实，余额影响为 0 |
| `finance.fund.transfer` | 账户间资金往来 | `sc.fund.account.operation` | 转账 | 来源账户、目标账户、金额、经办人、账户币种一致 | 生成账户资金往来事实和往来现金流台账 |
| `finance.loan.project` | 项目/承包人借还款 | `sc.financing.loan` | 借款/还款 | 项目、借款人/还款人、账户、金额、期限 | 生成资金往来和项目资金事实 |

字典化落地要求：

- 先以当前用户历史数据命名保持可见认知，再给每个类别分配稳定编码。
- 分类字典应允许客户启停、改名、排序、配置必填字段和附件要求。
- 行业模板只预置建筑行业常见类别，不锁死客户自定义类别。
- 审批策略、台账方向、成本/税务沉淀规则应挂到分类上，而不是散落在菜单和按钮里。
- 浏览器验收按分类抽样，不只按模型抽样。
- 在正式字典模型落地前，`scripts/ops/validate_finance_business_categories.sh` 作为过渡门禁，确保当前 action/domain/context/menu 已经按分类候选收敛，且新建保存后不会从当前入口丢失。
- 第一阶段已新增 `sc.business.category`，沉淀 22 个财务/资金类分类、5 个发票/税务分类和 7 个材料采购库存分类；现有 action/domain/context 暂不替换，后续按门禁逐步绑定字典默认值、必填字段和下游策略。
- 模板同步只写 `template_key`、`template_version`、`action_xmlid` 三类系统绑定字段，避免升级覆盖客户维护的显示名称、启停、排序、附件、审批和表单策略。
- 字典审计已验证 34 个分类的绑定 action 存在，且 action 目标模型与分类 `target_model` 一致。

## Iteration Evidence - 2026-06-11 Finance Category Action Mapping

本轮把财务“分类字典化”的原则推进到可执行静态门禁：

- 新增 `scripts/verify/finance_business_category_action_audit.py`。
- 新增 `scripts/ops/validate_finance_business_categories.sh`。
- 覆盖 21 个财务分类候选，包括支付申请、往来单位付款、公司财务支出、收入、工程进度款收入、报销/项目费用、保证金、扣款、账户资金、借还款。
- 审计内容：
  - 分类编码候选必须绑定到明确 action。
  - action 必须使用正式模型。
  - action context 必须提供当前分类默认值。
  - action domain 必须覆盖新建默认值，避免用户保存后从当前入口列表消失。
  - 菜单必须绑定到对应 action。
- 新增运行时审计 `scripts/verify/finance_business_category_runtime_audit.py`：
  - 直接读取 `sc_demo` 数据库里的 action context/domain。
  - 按每个分类默认值创建临时业务记录。
  - 使用当前 action domain 搜索该记录，证明保存后仍能回到当前入口。
- 修正了以下入口的 domain：
  - `action_sc_receipt_income_engineering_progress`：新系统 `income_category=工程进度款收入` 保存后仍留在入口。
  - `action_payment_request_user_payment_apply`：付款申请新建保存后仍留在支付申请入口。
  - `action_sc_payment_execution_partner_payment`：新系统 `payment_family=往来单位付款` 保存后仍留在入口。
  - `action_sc_financing_loan_contractor_project_borrow`：`purpose=承包人借项目款` 改为明确分类匹配。
- 修正了后加载覆盖：
  - `support/user_confirmed_formal_list_views.xml` 中 `action_sc_receipt_income_engineering_progress` 曾覆盖回历史只读列表口径。
  - 当前保留用户确认列表作为 tree 首屏，同时补回 form 视图、允许新系统办理，并统一 domain 覆盖历史事实和新系统 `income_category`。

验证结果：

```text
scripts/ops/validate_finance_business_categories.sh
FINANCE_BUSINESS_CATEGORY_ACTION_AUDIT: status=PASS
category_count=21
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh
FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
category_count=21
```

```text
python3 scripts/verify/finance_expense_claim_entry_context_audit.py
FINANCE_EXPENSE_CLAIM_ENTRY_CONTEXT_AUDIT: status=PASS
```

## Formal Model Handling State

### `payment.request`

- 用户语义：付款申请、收款申请、往来单位付款申请。
- 状态：使用 `ScStateMachine.PAYMENT_REQUEST`，状态写入受 `allow_transition` 上下文保护。
- 关键动作：
  - `action_submit`：校验合同、合同状态、资金/结算 advisory，进入审批。
  - `action_approval_decision` / `action_set_approved`：处理统一审批状态并批准。
  - `action_done`：付款生成 `payment.ledger`，收款生成 `sc.treasury.ledger`。
- 已有保护：
  - 无合同不能提交。
  - 已取消合同不能提交。
  - 审批未完成不能批准/完成。
  - 审批动作要求财务审批角色。
  - 完成动作有财务权限要求。
  - 状态迁移写审计日志。

### `sc.payment.execution`

- 用户语义：往来单位付款、实际付款登记。
- 状态：`draft -> confirmed -> paid`，历史确认和取消状态单独保留。
- 关键动作：
  - `action_confirm`：确认付款执行，可触发统一审批。
  - `action_paid`：登记已付款，校验审批、业务锚点和付款申请范围。
  - `_sync_payment_request_done`：实付满足申请金额时自动完成付款申请并生成付款台账。
- 已有保护：
  - 非草稿不能重复确认。
  - 已付款/历史确认/已取消不能继续登记付款。
  - 新系统登记必须关联付款申请、合同、往来单位、付款账户和收款账户。
  - 登记付款要求财务审批/确认角色。
  - 项目、往来单位、付款申请不一致会阻断。
  - 历史迁移付款执行不能在新系统取消。

### `sc.receipt.income`

- 用户语义：到款确认、项目收款登记、收入确认。
- 状态：`draft -> confirmed -> received`，历史确认和取消状态单独保留。
- 关键动作：
  - `action_confirm`：确认收款收入，可触发统一审批。
  - `action_received`：登记已收款，校验审批、业务锚点和收款申请范围。
  - `_sync_payment_request_done`：完成关联收款申请并生成资金台账。
- 已有保护：
  - 非草稿不能重复确认。
  - 非草稿/已确认不能登记收款。
  - 新系统登记必须关联收款申请、合同、往来单位和收款账户。
  - 登记收款要求财务审批/确认角色。
  - 历史迁移收款不能在新系统取消。

### `sc.expense.claim`

- 用户语义：费用报销、保证金、借还款、扣款/退回等费用资金类单据。
- 状态：`draft -> submit -> approved -> done`，历史确认和取消状态单独保留。
- 关键动作：
  - `action_submit`：提交费用/保证金单据，可触发统一审批。
  - `action_approve` / `action_on_tier_approved`：完成审批。
  - `action_done`：完成单据并同步关联付款申请。
- 已有保护：
  - 非草稿不能提交。
  - 非已提交不能批准。
  - 非已批准不能完成。
  - 批准和完成动作要求财务审批/确认角色。
  - 新系统登记必须关联付款/收款申请、往来单位和账户信息。
  - 业务必备字段缺失时不能继续办理。

## Delivery Gaps To Close Next

当前审计未发现 P0 表单阻断，因此下一步不应做无目标的代码修补。Phase 1 下一轮按以下顺序推进：

1. 浏览器级办理验收：为支付申请、往来单位付款、到款确认、费用单据补浏览器级验收记录，覆盖新建、附件、提交、审批、完成和取消。
2. 扩展业务关系策略：账户间资金往来、项目/承包人借还款、扣款/税务登记进入 Phase 2 前继续补关系必填门禁。
3. 正式交付清单：汇总角色账号、基础数据、首批真实业务数据导入/锁定、回滚和验收脚本。
4. 浏览器级下游追溯验收：从台账、成本、结算页面回到申请、审批、附件和历史来源。
5. 报表后置：只在以上办理事实稳定后，再完善应收应付、账户收支、资金日报等汇总入口。

## Iteration Evidence - 2026-06-11 Expense Claim Entry Clarity

本轮已完成 `sc.expense.claim` 入口清晰度修正：

- `项目费用报销单` action 补 `default_summary`，新建单据摘要不再为空泛。
- `扣款实缴登记`、`扣款实缴退回` action 的 domain 同时覆盖历史来源和新系统默认 `expense_type`，避免新建保存后从当前入口列表消失。
- 新增投标/合同保证金四个语义 action：
  - `action_sc_bid_deposit_pay`
  - `action_sc_bid_deposit_return`
  - `action_sc_contract_deposit_pay`
  - `action_sc_contract_deposit_return`
- 修正后加载的 `expense_business_fact_taxonomy_views.xml` 菜单覆盖，保证以下菜单最终绑定到具体 action，而不是退回泛化保证金 action：
  - `menu_sc_bid_deposit_pay`
  - `menu_sc_bid_deposit_return`
  - `menu_sc_contract_deposit_register`
  - `menu_sc_contract_deposit_return`
- 新增静态门禁：`scripts/verify/finance_expense_claim_entry_context_audit.py`，按 manifest 顺序检查 action context、domain 和最终菜单绑定。

验证结果：

```text
python3 scripts/verify/finance_expense_claim_entry_context_audit.py
FINANCE_EXPENSE_CLAIM_ENTRY_CONTEXT_AUDIT: status=PASS
```

```text
CODEX_MODE=fast CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_demo make mod.upgrade
PASS
```

```text
EXPENSE_ENTRY_RUNTIME_AUDIT: status=PASS
menus checked: menu_sc_bid_deposit_pay, menu_sc_bid_deposit_return, menu_sc_contract_deposit_register, menu_sc_contract_deposit_return
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_action_coverage.sh
BUSINESS_ACTION_COVERAGE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo python3 scripts/verify/p1_daily_business_form_usability_audit.py
[p1_daily_business_form_usability_audit] PASS
```

```text
make verify.baseline DB_NAME=sc_demo
[verify.baseline] PASS ALL on sc_demo
```

## Iteration Evidence - 2026-06-11 Finance Downstream Traceability Audit

本轮已把 Phase 1 财务办理链路从“生成下游事实”推进到“下游事实可反查”：

- `payment.ledger` 补导航动作：
  - `action_open_payment_request`
  - `action_open_settlement`
- `sc.treasury.ledger` 既有 `action_open_payment_request`、`action_open_settlement` 继续作为资金流水反查入口。
- 新增 `scripts/verify/finance_downstream_traceability_audit.py`，从付款台账/资金台账反查：
  - 付款/收款申请
  - 结算单
  - 来源业务单据：付款执行、到款确认、费用/保证金单据
  - 申请附件和来源单据附件
  - 审计事件：提交、审批、完成/付款/收款
- 新增 `scripts/ops/validate_finance_downstream_traceability.sh`，作为 Phase 1 下游追溯门禁。

验证结果：

```text
CODEX_MODE=fast CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_demo make mod.upgrade
PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_downstream_traceability.sh
FINANCE_DOWNSTREAM_TRACEABILITY_AUDIT: status=PASS
covered: direct_payment, direct_receive, payment_execution, receipt_income, expense_claim
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_role_permissions.sh
FINANCE_ROLE_PERMISSION_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_relation_required.sh
FINANCE_RELATION_REQUIRED_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_handling_evidence.sh
FINANCE_HANDLING_EVIDENCE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_action_coverage.sh
BUSINESS_ACTION_COVERAGE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo python3 scripts/verify/p1_daily_business_form_usability_audit.py
[p1_daily_business_form_usability_audit] PASS
```

```text
make verify.baseline DB_NAME=sc_demo
[verify.baseline] PASS ALL on sc_demo
```

## Iteration Evidence - 2026-06-11 Finance Role Permission Audit

本轮已把 Phase 1 财务办理链路的角色边界从 ACL/规则配置推进到可执行用户证据：

- 只读查询：财务只读用户在已分配项目范围内可读付款/收款申请，但不能创建新申请。
- 业务经办：业务经办可提交付款/收款申请、提交费用单据。
- 财务经办：财务经办可确认付款执行、确认收款收入，但不能审批付款申请、不能登记付款/收款、不能完成费用单据。
- 财务审批/确认：财务审批用户可审批付款申请和费用单据，并可完成付款申请、登记付款、登记收款、完成费用单据。

实现补齐：

- `payment.request` 的 `action_approve`、`action_approval_decision`、`action_set_approved` 增加财务审批角色校验。
- `sc.payment.execution.action_paid` 增加财务确认角色校验。
- `sc.receipt.income.action_received` 增加财务确认角色校验。
- `sc.expense.claim.action_approve`、`action_done` 增加财务审批/确认角色校验。
- 新增 `scripts/verify/finance_role_permission_audit.py`，用真实用户上下文验证只读、经办、审批、财务确认边界。
- 新增 `scripts/ops/validate_finance_role_permissions.sh`，作为 Phase 1 角色权限门禁。

验证结果：

```text
CODEX_MODE=fast CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_demo make mod.upgrade
PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_role_permissions.sh
FINANCE_ROLE_PERMISSION_AUDIT: status=PASS
covered: payment_request, payment_execution, receipt_income, expense_claim
users: initiator, finance_read, finance_user, finance_manager
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_relation_required.sh
FINANCE_RELATION_REQUIRED_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_handling_evidence.sh
FINANCE_HANDLING_EVIDENCE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_action_coverage.sh
BUSINESS_ACTION_COVERAGE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo python3 scripts/verify/p1_daily_business_form_usability_audit.py
[p1_daily_business_form_usability_audit] PASS
```

```text
make verify.baseline DB_NAME=sc_demo
[verify.baseline] PASS ALL on sc_demo
```

## Iteration Evidence - 2026-06-11 Finance Relation Required Audit

本轮已把“新发生单据关系完整”从计划项推进为可验证门禁：

- `sc.payment.execution`：新系统付款执行在确认/登记付款前必须具备付款申请、合同、往来单位、付款账户和收款账户。
- `sc.receipt.income`：新系统收款收入在确认/登记收款前必须具备收款申请、合同、往来单位和收款账户。
- `sc.expense.claim`：新系统费用/保证金单据在提交/完成前必须具备付款/收款申请、往来单位和按资金方向匹配的账户信息。
- 历史迁移记录继续走既有只读/补锚点策略，不把历史残缺事实改造成新发生业务。
- 正向办理证据脚本已同步补齐账户字段，保证完整业务链路仍能跑通。

新增门禁：

- `scripts/verify/finance_relation_required_audit.py`
- `scripts/ops/validate_finance_relation_required.sh`

验证结果：

```text
CODEX_MODE=fast CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_demo make mod.upgrade
PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_relation_required.sh
FINANCE_RELATION_REQUIRED_AUDIT: status=PASS
covered: payment_execution, receipt_income, expense_claim
negative cases: missing_request, missing_payer_account, missing_payee_account, missing_receiving_account
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_handling_evidence.sh
FINANCE_HANDLING_EVIDENCE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_action_coverage.sh
BUSINESS_ACTION_COVERAGE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo python3 scripts/verify/p1_daily_business_form_usability_audit.py
[p1_daily_business_form_usability_audit] PASS
```

```text
make verify.baseline DB_NAME=sc_demo
[verify.baseline] PASS ALL on sc_demo
```

## Iteration Evidence - 2026-06-11 Finance Handling Evidence Audit

本轮已把 Phase 1 财务办理链路从“动作覆盖”推进到“证据闭环”：

- `payment.request` 直接付款链路：附件、新建、提交、审批、完成、`payment.ledger`、审计事件均已验证。
- `payment.request` 直接收款链路：附件、新建、提交、审批、完成、`sc.treasury.ledger`、审计事件均已验证。
- `sc.payment.execution` 往来单位付款：附件、确认、付款、关联付款申请完成、付款台账和审计事件均已验证。
- `sc.receipt.income` 到款确认：附件、确认、收款、关联收款申请完成、资金台账和审计事件均已验证。
- `sc.expense.claim` 报销/费用单据：附件、提交、审批、完成、关联付款申请完成、付款台账和审计事件均已验证。

实现补齐：

- `sc.payment.execution` 的付款完成同步逻辑补 `payment_paid` 审计事件，`action_name=payment_execution_paid`。
- `sc.expense.claim` 的费用完成同步逻辑补 `payment_paid` 审计事件，`action_name=expense_claim_done`。
- 新增 `scripts/verify/finance_handling_evidence_audit.py`，以临时业务数据验证附件、状态闭环、下游台账和审计事件。
- 新增 `scripts/ops/validate_finance_handling_evidence.sh`，作为 Phase 1 财务办理证据门禁。

验证结果：

```text
CODEX_MODE=fast CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_demo make mod.upgrade
PASS
```

```text
DB_NAME=sc_demo bash scripts/ops/validate_finance_handling_evidence.sh
FINANCE_HANDLING_EVIDENCE_AUDIT: status=PASS
covered: direct_payment_request, direct_receive_request, payment_execution, receipt_income, expense_claim
evidence: attachment_count=1, ledger_count=1 / treasury_ledger_count=1
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_action_coverage.sh
BUSINESS_ACTION_COVERAGE_AUDIT: status=PASS
```

```text
DB_NAME=sc_demo python3 scripts/verify/p1_daily_business_form_usability_audit.py
[p1_daily_business_form_usability_audit] PASS
```

```text
python3 scripts/verify/finance_expense_claim_entry_context_audit.py
FINANCE_EXPENSE_CLAIM_ENTRY_CONTEXT_AUDIT: status=PASS
```

```text
make verify.baseline DB_NAME=sc_demo
[verify.baseline] PASS ALL on sc_demo
```
