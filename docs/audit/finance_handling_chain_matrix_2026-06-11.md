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

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_expense.approval_policy.audit
FINANCE_EXPENSE_APPROVAL_POLICY_AUDIT: status=PASS
covered: 12 sc.expense.claim business categories
evidence: category approval_policy_id=expense_claim_approval, optional approval path can complete, required approval path blocks approve/done before tier validation, validated approval can complete and write treasury ledger
```

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_cash_ledger.backfill_readiness.audit
FINANCE_LEGACY_CASH_LEDGER_BACKFILL_READINESS_AUDIT: status=PASS
expected_source_linked_ledger_count=113549
missing_source_linked_ledger_count=113549
existing_source_less_legacy_ledgers=18347
```

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_source_less_ledger.reconciliation.audit
FINANCE_LEGACY_SOURCE_LESS_LEDGER_RECONCILIATION_AUDIT: status=PASS
source_less_legacy_ledger_count=18347
exact_attachable_ledger_count=0
candidate_currency_mismatch=16006
no_candidate_by_legacy_record_id=2322
```

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make backfill.finance_legacy_treasury.currency
FINANCE_LEGACY_TREASURY_CURRENCY_BACKFILL: status=PASS updated_rows=18347

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_treasury.currency.audit
FINANCE_LEGACY_TREASURY_CURRENCY_BACKFILL: status=PASS mismatched_count=0

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_source_less_ledger.reconciliation.audit
FINANCE_LEGACY_SOURCE_LESS_LEDGER_RECONCILIATION_AUDIT: status=PASS
source_less_legacy_ledger_count=18347
exact_attachable_ledger_count=16006
no_candidate_by_legacy_record_id=2322
candidate_direction_mismatch=18
candidate_project_mismatch=1

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make backfill.finance_legacy_source_less_ledger.attach
FINANCE_LEGACY_SOURCE_LESS_LEDGER_ATTACH: status=PASS updated_rows=16006
before.source_less_legacy_ledger_count=18347
after.source_less_legacy_ledger_count=2341
after.source_linked_legacy_count=16006

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_source_less_ledger.attach.audit
FINANCE_LEGACY_SOURCE_LESS_LEDGER_ATTACH: status=PASS attachable_count=0 source_linked_legacy_count=16006

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_source_less_ledger.reconciliation.audit
FINANCE_LEGACY_SOURCE_LESS_LEDGER_RECONCILIATION_AUDIT: status=PASS
source_less_legacy_ledger_count=2341
already_source_linked=16006
exact_attachable_ledger_count=0

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make backfill.finance_legacy_source_linked_ledger.payment_request_boundary
FINANCE_LEGACY_SOURCE_LINKED_LEDGER_PAYMENT_REQUEST_BOUNDARY: status=PASS updated_rows=16006
after.boundary_violation_count=0

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_cash_ledger.backfill_readiness.audit
FINANCE_LEGACY_CASH_LEDGER_BACKFILL_READINESS_AUDIT: status=PASS
existing_source_linked_ledger_count=16006
missing_source_linked_ledger_count=97543
```

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make backfill.finance_legacy_handling.currency
FINANCE_LEGACY_HANDLING_CURRENCY_BACKFILL: status=PASS
updated_by_lane: expense_claim=10487, payment_execution=6098, receipt_income=4766

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_handling.currency.audit
FINANCE_LEGACY_HANDLING_CURRENCY_BACKFILL: status=PASS
mismatched_count=0
```

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make backfill.finance_legacy_cash_ledger
FINANCE_LEGACY_CASH_LEDGER_BACKFILL: status=PASS
inserted_rows=97543
after.existing_source_linked_ledger_count=113549
after.missing_source_linked_ledger_count=0

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_cash_ledger.backfill_readiness.audit
FINANCE_LEGACY_CASH_LEDGER_BACKFILL_READINESS_AUDIT: status=PASS
existing_source_linked_ledger_count=113549
missing_source_linked_ledger_count=0

COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_legacy_source_linked_ledger.payment_request_boundary.audit
FINANCE_LEGACY_SOURCE_LINKED_LEDGER_PAYMENT_REQUEST_BOUNDARY: status=PASS
legacy_source_linked_count=113549
boundary_violation_count=0
```

