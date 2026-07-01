# 正式字段稳定化专题 v1

## 目标

正式产品的用户办理面、配置面和发布基线必须使用稳定的业务字段名和业务标签，不再把迁移、验收、低代码兼容阶段的过渡字段作为长期产品事实。

本专题不是删除历史追溯能力。旧系统来源、迁移证据、审计字段可以保留在内部模型和审计入口，但不得进入正式办理面、正式配置面和正式发布基线。

## 边界

正式面包括：

- `addons/smart_construction_core/models/core`
- `addons/smart_construction_core/models/projection`
- `addons/smart_construction_core/views/core`
- `addons/smart_construction_core/views/support/user_confirmed_formal_*`
- `addons/smart_construction_core/data/view_orchestration_*`
- `addons/smart_construction_core/data/p1_daily_business_form_orchestration_contract_data.xml`

内部面包括：

- 迁移事实模型
- 历史审计模型
- 来源追溯模型
- 修复、重放、审计脚本
- 只供研发/实施使用的 support audit 入口

## 不应进入正式面的过渡字段

- `p1_visible_*`
- `legacy_visible_*`
- `legacy_attachment_ref` / `legacy_line_attachment_ref` / `legacy_attachment_name` / `legacy_attachment_path`
- `creator_legacy_user_id`
- `legacy_residual_reason`
- `accepted_visible_*`
- `user_acceptance_*`
- `CODEX_*`
- `*_HIDDEN`

`legacy_*` 和 `source_*` 不是按前缀一刀切。若字段承载的是旧系统 ID、来源表、来源记录、导入批次、迁移证据，则只能留在内部审计面；若字段承载的是正式业务上下文，应改名为业务字段。

## 当前债务基线

当前静态审计命令：

```bash
make verify.formal_surface.transition_field_audit
```

初始债务：

| 分类 | 前缀 | 数量 |
| --- | --- | ---: |
| formal_config_contract | p1_visible | 0 |
| formal_config_contract | legacy_visible | 0 |
| formal_confirmed_view | legacy_visible | 0 |
| formal_confirmed_view | p1_visible | 0 |
| formal_confirmed_view | user_acceptance | 0 |
| formal_confirmed_view | accepted_visible | 0 |
| formal_core_model | legacy_visible | 0 |
| formal_core_model | user_acceptance | 0 |
| formal_core_view | legacy_visible | 0 |
| formal_projection_model | legacy_visible | 0 |

本专题已清理正式办理视图、正式 core 模型和发布配置合同中的过渡字段命名；当前正式面只允许稳定模型/视图字段。配置合同中的 `p1_visible_*` 已清零。当前预算基线位于：

`scripts/verify/baselines/formal_surface_transition_field_budget_v1.json`

预算只能下降，不能上升。新增分类或新增前缀命中必须失败。

## 执行顺序

### 第一批：配置和办理面的防新增

已完成：

- 增加 `scripts/verify/formal_surface_transition_field_audit.py`
- 增加预算基线 `formal_surface_transition_field_budget_v1.json`
- 接入 `make verify.formal_surface.transition_field_audit`
- 接入 `verify.user_confirmed.formal_surface.locked`
- `formal_surface_transition_field_audit` 已扩展覆盖历史附件引用、历史附件名/路径、历史录入人 ID 和历史残余原因载体，正式面保持零预算
- 增加 `scripts/verify/formal_config_p1_alias_contract_audit.py`，静态输出配置合同中剩余 `p1_visible_*` 的模型、中文标签和可见性来源；隐藏别名或未知来源别名直接失败
- 增加 `scripts/verify/formal_config_p1_candidate_runtime_audit.py`，在 Odoo 运行时验证静态候选字段是否真实存在，并区分稳定模型字段候选与 `legacy_visible_*` / `accepted_visible_*` / `user_acceptance_*` 等过渡候选

### 第二批：配置契约字段稳定化

`formal_config_contract.p1_visible=0` 已完成。

当前边界事实：