```text
COMPOSE_PROJECT_NAME=sc-backend-odoo-dev DB_NAME=sc_demo make verify.finance_expense_category.handling_policy.audit
FINANCE_EXPENSE_CATEGORY_HANDLING_POLICY_AUDIT: status=PASS
category_count=11
legacy_source_linked_ledger_missing_count=0
policy=经营现金类必须要求 payment_request_id 和账户字段；往来还款类 payment_request_policy=not_applicable，且不进入 payment.ledger
attachment_policy_runtime=无附件提交被拦截，补附件后可提交
```

HTTP/API 可见面验收结论：

- 支付申请：用户可见入口 `smart_construction_core.menu_sc_user_payment_apply_acceptance` 打开 `payment.request`，本地用户数据 29,549 条，已办样本可追到 `payment.ledger`；`payment.request.business_category_id` 已绑定 `finance.payment.apply.pay`/`finance.payment.apply.receive`，付款申请与收款申请按字典分类切分。
- 往来单位付款：用户可见入口 `smart_construction_core.menu_sc_partner_payment` 打开 `sc.payment.execution`，本地用户数据 24,049 条，入口和已办样本可读；`sc.payment.execution.business_category_id` 已绑定 `finance.payment.execution.partner`/`finance.payment.execution.company`，当前运行时门禁验证 38,164 条往来单位付款类、403 条公司财务支出类全部分类正确（含运行时样本）；HTTP smoke 已支持按 `sc.treasury.ledger(source_model='sc.payment.execution')` 反选办理样本，当前 80 条来源级台账样本可反选 20 条办理样本并追到下游资金台账。
- 到款确认/项目收款：用户可见入口 `smart_construction_core.menu_sc_engineering_progress_income` 打开 `sc.receipt.income`，本地用户数据 15,905 条，入口和已办样本可读；HTTP smoke 已支持按 `sc.treasury.ledger(source_model='sc.receipt.income')` 反选办理样本，当前 80 条来源级台账样本可反选 20 条办理样本并追到下游资金台账。
- 收款收入分类：`sc.receipt.income` 已新增正式 `business_category_id`，普通收款收入绑定 `finance.receipt.income.project`，工程进度款收入绑定 `finance.receipt.income.progress`；运行时门禁验证本地 25,099 条普通收款收入和 3,902 条工程进度款收入分类不漏不串。
- 项目费用报销单：用户可见入口 `smart_construction_core.menu_sc_project_expense_claim` 打开 `sc.expense.claim`，本地用户数据 37,013 条，入口和已办样本可读；HTTP smoke 已支持按 `sc.treasury.ledger(source_model='sc.expense.claim')` 反选办理样本，当前 80 条来源级台账样本可反选 20 条办理样本并追到下游资金台账。
- 扩展入口：`make verify.finance_handling.http_surface.smoke` 已覆盖 15 个用户可见财务办理入口，包括支付申请、付款执行、到款确认、费用/报销、投标保证金、合同保证金、扣款单/实缴/退回、还款登记、承包人还项目款和项目还公司款。`system.init` 当前只返回前 300 个导航行，smoke 对后置菜单使用 action 名称和模型兜底解析；兜底只解决验证取数，不改变菜单最终 action 绑定。
- 合同保证金支付/退回是行业模板入口，当前用户数据没有已办样本；HTTP smoke 只验证 action 可解析、页面契约可打开和分类策略可运行，不把样本数作为当前用户验收缺口。

历史已办事实现金流审计结论：