- 配置合同中的 `p1_visible_*` 来源于 `addons/smart_construction_core/models/support/p1_daily_business_visible_alias_fields.py` 的 `P1_ALIAS_LABELS` / `P1_ALIAS_COMPAT_LABELS`
- 字段名由中文标签经过 `_alias_field_name(label)` 生成，即 `p1_visible_` + `sha1(label)[:12]`
- 发布配置合同不得再保留隐藏的 `p1_visible_*`；仍可见的别名必须先有明确中文标签来源，再逐步晋升为正式模型字段或正式视图字段
- 本地事实清单输出到 `artifacts/backend/formal_config_p1_alias_contract_audit.json` 和 `artifacts/backend/formal_config_p1_alias_contract_audit_rows.csv`
- 静态候选只代表来源线索，不代表可以直接替换；必须通过运行时模型字段校验后才可作为迁移候选
- 运行时事实清单输出到 `artifacts/backend/formal_config_p1_candidate_runtime_audit.json`
- 已将 174 个不会制造重复列、且只有一个稳定正式候选的配置字段从 `p1_visible_*` 晋升为正式字段名
- 已将 79 个有明确模型专属正式字段前缀、且不会制造重复列的配置字段从 `p1_visible_*` 晋升为正式字段名
- 已将 49 个首选候选为正式展示/摘要字段且不会制造重复列的配置字段从 `p1_visible_*` 晋升为正式字段名
- 已为最后 141 个配置字段补齐一标签一字段的正式业务投影字段，并将发布配置合同全部改挂正式字段名
- 当前发布配置合同中 `p1_visible_*` 剩余为 0
- 当前稳定候选缺口已归零；后续配置合同从 `p1_visible_*` 切换到正式字段时，不再允许新增运行时缺口或过渡候选
- `sc.material.rental.order` 已将 10 个仅有过渡候选的字段稳定为按 `legacy_acceptance_label` 分支计算的正式投影字段：`invoiced_amount_text`、`paid_amount_text`、`unpaid_amount_text`、`uninvoiced_amount_text`、`contract_sign_date_text`、`rental_material_name`、`rental_material_spec`、`rental_quantity_text`、`rental_unit_price_text`、`rental_deposit_amount_text`
- `sc.material.rental.order` 已将 3 个开户信息缺口稳定为供应商结算账户 related 字段：`account_holder`、`bank_name`、`bank_account`
- `sc.financing.loan` 已将 3 个账户信息缺口稳定为正式投影字段：`loan_account`、`loan_bank_name`、`repayment_account`；本地 `sc_demo` 校验 `贷款账户` 645 条、`贷款银行` 554 条、`还款账户` 644 条与原 p1 办理面字段一致，mismatch 均为 0
- `sc.material.settlement` 已将 2 个支付信息缺口指向已有正式汇总字段：`payment_paid_amount`、`payment_remaining_amount`；本地 `sc_demo` 当前无材料结算记录，已完成运行时字段边界校验，无历史值样本可比对
- `sc.labor.usage` 已修正 3 个 p1 办理面误映射字段，并稳定为正式投影字段：`document_date_text`、`construction_part`、`amount_total`；本地 `sc_demo` 校验 `单据日期` 9045 条、`施工部位` 7484 条、`总金额` 9046 条与 p1 办理面字段一致，mismatch 均为 0
- `sc.labor.settlement` 已将 4 个付款/申请金额缺口稳定为正式边界字段：`payment_paid_amount`、`payment_unpaid_amount`、`payment_requested_amount`、`payment_unrequested_amount`；当前产品尚未将劳务结算接入付款申请关系，字段口径为已付款/已申请 0，未付款/未申请等于结算金额；本地 `sc_demo` 当前无劳务结算记录，已完成运行时字段边界校验，无历史值样本可比对
- `sc.equipment.settlement` 已将 5 个结算/付款/申请金额缺口稳定为正式边界字段：`settlement_content`、`payment_paid_amount`、`payment_unpaid_amount`、`payment_requested_amount`、`payment_unrequested_amount`；当前产品尚未将设备结算接入付款申请关系，字段口径为已付款/已申请 0，未付款/未申请等于结算金额，结算内容取结算行设备名称摘要并回退到备注；本地 `sc_demo` 当前无设备结算记录，已完成运行时字段边界校验，无历史值样本可比对
- `sc.subcontract.settlement` 已将 4 个付款/申请金额缺口稳定为正式边界字段：`payment_paid_amount`、`payment_unpaid_amount`、`payment_requested_amount`、`payment_unrequested_amount`；当前产品尚未将分包结算接入付款申请关系，字段口径为已付款/已申请 0，未付款/未申请等于结算金额；本地 `sc_demo` 当前无分包结算记录，已完成运行时字段边界校验，无历史值样本可比对
- `sc.material.inbound` 已将 4 个税率/付款/结算金额缺口稳定为正式边界字段：`tax_rate_text`、`payment_paid_amount`、`payment_unpaid_amount`、`settlement_settled_amount`；当前材料入库模型不承载税率、付款申请或结算关系，字段口径为税率空、已付款 0、未付款等于入库金额合计、已结算 0；本地 `sc_demo` 校验 13588 条记录字段存在，并抽样确认金额 100 的入库单未付款金额为 100
- `sc.subcontract.request` 已将 5 个类型/数量/单价/金额缺口稳定为正式汇总字段：`subcontract_type_text`、`quantity_total`、`price_unit`、`amount_total`、`monthly_amount_total`；当前分包申请模型不承载分包类型，字段口径为类型空、数量汇总申请明细数量、单价按预计金额除以数量、金额/本月合价等于申请预计金额；本地 `sc_demo` 校验 725 条申请字段存在，并抽样确认数量 855、预计金额 33430.5 时单价为 39.1
- `sc.material.purchase.request` 已将 6 个金额/税率缺口稳定为正式边界字段：`amount_total`、`invoice_amount`、`payment_paid_amount`、`payment_unpaid_amount`、`uninvoiced_amount`、`tax_rate_text`；当前采购申请模型不承载发票、付款或税率链路，字段口径为总金额汇总申请明细预计金额，已开票/已付款为 0，未开票/未付款等于总金额，税率为空；本地 `sc_demo` 当前 4 条采购申请且无申请明细，已完成运行时字段边界校验，无历史值样本可比对
- `sc.equipment.usage` 已将 6 个日期/规格/单位/工时/单价/金额缺口稳定为直营验收正式投影字段：`document_date`、`specification`、`uom_text`、`work_hours`、`price_unit`、`amount`；字段口径为直营机械台班记录取 `legacy_visible_04/08/09/10/11/12`，非直营记录回退到使用日期、使用台时和 0 金额；本地 `sc_demo` 校验 17502 条设备台班字段存在，并抽样 200 条确认规格、单位、工作时间、单价、金额与历史可见值 mismatch 为 0
- `sc.subcontract.register` 已将 7 个签订时间/数量/金额/开票/付款缺口稳定为正式边界字段：`sign_date`、`quantity_total`、`amount_total`、`invoice_amount`、`paid_amount`、`unpaid_amount`、`uninvoiced_amount`；当前分包登记模型不承载发票或付款链路，字段口径为签订时间取登记日期、总数量汇总登记明细合同数量、金额等于登记合同金额、已开票/已付款为 0、未开票/未付款等于金额；本地 `sc_demo` 当前无分包登记记录，已完成运行时字段边界校验，无历史值样本可比对
- `sc.equipment.request` 已将 8 个数量/金额/税率/增值税类型缺口稳定为正式边界字段：`quantity_total`、`amount_total`、`invoice_amount`、`paid_amount`、`unpaid_amount`、`uninvoiced_amount`、`tax_rate_text`、`vat_type_text`；当前设备申请模型不承载金额、税率、发票或付款链路，字段口径为总数量汇总申请明细申请台数，金额/票款为 0，税率和增值税类型为空；本地 `sc_demo` 当前 4 条设备申请且无申请明细，已完成运行时字段边界校验，无历史值样本可比对
- `sc.labor.request` 已将 9 个负责人/金额/结算/票款/计价/施工部位缺口稳定为正式边界字段：`owner_id`、`amount_total`、`settlement_ratio`、`invoice_amount`、`paid_amount`、`unpaid_amount`、`uninvoiced_amount`、`pricing_method`、`construction_part`；当前劳务申请模型不承载金额、结算、发票或付款链路，字段口径为负责人取申请人，金额/结算/票款为 0，计价方式为空，施工部位取申请明细作业内容摘要；本地 `sc_demo` 当前 4 条劳务申请且无申请明细，已完成运行时字段边界校验，无历史值样本可比对
- 运行时预算基线位于 `scripts/verify/baselines/formal_config_p1_candidate_runtime_budget_v1.json`；`total_hits`、`without_existing_runtime_candidate_hits`、`without_stable_formal_candidate_hits`、`transition_candidate_only_hits` 只能下降，不能上升
- 工程进度款收入登记入口以正式业务分类 `business_category_id.code = finance.receipt.income.progress` 作为产品锚点；历史来源字段只作为迁移追溯事实，不能再作为办理入口主边界
- 公司财务支出历史验收数据可通过 P4 受控入口 `company_finance_expense.payment_execution.backfill.write` 从 `sc.expense.claim` 回填到正式 `sc.payment.execution`；该入口仅用于迁移/修复复跑，不是长期产品事实来源，本轮只完成 `make -n` 和脚本编译校验，未执行写库
- `sc.business.category` 属于发布配置字典，不属于用户办理面单据，录入元数据门禁不对它强制要求；`sc.self.funding.registration` 属于用户办理面，必须展示正式录入人/录入时间字段
- 配置面字段来源是 `ui.business.config.contract.view_orchestration.views.tree.columns`，办理面字段来源是 `ui.contract.v2.layoutContract.listProfile.columns`；正式产品要求字段顺序、字段集合和用户可见标签三者同时一致，不能只看字段名对齐
- `收入合同结算` / `支出合同结算` 曾存在历史发布契约仍引用 `user_acceptance_*` 的问题；已通过 `ui.business.config.contract.sc_sync_settlement_formal_list_contracts()` 在模块升级链路中将两个 action 的已发布 tree 契约稳定为 `settlement_acceptance_*` 字段和中文标签
- 当前 `make verify.business_config.list_config_boundary` 本地校验结果为 `checked=307 mismatches=0 errors=0 skipped=1`；唯一 skipped 是默认视图非列表的 `项目驾驶舱`。该门禁已拦截 `legacy_attachment_ref`、`legacy_line_attachment_ref`、`legacy_attachment_name`、`legacy_attachment_path`、`creator_legacy_user_id`、`legacy_residual_reason` 这类显式历史载体字段名回流到已发布列表配置；既有 P1/legacy 过渡字段仍按技术标签泄漏规则逐步治理

目标：

- 发布基线配置不再引用 `p1_visible_*`
- `ui.business.config.contract.view_orchestration.views.tree.columns` 使用正式字段名
- 配置面和办理面继续通过 `verify.business_config.list_config_boundary`

处理方式：

- 为每个 `p1_visible_*` 建立正式字段映射
- 已存在正式字段时直接替换
- 不存在正式字段时新增 compute/store 或迁移字段
- 更新生成契约和对应数据迁移
- 下调预算

### 第三批：用户确认正式视图稳定化

已完成：

- `formal_confirmed_view.legacy_visible=0`
- `formal_confirmed_view.p1_visible=0`

目标：

- `user_confirmed_formal_list_views.xml`
- `user_confirmed_formal_form_views.xml`
- `user_confirmed_formal_list_alignment_views.xml`

不再直接引用过渡字段。

### 第四批：核心模型和核心视图稳定化

优先处理：

- `payment.request`
- `sc.invoice.registration`
- `sc.payment.execution`
- `sc.expense.claim`
- `sc.office.admin.document`
- `sc.hr.payroll.document`
- `sc.fund.account.operation`

目标：

- core 模型中业务字段使用正式命名
- 旧字段仅保留为 internal provenance
- core 视图不再暴露 `legacy_visible_*`

### 第五批：投影模型稳定化