- `payment.ledger` 保持付款申请专用，不承接所有历史付款执行和费用事实；没有真实 `payment_request_id` 的历史现金流应进入 `sc.treasury.ledger`。
- 三类正式办理模型中具备项目和正金额的历史已办候选共 113,549 条，已全部具备来源级 `sc.treasury.ledger.source_model/source_res_id` 反查。
- 按来源拆分：`sc.payment.execution` 36,285 条付款流出，`sc.receipt.income` 26,439 条收款流入，`sc.expense.claim` 41,138 条费用/保证金/扣款流出和 9,687 条退回/收取流入。
- 现有 `sc.treasury.ledger` 已有 18,347 条 `legacy_actual_outflow`/`legacy_receipt` 台账，但 `source_model/source_res_id` 为空，不能证明与正式办理记录一一对应。
- 已修正本地 source-less legacy 台账币种基线：18,347 条 legacy 资金台账按项目公司币种从 `USD` 对齐为 `CNY`，并修正 `fresh_db_treasury_ledger_projection_write.py`，避免未来重放继续继承旧 `payment_request.currency_id`。
- 已将 16,006 条 source-less legacy 台账按 `legacy_record_id + project_id + direction + source_kind + amount + currency` 一对一补挂到正式办理事实，其中 12,846 条为 `sc.payment.execution`、3,160 条为 `sc.receipt.income`；补挂只更新来源字段和标记，不改业务金额、方向、日期和状态。
- 已清空上述 16,006 条来源级 legacy 台账的 `payment_request_id`，历史现金流以 `source_model/source_res_id` 为追溯口径；`payment_request_id` 仅保留给真实收付款申请生成的台账。
- 已确认用户历史财务办理事实币种基线为人民币，并在本地 `sc_demo` 将三类 legacy confirmed 正式办理事实按项目公司币种对齐为 `CNY`：费用/保证金/扣款 10,487 条、付款执行 6,098 条、收款登记 4,766 条，共 21,351 条；只更新 `currency_id` 和修正标记，不改金额、状态、项目、往来单位、来源和办理日期。复跑币种门禁后不一致数为 0。
- 已补齐 P0 财务新发生办理默认币种门禁：`payment.request`、`sc.payment.execution`、`sc.receipt.income`、`sc.expense.claim`、`sc.financing.loan`、`sc.self.funding.registration`、`sc.fund.account`、`sc.fund.account.operation`、`sc.invoice.registration`、`sc.tax.deduction.registration` 的 `default_get(currency_id)` 均为 `base.CNY`。
- 已补齐剩余 97,543 条来源级历史现金流台账，其中费用/保证金/扣款 50,825 条、付款执行 23,439 条、收款登记 23,279 条；迁移只插入缺失 `sc.treasury.ledger`，不修改原办理事实，且历史来源级现金流 `payment_request_id` 保持为空。
- 已补齐费用分类办理策略门禁：报销、项目费用、保证金支付/退回、扣款实缴/退回等经营现金类分类必须配置收付款申请和账户字段；还款登记、承包人还项目款、项目还公司款登记等往来类分类必须保持 `payment_request_id` 缺省且 `payment_request_policy=not_applicable`，下游只进入 `sc.interfund.movement.fact` 和 `sc.treasury.ledger`，不得进入 `payment.ledger`。
- 已补齐费用/保证金/扣款/还款附件强制策略：11 个 `sc.expense.claim` 分类默认 `attachment_policy=required`，手工新建单据提交、批准或完成前必须上传附件；历史迁移事实不 retroactive 强制。增强后的费用分类门禁验证无附件提交会被拦截，补附件后可提交。
- 已补齐费用/保证金/扣款/还款审批策略：12 个 `sc.expense.claim` 分类默认绑定 `expense_claim_approval`，同步时不覆盖客户已维护策略；免审批配置可提交后完成，启用审批配置时审批前不能批准或完成，tier validation 通过后才能完成并写入来源级资金台账。
- 已补齐扣款单非现金办理边界：`finance.deduction.bill` 不关联 `payment.request`，不生成 `payment.ledger` 或 `sc.treasury.ledger`，只作为非现金扣款事实完成办理；`finance.deduction.paid`、`finance.deduction.refund` 继续按真实付款/收款进入现金流。费用分类门禁已验证误挂收付款申请被拦截，无收付款申请完成后现金台账新增数为 0。
- 已补齐保证金收付现金流边界：投标/合同保证金支付必须走付款申请并生成 `payment.ledger`，保证金退回必须走收款申请并生成 `sc.treasury.ledger`；方向错配在费用单提交阶段被拦截。增强后的费用分类门禁已验证支付申请和退回申请均自动完成，且分别只生成对应现金流台账。
- 已修正借款类入口切分：承包人借项目款、项目借公司款登记按 `business_category_id.code` 明确切分，静态和运行时门禁均验证保存后仍留在正确入口，不再依赖 purpose 文本包含关系。
- 已修正通用借款申请默认分类：无明确“项目借公司款”或“借...项目...款”语义时保存为 `finance.loan.borrowing`，避免普通借款申请被默认归入项目借公司款；`validate_finance_business_category_runtime.sh` 已通过。
- 已修复扣款单页面契约 500：`action_sc_expense_claim_deduction_bill` 曾残留绑定旧 `sc.tax.deduction.registration` tree 视图，当前清空 action 级视图绑定后由 `sc.expense.claim` 标准视图加载；`扣款单位/扣款金额/扣款事由/附件/录入时间` 可见别名字段已补映射。
- 已增强公司-承包人责任余额可见面门禁：`make verify.company_contractor.responsibility_http.smoke` 现在覆盖入口打开、列表读取、按责任状态分组，以及从余额行执行“查看责任明细”并读取 `sc.company.contractor.responsibility.fact`；当前样本 `source_line_count=4`，钻取明细 4 条，首条明细保留来源模型 `sc.legacy.fund.confirmation.document`。
- 已把拨付/往来单位付款接入公司-承包人责任余额上下文：`sc.payment.execution` 继承责任上下文，列表和表单展示责任状态、到款可处理余额、到款超处理金额和自筹未退余额，并提供查看责任余额动作。`validate_company_contractor_responsibility_context.sh` 已验证付款执行按正式往来单位匹配责任余额 678 条。
- 已补付款执行责任余额动作约束：责任余额到款超处理时阻断付款；本次实付超过到款可处理余额时阻断；自筹未退作为提示继续保留用户认知。门禁已验证自筹未退不误阻断、超处理阻断、超余额阻断和余额内允许。
- 已补强正式自筹办理证据：`verify.self_funding.handling.audit` 直接校验自筹垫付/退回的 `sc.company.contractor.responsibility.fact`、`sc.treasury.ledger` 和 `sc.audit.log`，确保办理动作、责任余额和现金流三条口径一致；`verify.company_contractor.responsibility_fact.audit` 同步证明正式自筹收入/退回各 1 条纳入责任事实，且历史自筹收入 2,153 条、历史自筹退回 1,575 条仍全部覆盖。
- 剩余 source-less legacy 台账 2,341 条：2,322 条找不到正式候选，18 条方向不一致，1 条项目不一致，暂不自动补挂。
- 后续迁移脚本不得重复追加 113,549 条来源级台账；应以 `source_model/source_res_id/project_id/direction/source_kind` 为幂等键，剩余 2,341 条 source-less legacy 行需单独判断保留、补来源或作废策略，防止现金流翻倍。