投影模型中的 `legacy_visible_*` 应改为业务摘要、来源说明或内部追溯字段。

## 验收命令

每批清理至少运行：

```bash
make verify.formal_surface.transition_field_audit
make verify.core_history_field.physical_boundary_audit
make verify.formal_config.p1_candidate_runtime_audit DB_NAME=sc_demo PROJECT=sc-backend-odoo-dev COMPOSE_PROJECT_NAME=sc-backend-odoo-dev
make verify.business_config.list_config_boundary DB_NAME=sc_demo PROJECT=sc-backend-odoo-dev COMPOSE_PROJECT_NAME=sc-backend-odoo-dev
```

## 用户数据产品字段覆盖矩阵

正式产品必须完整承载用户数据，但不能把旧系统页面列名原样固化为产品逻辑。`make verify.user_data.product_field_coverage.matrix` 以 P1 用户可见历史标签为输入，输出每个标签当前由哪类字段承载：

- `formal_product`：已经由正式产品字段承载
- `source_trace`：仍主要依赖来源/旧系统追溯字段，可对账但未完全产品化
- `transition_alias`：仍依赖 `p1_visible_*` / `legacy_visible_*` 等过渡别名
- `history_carrier`：仍依赖显式历史载体
- `missing`：未找到当前承载字段

当前 `sc_demo` 基线：`label_count=832`，`formal_product=832`，`backlog_count=0`，其中 `source_trace=0`、`transition_alias=0`、`missing=0`。`sc.financing.loan` 已将 `申请部门`、`申请时间`、`是否预算内`、`实际借款金额`、`主要资金使用安排`、`开户银行`、`借款账号`、`实际批复金额`、`申请金额`、`预计归还时间`、`借款类型` 从矩阵 `missing` 吸纳为可编辑正式产品字段，645 条历史融资借款记录均有正式承载值；新办理可直接录入这些字段，金额、用途、到期日、单据日期会同步到底层办理字段，历史确认单据也允许维护这些正式业务字段。`sc.office.admin.document` 已将印章使用审批表的 `用印时间`、`用印部门`、`用印申请人`、`用印部门负责人签字`、`用印种类`、`用印文本名称及文号`、`经办人签字`、`领导签字`、`份数`、`归还时间`、`合同金额`、`合同编号`、`所属公司`、`使用印章公司`、`是否外带` 吸纳为可编辑正式产品字段，新办/编辑会同步到底层 `use_date/use_purpose/return_date/amount` 办理字段，历史回填脚本负责把 custom 历史列搬入正式字段。`sc.business.entity` 已将单据状态、推送结果、项目名称、合作类型、开户银行、账号/开户账号/银行账号、统一社会信用代码、主税率、收款金额、付款金额、开户姓名、录入人、录入时间吸纳为可编辑正式主数据/业务字段，11077 条历史往来单位记录已回填为正式字段。`sc.document.admin.document` 已将资料借阅的项目名称、申请日期、借阅部门、借阅人、联系方式、借阅形式、负责人、归还申请/确认时间、是否归还、归还日期、修改与审定意见等标签吸纳为可编辑正式办理字段，29 条历史资料借阅记录已回填，新增和编辑可直接维护这些字段。`construction.contract` 的 `工程内容` 已从 `legacy_visible_engineering_content` 过渡列切回正式可编辑 `engineering_content` 字段，合同新办和编辑均可直接维护。`sc.legacy.invoice.tax.fact` 已将状态、开票单位、发票提供人/单位、价税合计、税额、不含税金额吸纳为可编辑正式发票税务字段，31072 条历史发票税额记录已回填。`tender.bid` 已将申请人、申请日期、备注、录入时间吸纳为可编辑正式投标办理字段，13101 条投标记录已补齐申请日期/录入时间，12994 条补齐申请人，10142 条补齐备注；新增和编辑投标记录可直接维护这些字段，`source_created_*` 与 `legacy_*` 仅保留为来源痕迹。最后一批剩余录入/登记类标签已映射到各行业模型既有正式经办和业务日期字段：设备台班 `recorder_id/usage_date`、材料入库 `keeper_id/inbound_date`、人事薪酬 `requester_id/business_date`、标书购买 `applicant_id/apply_date`，以及各申请/结算/登记模型的 `requester_id/owner_id/responsible_id` 和 `request_date/settlement_date/register_date`；`sc.legacy.user.profile` 的 `legacy_created_at` 是历史用户画像自身建立时间，按该模型正式资料字段计入。后续新增 P1 标签必须直接落到正式产品字段，矩阵 backlog 必须保持 0；`make verify.user_data.product_field_coverage.matrix` 已升级为门禁，`backlog_count > 0` 会直接失败。

## 行业模块办理能力边界审计

`make verify.industry_module.handling_capability_boundary` 用 P1 用户可见标签反查当前承载字段，并按行业模块办理能力边界分类：行业模块必须定义正式字段、表单、可编辑性、流程和下游办理语义；用户模块只负责把历史数据填入正式字段并保留来源痕迹。