```text
scripts/ops/validate_finance_business_categories.sh
FINANCE_BUSINESS_CATEGORY_ACTION_AUDIT: status=PASS
covered: 24 finance category candidates
evidence: category -> action -> menu binding, context defaults, domain coverage for new records
```

```text
DB_NAME=sc_demo scripts/ops/validate_finance_business_category_runtime.sh
FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: status=PASS
covered: 30 finance category candidates
evidence: create temp record from runtime action context, verify current runtime action domain can find it, and verify record-level category bindings
```

```text
DB_NAME=sc_demo scripts/ops/validate_business_category_dictionary.sh
BUSINESS_CATEGORY_DICTIONARY_AUDIT: status=PASS
covered: 54 business category template records
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
| 往来单位付款 | `sc.payment.execution` | `action_confirm`、`action_paid`、`action_cancel`、`action_on_tier_approved` | 新办理通过 `payment.request` 生成 `payment.ledger`；历史已办事实应通过 `sc.treasury.ledger` 来源级追溯现金流 | 办理入口可见面已通过 HTTP/API；12,846 条 source-less legacy 付款流出已补挂到付款执行；HTTP smoke 已按来源台账反选样本并追到 `sc.treasury.ledger` | 对剩余付款流出缺口做来源级现金流迁移，并补浏览器级抽样验收 |
| 到款确认表 | `sc.receipt.income` | `action_confirm`、`action_received`、`action_cancel`、`action_on_tier_approved` | 新办理通过收款申请生成 `sc.treasury.ledger`；历史已办事实通过 `sc.treasury.ledger` 来源级追溯现金流 | 办理入口可见面已通过 HTTP/API；普通收款收入和工程进度款收入已按 `business_category_id` 字典化，历史收款流入来源级台账覆盖已补齐 | 补项目收款状态约束与收款申请、销项发票、责任余额的分类策略联动 |
| 报销/费用单据 | `sc.expense.claim` | `action_submit`、`action_approve`、`action_done`、`action_cancel`、审批回调 | 新办理通过 `payment.request` 或往来款现金流生成台账；历史已办事实按方向进入 `sc.treasury.ledger` | 办理入口可见面已通过 HTTP/API；50,825 条历史费用/保证金/扣款候选缺来源级台账 | 按 `claim_type` 和业务分类区分经营收付、保证金、扣款、往来款，再做来源级现金流迁移 |
| 扣款单/扣款实缴/退回 | `sc.tax.deduction.registration` | 确认、已抵扣、取消 | 税务事实、项目经营口径 | 办理证据闭环、角色权限、下游税务事实追溯通过；抵扣登记入口已按 `business_category_id.code` 收紧 | 继续补转出、扣款抵扣等更细税务分类边界 |
| 账户间资金往来 | `sc.fund.account.operation` | 确认、完成、取消 | 账户资金往来事实、往来现金流台账 | 已接入 `business_category_id=finance.fund.transfer`；后端动作、关系必填、现金流追溯、历史回填就绪审计通过；内部往来分类策略已纳入 `verify.finance_interfund_category.handling_policy.audit` | 补浏览器级验收和账户余额回填策略 |
| 项目/承包人借还款 | `sc.financing.loan` / `sc.expense.claim` | 借款登记、还款登记 | 资金往来事实、项目资金口径、来源级资金台账 | 借出、借入、还款分类已按 `sc.business.category` 固化；新发生办理默认 `CNY` 且纳入 P0 币种门禁；不走收付款申请，不写 `payment.ledger`，通过 `sc.interfund.movement.fact` 与 `sc.treasury.ledger` 追溯 | 补浏览器级验收、利息/账户关系和公司-承包人责任余额约束 |
| 资金日报表 | `sc.fund.account.operation` | 确认、完成、取消 | 来源级 `sc.treasury.ledger(source_kind='daily_line')`、`sc.fund.account` 当前账面/银行余额 | 已接入 `business_category_id=finance.fund.daily_report`；办理分类、入口运行时、完成后现金流台账承接和账户余额回写通过；不进入 `payment.request`，不进入 `sc.interfund.movement.fact` | 补历史余额初始化/迁移策略和浏览器级抽样验收 |
| 历史资金日报快照 | `sc.legacy.fund.daily.snapshot.fact` | 历史事实查看 | 来源事实明细 | 表单契约通过 | 只作为历史追溯和后续日报汇总分析来源 |

## Finance Classification Dictionary Candidates

这些类别来自当前用户数据和已梳理菜单，是 Phase 1/Phase 2 的字典化候选项。短期可继续用 action/domain/context 实现，长期应进入可维护分类字典和行业模板。

| 分类编码候选 | 用户可见事项 | 正式模型 | 方向 | 建议必填关系 | 下游策略 |
| --- | --- | --- | --- | --- | --- |
| `finance.payment.apply.pay` | 付款申请 | `payment.request` | 付款 | 项目、合同、往来单位、金额、付款账户 | 绑定正式 `business_category_id`，完成后生成 `payment.ledger` |
| `finance.payment.apply.receive` | 收款申请 | `payment.request` | 收款 | 项目、合同、往来单位、金额、收款类别 | 绑定正式 `business_category_id`，完成后生成 `sc.treasury.ledger` |
| `finance.payment.execution.partner` | 往来单位付款 | `sc.payment.execution` | 付款执行 | 付款申请、项目、合同、往来单位、付款账户、收款账户、实付金额 | 绑定正式 `business_category_id`，同步付款申请，生成 `payment.ledger` |
| `finance.payment.execution.company` | 公司财务支出 | `sc.payment.execution` | 付款执行 | 项目、合同、往来单位、付款账户、收款账户、实付金额 | 绑定正式 `business_category_id`，生成付款执行现金流 |
| `finance.receipt.income.project` | 到款确认/项目收款 | `sc.receipt.income` | 收款确认 | 收款申请、项目、合同、往来单位、收款账户、收款金额 | 绑定正式 `business_category_id`，同步收款申请，生成 `sc.treasury.ledger` |
| `finance.expense.reimbursement` | 项目费用报销单 | `sc.expense.claim` | 付款 | 付款申请、项目、往来单位、报销金额、付款账户、收款账户 | 同步付款申请，生成 `payment.ledger` |
| `finance.deposit.bid.pay` | 投标保证金支付 | `sc.expense.claim` | 付款 | 项目/投标事项、往来单位、金额、付款账户、收款账户、付款申请 | 完成付款申请并生成 `payment.ledger` |
| `finance.deposit.bid.return` | 投标保证金退回 | `sc.expense.claim` | 收款/退回 | 项目/投标事项、往来单位、金额、收款账户、收款申请 | 完成收款申请并生成 `sc.treasury.ledger` |
| `finance.deposit.contract.pay` | 合同保证金支付 | `sc.expense.claim` | 付款 | 项目、合同、往来单位、金额、付款账户、收款账户、付款申请 | 完成付款申请并生成 `payment.ledger` |
| `finance.deposit.contract.return` | 合同保证金退回 | `sc.expense.claim` | 收款/退回 | 项目、合同、往来单位、金额、收款账户、收款申请 | 完成收款申请并生成 `sc.treasury.ledger` |
| `finance.deduction.bill` | 扣款单 | `sc.expense.claim` / `sc.tax.deduction.registration` | 非现金/扣款 | 项目、合同/发票、往来单位、扣款金额、扣款原因 | 非现金扣款事实；不得关联收付款申请，不写现金流台账 |
| `finance.deduction.paid` | 扣款实缴登记 | `sc.expense.claim` / `sc.tax.deduction.registration` | 付款/税务 | 项目、往来单位、金额、账户、税务依据 | 进入付款台账和税务事实 |
| `finance.deduction.refund` | 扣款实缴退回 | `sc.expense.claim` / `sc.tax.deduction.registration` | 收款/退回 | 项目、往来单位、金额、收款账户、退回原因 | 进入资金台账和税务事实 |
| `invoice.output.registration` | 销项开票登记 | `sc.invoice.registration` | 销项/税务 | 项目、合同、往来单位、发票号、金额、税额 | 进入发票分类汇总，作为收入合同和税务口径依据 |
| `invoice.input.report` | 进项税额上报 | `sc.invoice.registration` | 进项/税务 | 项目、合同、往来单位、发票号、金额、税额 | 进入发票分类汇总，作为成本和抵扣来源候选 |
| `tax.deduction.registration` | 抵扣登记 | `sc.tax.deduction.registration` | 非现金税务 | 项目、往来单位、发票号、认证日期、抵扣金额、抵扣税额 | 以 `noncash_tax` 进入项目税务事实，余额影响为 0 |
| `finance.fund.transfer` | 账户间资金往来 | `sc.fund.account.operation` | 转账 | 来源账户、目标账户、金额、账户币种一致 | 生成账户资金往来事实和往来现金流台账；不关联收付款申请 |
| `finance.loan.project_borrow_company` | 项目借公司款登记 | `sc.financing.loan` | 借入 | 项目、往来单位、金额、单据日期 | 生成内部往来事实和项目资金流入台账；不关联收付款申请 |
| `finance.loan.contractor_project_borrow` | 承包人借项目款 | `sc.financing.loan` | 借出 | 项目、承包人、金额、单据日期 | 生成内部往来事实和项目资金流出台账；不关联收付款申请 |
| `finance.repayment.project_company` | 项目还公司款登记 | `sc.expense.claim` | 还款流出 | 项目、往来单位、金额、还款类型 | 生成内部往来事实和项目资金流出台账；不关联收付款申请 |
| `finance.repayment.contractor_project` | 承包人还项目款 | `sc.expense.claim` | 还款流入 | 项目、承包人、金额、还款类型 | 生成内部往来事实和项目资金流入台账；不关联收付款申请 |

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
- `make verify.finance_interfund_category.handling_policy.audit` 已覆盖 7 个内部往来分类：账户间资金往来、借款申请、承包人借项目款、项目借公司款登记、还款登记、承包人还项目款、项目还公司款登记。当前 `sc_demo` 中 `sc.interfund.movement.fact` 共 1,543 条，全部为高置信分类；正金额借款/还款事实通过 `source_model/source_res_id` 追溯到 `sc.treasury.ledger` 的缺口为 0，零金额历史事实保留为可见分类事实，不强制生成现金流台账。

## Iteration Evidence - 2026-06-11 Finance Category Action Mapping

本轮把财务“分类字典化”的原则推进到可执行静态门禁：

- 新增 `scripts/verify/finance_business_category_action_audit.py`。
- 新增 `scripts/ops/validate_finance_business_categories.sh`。
- 覆盖 24 个财务分类候选，包括支付申请、往来单位付款、公司财务支出、收入、工程进度款收入、报销/项目费用、保证金、扣款、账户资金、资金日报、余额调整、借还款。
- 费用/保证金/扣款/还款 12 个 `sc.expense.claim` 用户入口已收紧为 `business_category_id.code` 域，action context 同步写入 `default_business_category_code`；`claim_type`、`expense_type`、`guarantee_type` 继续作为业务事实字段和历史回填兜底，不再作为入口长期锚点。
- 发票/税务 5 个用户入口已收紧为 `business_category_id.code` 域，action context 同步写入 `default_business_category_code`；`source_kind`、`direction`、`invoice_content`、`is_transfer_out` 继续作为事实字段和历史兼容兜底，不再作为入口长期锚点。
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
  - `action_payment_request_receive`：收款申请新建保存后仍留在收款申请入口。
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
  - 按业务分类执行附件策略；`attachment_policy=required` 的手工新建单据无附件不能提交、批准或完成。
  - 业务必备字段缺失时不能继续办理。

## Delivery Gaps To Close Next

当前审计未发现 P0 表单阻断，因此下一步不应做无目标的代码修补。Phase 1 下一轮按以下顺序推进：

1. 公司-承包人责任余额办理约束：先把到款确认、自筹垫付/退回、拨付、扣款、退回、自筹抵扣和收款核销的读取口径接到具体办理动作。
2. 扩展业务关系策略：账户间资金往来、项目/承包人借还款、扣款/税务登记继续补关系必填门禁。
3. 浏览器级办理验收：为支付申请、往来单位付款、到款确认、费用单据补浏览器级验收记录，覆盖新建、附件、提交、审批、完成和取消。
4. 正式交付清单：汇总角色账号、基础数据、首批真实业务数据导入/锁定、回滚和验收脚本。
5. 报表后置：只在以上办理事实稳定后，再完善应收应付、账户收支、资金日报汇总分析等汇总入口；资金日报登记本身属于账户资金办理链路，不能再作为纯报表后置。

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

## Iteration Evidence - 2026-06-12 Company Contractor Responsibility Gates

本轮明确资金办理链路中的责任约束边界：

- 付款执行：公司向承包人继续拨付时，读取公司-承包人责任余额；到款超处理阻断，实付金额超过到款可处理余额阻断。
- 扣款单：非现金扣款事实不走 `payment.request`，但同样消耗到款可处理余额；到款超处理阻断，扣款金额超过到款可处理余额阻断。
- 扣款抵扣：`sc.tax.deduction.registration` 保留税务抵扣办理口径；只有存在 `withholding_amount` 时，在 `action_deduct` 终态动作读取公司-承包人责任余额，到款超处理阻断，扣款金额超过到款可处理余额阻断。
- 自筹未退：当前作为责任提示，不在付款执行和扣款单上硬阻断。
- 普通税务抵扣、扣款实缴、扣款退回保留各自办理口径，不与扣款单合并为单一入口或单一台账口径。

验证结果：

```text
python3 -m py_compile addons/smart_construction_core/models/support/company_contractor_responsibility_context_mixin.py addons/smart_construction_core/models/core/payment_execution.py addons/smart_construction_core/models/core/expense_claim.py addons/smart_construction_core/models/core/tax_deduction_registration.py scripts/verify/company_contractor_responsibility_context_audit.py
PASS