当前审计基线：`label_count=832`，`industry_editable_product_field=634`，`industry_derived_product_field=170`，`industry_operational_metadata=28`，`action_required=0`。当前已无 `user_history_transition_field`、`source_trace_only`、`missing` 或 `history_carrier` 待处理项；审计产物写入 `artifacts/backend/industry_module_handling_capability_boundary_audit.json`。`make verify.industry_module.handling_capability_boundary` 已升级为门禁，`action_required_count > 0` 会直接失败。

## 后续专题：core 历史字段物理剥离

正式面稳定化已证明过渡字段不再进入用户办理面、配置面和发布基线。下一阶段处理更严格的物理分离：`smart_construction_core` 的 core/projection 模型不再新增历史用户数据载体，既有 `legacy_visible_*` 动态字段和引用必须逐批迁往 `smart_construction_custom` 或 support/history carrier。

当前预算门禁：

```bash
make verify.core_history_field.physical_boundary_audit
```

当前基线位于 `scripts/verify/baselines/core_history_field_physical_boundary_budget_v1.json`，`total_hits=0`。该预算只能保持为 0，不能上升。审计同时覆盖直接文本和拆分/格式化构造出的 `legacy_visible` 字段名、`creator_legacy_user_id` 这类历史用户 ID 载体，以及 `legacy_residual_reason` 这类历史残余说明，避免 core/projection 通过字符串拼接或审计字段声明重新耦合历史用户数据。`sc.expense.claim` 与 `sc.financing.loan` 的历史可见字段声明已迁入 `smart_construction_custom`；融资借款的历史往来方 ID、历史金额字段、历史附件引用也已从 core 模型和 core 视图迁出；项目台账历史附件引用已从 core support 迁移承载、core 项目表单、core 表单编排配置和付款执行迁移默认配置迁入 custom 用户历史扩展；`sc.invoice.registration` 的历史附件引用已从 core 字段、core 迁移来源页、core 写保护白名单和 core 业务分类 seed 迁入 custom hook；core 业务分类 seed 不再发布 `legacy_visible_attachment` 历史附件字段，正式附件入口保留 `attachment_ids`/`attachment_text`；`sc.construction.diary` 的历史附件引用、明细附件引用、附件名和附件路径已从 core 模型迁入 custom 用户历史扩展；`sc.general.contract` 的历史附件引用已从 core 模型迁入 custom 用户历史扩展；`sc.fund.account.operation` 的历史字段已由 custom 承载，资金账户操作历史附件引用也已从 core 模型、core 迁移来源页和 core 正式配置投影 source mapping 迁出；`sc.settlement.order` 的历史附件引用已从 core 模型和附件计数依赖迁入 custom hook，正式附件数量在 core 仅依赖正式附件关系并通过可覆盖钩子读取历史 fallback，初始化回填入口也改为中性的 history surface hook；`sc.receipt.income` 的历史附件引用已从 core 模型和 core 列表视图迁入 custom hook，工程进度款收入登记正式列表改用 `receipt_income_attachment_text_display` 展示附件；direct acceptance 共用历史验收载体已从 P1 core 模型目录归类到 support/history carrier。core 业务分类 seed 的 `form_policy_json` 不再发布任何 `legacy_visible_*` 历史可见字段，`formal_surface_transition_field_audit` 已覆盖该 seed 并保持零预算。隐藏的历史列回填、正式可见 fallback hook、历史录入人 ID 字段和历史残余说明字段已移到 custom/support，core/projection 不再构造 `legacy_visible_*` 历史字段名，也不再声明 `creator_legacy_user_id` 或 `legacy_residual_reason`。

涉及模型字段、XML data 或视图时，还需升级模块并跑正式面锁定验收：

```bash
CODEX_MODE=gate CODEX_NEED_UPGRADE=1 MODULE="smart_core,smart_construction_core" DB_NAME=sc_demo PROJECT=sc-backend-odoo-dev COMPOSE_PROJECT_NAME=sc-backend-odoo-dev make mod.upgrade
make verify.user_confirmed.formal_surface.locked DB_NAME=sc_demo PROJECT=sc-backend-odoo-dev COMPOSE_PROJECT_NAME=sc-backend-odoo-dev
```