git diff --check
PASS

DB_NAME=sc_demo scripts/ops/validate_company_contractor_responsibility_context.sh
PASS
tax_deduction_responsibility_constraints includes action_deduct_blocks_over_processed_responsibility
```

## Iteration Evidence - 2026-06-12 Self Funding Source Context

本轮没有把历史自筹源表改造成可编辑办理单，而是先补齐用户验收和责任解释所需的可见上下文：

- 自筹垫付收入和自筹垫付退回入口继续只读，保留用户旧认知。
- 源单列表和表单展示公司-承包人责任状态、自筹未退余额，并提供责任余额钻取。
- 责任余额仍以 `income/refund` 正式族计算；可见参考族只用于追溯。
- 正式新增自筹办理还未完成，需要后续新增登记/审批/确认动作和现金台账或责任事实写入口径。

验证结果：

```text
CODEX_MODE=fast CODEX_NEED_UPGRADE=1 MODULE=smart_construction_core DB_NAME=sc_demo make mod.upgrade
PASS

DB_NAME=sc_demo scripts/ops/validate_company_contractor_responsibility_context.sh
PASS

DB_NAME=sc_demo make verify.company_contractor.responsibility_http.smoke
PASS

DB_NAME=sc_demo make verify.finance_handling.http_surface.smoke
PASS entries=17, includes self_funding_income/self_funding_refund
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
