# Workflow State Inventory

- Generated: 2026-06-15T04:03:28Z
- Database: sc_demo
- Models with workflow signals: 149

## Summary

- `attainment_state`: 1 models
- `candidate_state`: 1 models
- `lifecycle_state`: 3 models
- `mapping_state`: 5 models
- `projection_state`: 1 models
- `promotion_state`: 1 models
- `responsibility_state`: 1 models
- `review_state`: 1 models
- `sc_state`: 1 models
- `state`: 104 models
- `suggested_state`: 2 models
- tier definitions present: 0 models
- approval fields present: 20 models
- workflow methods present: 74 models
- workflowContract covered: 71 models
- workflowContract uncovered: 78 models

## Workflow Contract Coverage

- Covered profiles: `construction.contract`, `construction.contract.expense`, `construction.contract.income`, `payment.request`, `project.material.plan`, `project.progress.entry`, `project.risk.action`, `project.settlement`, `sc.attendance.checkin`, `sc.construction.diary`, `sc.contract.event`, `sc.dashboard.cockpit.fact`, `sc.document.admin.document`, `sc.edition.release.snapshot`, `sc.equipment.plan`, `sc.equipment.price`, `sc.equipment.request`, `sc.equipment.settlement`, `sc.equipment.usage`, `sc.expense.claim`, `sc.financing.loan`, `sc.fund.account.operation`, `sc.general.contract`, `sc.hazard.source`, `sc.hr.payroll.document`, `sc.invoice.registration`, `sc.labor.plan`, `sc.labor.price`, `sc.labor.request`, `sc.labor.settlement`, `sc.labor.usage`, `sc.legacy.business.entity.map`, `sc.legacy.partner.map`, `sc.legacy.project.map`, `sc.legacy.purchase.contract.fact`, `sc.legacy.scbs.material.map`, `sc.material.acceptance`, `sc.material.inbound`, `sc.material.outbound`, `sc.material.purchase.request`, `sc.material.rental.order`, `sc.material.rental.plan`, `sc.material.rental.settlement`, `sc.material.rfq`, `sc.material.settlement`, `sc.office.admin.document`, `sc.output.invoice.adjustment`, `sc.partner.import.review`, `sc.payment.execution`, `sc.plan`, `sc.project.document`, `sc.quality.issue`, `sc.receipt.income`, `sc.safety.disclosure`, `sc.safety.issue`, `sc.safety.patrol.task`, `sc.safety.plan`, `sc.self.funding.registration`, `sc.settlement.adjustment`, `sc.settlement.order`, `sc.subcontract.plan`, `sc.subcontract.price`, `sc.subcontract.register`, `sc.subcontract.request`, `sc.subcontract.settlement`, `sc.tax.deduction.registration`, `sc.treasury.reconciliation`, `sc.workbench.item`, `sc.workflow.instance`, `tender.doc.purchase`, `tender.guarantee`
- Uncovered models with workflow methods:
  - `account.move`: `button_draft`
  - `purchase.order`: `button_confirm`, `button_draft`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
  - `stock.picking`: `action_confirm`, `action_cancel`

## Models

### `account.move`

- Label: Journal Entry
- State fields: `state`
  - `state`: draft=Draft; posted=Posted; cancel=Cancelled
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: `button_draft`
- Header/form buttons:
  - `action_post` 过账 type=object invisible=hide_post_button or move_type != 'entry' states=- groups=account.group_account_invoice
  - `action_post` 确认 type=object invisible=hide_post_button or move_type == 'entry' or display_inactive_currency_warning states=- groups=account.group_account_invoice
  - `action_invoice_sent` 发送和打印 type=object invisible=state != 'posted' or is_being_sent or invoice_pdf_report_id or move_type not in ('out_invoice', 'out_refund') states=- groups=-
  - `action_invoice_sent` 发送和打印 type=object invisible=state != 'posted' or not is_being_sent and not invoice_pdf_report_id or move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund') states=- groups=-
  - `action_register_payment` 登记付款 type=object invisible=state != 'posted' or payment_state not in ('not_paid', 'partial') or move_type not in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt') states=- groups=account.group_account_invoice
  - `preview_invoice` 预览 type=object invisible=move_type not in ('out_invoice', 'out_refund') or state == 'cancel' states=- groups=-
  - `264` 撤销分录 type=action invisible=move_type != 'entry' or state != 'posted' or payment_state == 'reversed' states=- groups=account.group_account_invoice
  - `action_reverse` 退款通知 type=object invisible=move_type not in ('out_invoice', 'in_invoice') or state != 'posted' states=- groups=account.group_account_invoice
  - `button_cancel` 取消分录 type=object invisible=not id or state != 'draft' or move_type != 'entry' states=- groups=account.group_account_invoice
  - `button_cancel` 取消 type=object invisible=not id or state != 'draft' or move_type == 'entry' states=- groups=account.group_account_invoice
  - `button_draft` 重置为草稿 type=object invisible=not show_reset_to_draft_button states=- groups=account.group_account_invoice
  - `button_request_cancel` 要求取消 type=object invisible=state != 'posted' or show_reset_to_draft_button or not need_cancel_request states=- groups=account.group_account_invoice
  - `button_set_checked` 设置为已检查 type=object invisible=not to_check states=- groups=account.group_account_invoice
  - `open_duplicated_ref_bill_view` 这些账单中的一张 type=object invisible=- states=- groups=-
  - `action_activate_currency`  type=object invisible=- states=- groups=-
  - `action_open_business_doc`  type=object invisible=move_type != 'entry' or not id or not payment_id states=- groups=-
  - `open_reconcile_view`  type=object invisible=move_type != 'entry' or not id or not has_reconciled_entries states=- groups=-
  - `open_created_caba_entries`  type=object invisible=not tax_cash_basis_created_move_ids states=- groups=-
  - `action_update_fpos_values` 更新税项和账户 type=object invisible=not show_update_fpos or state in ['cancel', 'posted'] states=- groups=-
  - `action_automatic_entry` Cut-Off type=object invisible=account_internal_group not in ('income', 'expense') states=- groups=-
  - ... 4 more

### `account.move.line`

- Label: Journal Item
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `open_reconcile_view` -> 查看已部分完成对账的分录 type=object invisible=full_reconcile_id or not matched_debit_ids and not matched_credit_ids states=- groups=-

### `construction.contract`

- Label: 项目合同
- State fields: `state`
  - `state`: draft=草稿; confirmed=已生效; running=执行中; closed=已关闭; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_close`, `action_set_running`, `action_reset_draft`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_generate_lines_from_budget` 从中标清单生成 type=object invisible=- states=- groups=-
  - `action_confirm` 提交审批 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_contract_user,smart_construction_core.group_sc_cap_contract_manager
  - `validate_tier` 审批通过 type=object invisible=- states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=- states=- groups=-
  - `action_set_running` 开始执行 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_close` 完成 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_cancel` 作废 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_reset_draft` 重置为草稿 type=object invisible=- states=- groups=-

### `construction.contract.expense`

- Label: 支出合同
- State fields: `state`
  - `state`: <callable>
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_close`, `action_set_running`, `action_reset_draft`, `action_cancel`, `validate_tier`, `reject_tier`
- Header/form buttons:
  - `action_generate_lines_from_budget` 从预算生成 type=object invisible=- states=- groups=-
  - `action_confirm` 提交审批 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_contract_user,smart_construction_core.group_sc_cap_contract_manager
  - `validate_tier` 审批通过 type=object invisible=- states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=- states=- groups=-
  - `action_set_running` 开始执行 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_close` 完成 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_cancel` 作废 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_reset_draft` 重置为草稿 type=object invisible=- states=- groups=-

### `construction.contract.income`

- Label: 收入合同
- State fields: `state`
  - `state`: <callable>
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_close`, `action_set_running`, `action_reset_draft`, `action_cancel`, `validate_tier`, `reject_tier`
- Header/form buttons:
  - `action_generate_lines_from_budget` 从中标清单生成 type=object invisible=- states=- groups=-
  - `action_confirm` 提交审批 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_contract_user,smart_construction_core.group_sc_cap_contract_manager
  - `validate_tier` 审批通过 type=object invisible=- states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=- states=- groups=-
  - `action_set_running` 开始执行 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_close` 完成 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_cancel` 作废 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_reset_draft` 重置为草稿 type=object invisible=- states=- groups=-

### `hr.department`

- Label: 组织架构
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `202`  type=action invisible=- states=- groups=-
  - `action_plan_from_department`  type=object invisible=- states=- groups=-

### `payment.provider`

- Label: Payment Provider
- State fields: `state`
  - `state`: disabled=Disabled; enabled=Enabled; test=Test Mode
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_toggle_is_published`  type=object invisible=not is_published states=- groups=-
  - `action_toggle_is_published`  type=object invisible=is_published states=- groups=-
  - `button_immediate_install` 安装 type=object invisible=module_to_buy states=- groups=-

### `payment.request`

- Label: 付款/收款申请
- State fields: `state`
  - `state`: draft=草稿; submit=提交; approve=审批中; approved=已批准; rejected=已驳回; done=已完成; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_approval_decision`, `action_done`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_submit` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_finance_user
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_approve` 批准 type=object invisible=state != 'submit' or validation_status != 'validated' states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_set_approved` 批准 type=object invisible=state != 'approve' states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_done` 完成 type=object invisible=state not in ['approve', 'approved'] states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_create_payment_execution` 生成付款登记 type=object invisible=type != 'pay' states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_cancel` 取消 type=object invisible=state in ['done', 'cancel'] states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `623` 付款记录 type=action invisible=- states=- groups=smart_construction_core.group_sc_cap_finance_read,smart_construction_core.group_sc_cap_finance_user,smart_construction_core.group_sc_cap_finance_manager
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=not company_contractor_responsibility_summary_id states=- groups=-

### `payment.request.line`

- Label: Payment Request Line
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_attachments` 附件 type=object invisible=- states=- groups=-

### `payment.token`

- Label: Payment Token
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `244` 付款 type=action invisible=- states=- groups=-

### `payment.transaction`

- Label: Payment Transaction
- State fields: `state`
  - `state`: draft=Draft; pending=Pending; authorized=Authorized; done=Confirmed; cancel=Canceled; error=Error
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_capture` 捕捉交易 type=object invisible=state != 'authorized' states=- groups=-
  - `action_void` 无效交易 type=object invisible=state != 'authorized' states=- groups=-
  - `action_view_refunds`  type=object invisible=refunds_count == 0 states=- groups=-
  - `action_view_refunds`  type=- invisible=- states=- groups=-
  - `action_view_invoices`  type=object invisible=invoices_count == 0 states=- groups=-

### `product.category`

- Label: Product Category
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `167`  type=action invisible=- states=- groups=-
  - `395` 上架规则 type=action invisible=- states=- groups=stock.group_stock_multi_locations
  - `437` 位置 type=action invisible=- states=- groups=-

### `product.template`

- Label: Product
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `169`  type=action invisible=product_variant_count <= 1 states=- groups=product.group_product_variant
  - `action_open_attribute_values` 配置 type=object invisible=- states=- groups=product.group_product_variant
  - `action_update_quantity_on_hand` 更新数量 type=object invisible=type != 'product' states=- groups=stock.group_stock_manager
  - `391` 补充 type=action invisible=type not in ['consu', 'product'] states=- groups=stock.group_stock_user
  - `action_update_quantity_on_hand`  type=object invisible=not show_on_hand_qty_status_button states=- groups=-
  - `action_product_tmpl_forecast_report`  type=object invisible=not show_forecasted_qty_status_button states=- groups=-
  - `action_view_stock_move_lines`  type=object invisible=type not in ['product', 'consu'] states=- groups=stock.group_stock_user
  - `action_view_orderpoints`  type=object invisible=type != 'product' or nbr_reordering_rules != 1 states=- groups=-
  - `action_view_orderpoints`  type=object invisible=type != 'product' or nbr_reordering_rules == 1 states=- groups=-
  - `action_open_product_lot`  type=object invisible=tracking == 'none' states=- groups=stock.group_production_lot
  - `action_view_related_putaway_rules`  type=object invisible=type == 'service' states=- groups=stock.group_stock_multi_locations
  - `action_view_storage_category_capacity`  type=object invisible=type == 'service' states=- groups=stock.group_stock_storage_categories
  - `action_open_label_layout` 标签打印 type=object invisible=detailed_type not in ['consu', 'product', 'combo'] states=- groups=-
  - `open_pricelist_rules`  type=object invisible=- states=- groups=product.group_product_pricelist
  - `action_open_documents`  type=object invisible=- states=- groups=-
  - `166` 配置标签 type=action invisible=- states=- groups=-
  - `action_view_po`  type=object invisible=not purchase_ok states=- groups=purchase.group_purchase_user
  - `430` 查看图表 type=action invisible=type not in ['product', 'consu'] states=- groups=-

### `project.budget`

- Label: 项目预算头
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_set_active` 设为当前 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager
  - `action_archive_version` 停用 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager
  - `action_copy_version` 复制并保留分摊 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager
  - `action_copy_version` 复制不带分摊 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager

### `project.funding.baseline`

- Label: Project Funding Baseline
- State fields: `state`
  - `state`: draft=草稿; active=生效; closed=关闭
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `project.material.plan`

- Label: 物资计划
- State fields: `state`
  - `state`: draft=草稿; submit=已提交; approved=已批准; done=已完成; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_done`, `action_reject`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_submit` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_material_user
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `524` 生成询价单 type=action invisible=state != 'approved' states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `action_create_purchase_request` 生成采购申请 type=object invisible=state != 'approved' states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `action_done` 完成 type=object invisible=state != 'approved' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_cancel` 取消 type=object invisible=state in ['done','cancel'] states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_view_purchase_orders`  type=object invisible=- states=- groups=-
  - `action_view_purchase_requests`  type=object invisible=- states=- groups=-
  - `action_view_purchase_lines`  type=object invisible=- states=- groups=-

### `project.milestone`

- Label: Project Milestone
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `350`  type=action invisible=- states=- groups=project.group_project_milestone

### `project.profit.compare`

- Label: 项目经营利润对比
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_actual_revenue_lines` 实际收入 type=object invisible=revenue_actual_amount == 0 states=- groups=-
  - `action_open_budget_revenue_lines` 预算收入 type=object invisible=revenue_budget_amount == 0 states=- groups=-
  - `action_open_actual_cost_ledger` 实际成本 type=object invisible=cost_actual_amount == 0 states=- groups=-
  - `action_open_budget_cost_allocations` 预算成本 type=object invisible=cost_budget_amount == 0 states=- groups=-

### `project.progress.entry`

- Label: 项目进度计量记录
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit_progress`
- Header/form buttons:
  - `action_submit_progress` 提交 type=object invisible=state == 'submitted' states=- groups=-

### `project.project`

- Label: 项目
- State fields: `lifecycle_state`
  - `lifecycle_state`: draft=草稿; in_progress=在建; paused=停工; done=竣工; closing=结算中; warranty=保修期; closed=关闭
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `327` 共享只读 type=action invisible=privacy_visibility != 'portal' states=- groups=project.group_project_manager
  - `327` 分享可编辑的内容 type=action invisible=privacy_visibility != 'portal' states=- groups=project.group_project_manager
  - `action_view_tasks`  type=object invisible=- states=- groups=-
  - `project_update_all_action`  type=object invisible=- states=- groups=project.group_project_user
  - `328`  type=action invisible=privacy_visibility != 'portal' states=- groups=project.group_project_manager
  - `330` 设置阶段的评分邮件模版 type=action invisible=- states=- groups=-
  - `action_open_project_budgets` 预算 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager
  - `action_open_project_contracts` 合同 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_user,smart_construction_core.group_sc_cap_contract_manager
  - `564`  type=action invisible=- states=- groups=smart_construction_core.group_sc_cap_project_user,smart_construction_core.group_sc_cap_project_manager
  - `action_sc_submit` 提交立项 type=object invisible=lifecycle_state != 'draft' states=- groups=-
  - `action_view_tasks` 任务 type=object invisible=- states=- groups=base.group_system,smart_construction_core.group_sc_task_entry_access,smart_construction_core.group_sc_super_admin
  - `project_update_all_action`  type=object invisible=- states=- groups=base.group_system,smart_construction_core.group_sc_task_entry_access,smart_construction_core.group_sc_super_admin
  - `action_open_wbs` 执行结构 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_project_read
  - `action_open_boq_import` 工程量清单 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager
  - `559` 预算/成本 type=action invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager
  - `562` 合同 type=action invisible=- states=- groups=smart_construction_core.group_sc_cap_contract_user,smart_construction_core.group_sc_cap_contract_manager
  - `525` 物资/采购 type=action invisible=- states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `553` 结算/财务 type=action invisible=- states=- groups=smart_construction_core.group_sc_cap_finance_user,smart_construction_core.group_sc_cap_finance_manager
  - `action_open_cost_ledger` 查看台账明细 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager
  - `action_open_progress_entries` 查看进度明细 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_cost_user,smart_construction_core.group_sc_cap_cost_manager
  - ... 16 more

### `project.risk.action`

- Label: 项目风险动作
- State fields: `state`
  - `state`: open=待处理; claimed=已认领; escalated=已升级; closed=已关闭
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_close`

### `project.settlement`

- Label: Project Settlement
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; done=完成; cancel=取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_done`, `action_cancel`

### `project.task`

- Label: Task
- State fields: `state`, `sc_state`
  - `state`: 01_in_progress=In Progress; 02_changes_requested=Changes Requested; 03_approved=Approved; 1_done=Done; 1_canceled=Canceled; 04_waiting_normal=Waiting
  - `sc_state`: draft=草稿; ready=就绪; in_progress=进行中; done=已完成; cancelled=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_ratings`  type=object invisible=rating_count == 0 or not rating_active states=- groups=project.group_project_rating
  - `action_open_parent_task`  type=object invisible=not parent_id states=- groups=-
  - `action_recurring_tasks`  type=object invisible=not active or not recurrence_id states=- groups=project.group_project_recurring_tasks
  - `339`  type=action invisible=not id or subtask_count == 0 states=- groups=-
  - `action_dependent_tasks`  type=object invisible=dependent_tasks_count == 0 states=- groups=project.group_project_task_dependencies
  - `action_project_sharing_view_parent_task`  type=object invisible=not display_parent_task_button states=- groups=-
  - `action_project_sharing_open_subtasks`  type=object invisible=not id or subtask_count == 0 states=- groups=-
  - `action_open_task` 查看任务 type=object invisible=project_id != context.get('active_id') states=- groups=-
  - `action_convert_to_task` 转换为任务 type=object invisible=- states=- groups=-

### `purchase.order`

- Label: Purchase Order
- State fields: `state`
  - `state`: draft=RFQ; sent=RFQ Sent; to approve=To Approve; purchase=Purchase Order; done=Locked; cancel=Cancelled
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: `button_confirm`, `button_draft`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_rfq_send` 通过EMail发送 type=object invisible=state != 'draft' states=- groups=-
  - `print_quotation` 打印询价 type=object invisible=state != 'draft' states=- groups=base.group_user
  - `button_confirm` 确认订单 type=object invisible=state != 'sent' states=- groups=-
  - `button_approve` 批准订单 type=object invisible=state != 'to approve' states=- groups=purchase.group_purchase_manager
  - `action_create_invoice` 创建账单 type=object invisible=state not in ('purchase', 'done') or invoice_status in ('no', 'invoiced') states=- groups=-
  - `action_rfq_send` 重新发送邮件 type=object invisible=state != 'sent' states=- groups=-
  - `print_quotation` 打印询价 type=object invisible=state != 'sent' states=- groups=base.group_user
  - `button_confirm` 确认订单 type=object invisible=state != 'draft' states=- groups=-
  - `action_rfq_send` 通过EMail发送采购单 type=object invisible=state != 'purchase' states=- groups=-
  - `confirm_reminder_mail` 确认收货日期 type=object invisible=state not in ('purchase', 'done') or mail_reminder_confirmed or not date_planned states=- groups=base.group_no_one
  - `action_create_invoice` 创建账单 type=object invisible=state not in ('purchase', 'done') or invoice_status not in ('no', 'invoiced') or not order_line states=- groups=-
  - `button_draft` 设置为草稿 type=object invisible=state != 'cancel' states=- groups=-
  - `button_cancel` 取消 type=object invisible=state not in ('draft', 'to approve', 'sent', 'purchase') states=- groups=-
  - `button_done` 锁定 type=object invisible=state != 'purchase' states=- groups=-
  - `button_unlock` 解锁 type=object invisible=state != 'done' states=- groups=purchase.group_purchase_manager
  - `action_view_invoice`  type=object invisible=invoice_count == 0 or state in ('draft', 'sent', 'to approve') states=- groups=-
  - `action_add_from_catalog` 目录 type=object invisible=- states=- groups=-
  - `action_purchase_history`  type=object invisible=not id states=- groups=-
  - `action_view_picking` 接收产品 type=object invisible=is_shipped or state not in ('purchase', 'done') or incoming_picking_count == 0 states=- groups=stock.group_stock_user
  - `action_view_picking`  type=object invisible=incoming_picking_count == 0 states=- groups=stock.group_stock_user
  - ... 5 more

### `purchase.order.line`

- Label: Purchase Order Line
- State fields: `state`
  - `state`: <callable>
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `purchase.report`

- Label: Purchase Report
- State fields: `state`
  - `state`: draft=Draft RFQ; sent=RFQ Sent; to approve=To Approve; purchase=Purchase Order; done=Done; cancel=Cancelled
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.account.income.expense.summary`

- Label: 账户收支统计表
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_account_master` 查看账户 type=object invisible=- states=- groups=-
  - `action_open_fund_daily_lines` 资金日报明细 type=object invisible=line_count == 0 states=- groups=-
  - `action_open_transaction_lines` 账户收支明细 type=object invisible=income_amount == 0 and expense_amount == 0 and cumulative_receipt_amount == 0 and cumulative_expense_amount == 0 and account_transfer_amount == 0 states=- groups=-

### `sc.approval.scope`

- Label: 审批岗位人员
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_add_user_wizard` 新增人员 type=object invisible=- states=- groups=-

### `sc.ar.ap.company.summary`

- Label: 应收应付报表
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_project_partner_rows` 往来单位明细 type=object invisible=- states=- groups=-
  - `action_open_income_contracts` 收入合同 type=object invisible=- states=- groups=-
  - `action_open_expense_contracts` 支出合同 type=object invisible=- states=- groups=-
  - `action_open_receipts` 收款登记 type=object invisible=- states=- groups=-
  - `action_open_invoices` 发票登记 type=object invisible=- states=- groups=-
  - `action_open_payments` 付款台账 type=object invisible=- states=- groups=-
  - `action_open_finance_facts` 资金事实 type=object invisible=- states=- groups=-

### `sc.ar.ap.project.summary`

- Label: 应收应付报表（项目）
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_income_contracts` 收入合同 type=object invisible=- states=- groups=-
  - `action_open_expense_contracts` 支出合同 type=object invisible=- states=- groups=-
  - `action_open_receipts` 收款登记 type=object invisible=- states=- groups=-
  - `action_open_invoices` 发票登记 type=object invisible=- states=- groups=-
  - `action_open_payments` 付款台账 type=object invisible=- states=- groups=-
  - `action_open_finance_facts` 资金事实 type=object invisible=- states=- groups=-

### `sc.attendance.checkin`

- Label: 考勤记录
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_confirm` 确认考勤 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('confirmed', 'cancel') states=- groups=-

### `sc.business.category`

- Label: Business Category
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_target_records` 查看业务记录 type=object invisible=- states=- groups=-
  - `action_open_bound_entry` 打开绑定入口 type=object invisible=- states=- groups=-

### `sc.business.entity`

- Label: 业务核算主体
- State fields: `mapping_state`
  - `mapping_state`: draft=草稿; candidate=候选; confirmed=已确认; conflict=冲突; archived=归档
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.company.contractor.responsibility.fact`

- Label: 公司-承包人资金责任明细
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_source_record` 打开来源单据 type=object invisible=- states=- groups=-
  - `action_open_finance_fact` 打开收付款事实 type=object invisible=- states=- groups=-

### `sc.company.contractor.responsibility.summary`

- Label: 公司-承包人资金责任余额
- State fields: `responsibility_state`
  - `responsibility_state`: over_processed=到款超处理; open=有待处理余额; self_funding_open=自筹未退; settled=已平衡
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_responsibility_facts` 查看责任明细 type=object invisible=- states=- groups=-

### `sc.company.operation.summary`

- Label: 公司经营情况表
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_deduction_paid` 扣款实缴明细 type=object invisible=deduction_management_fee_amount == 0 and deduction_enterprise_income_tax_amount == 0 and deduction_vat_surcharge_amount == 0 and deduction_vat_surcharge_nonrefundable_amount == 0 states=- groups=-
  - `action_open_company_income` 公司财务收入 type=object invisible=income_amount == 0 states=- groups=-
  - `action_open_reimbursements` 费用报销明细 type=object invisible=reimbursement_amount == 0 states=- groups=-
  - `action_open_payroll_documents` 工资社保来源 type=object invisible=salary_amount == 0 and employee_social_security_amount == 0 and certificate_social_security_amount == 0 states=- groups=-
  - `action_open_deduction_refunds` 扣款退回来源 type=object invisible=deduction_refund_surcharge_amount == 0 states=- groups=-
  - `action_open_company_expenses` 公司财务支出 type=object invisible=expense_amount == 0 states=- groups=-

### `sc.comprehensive.cost.summary`

- Label: 成本统计表（综合）
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_income_contracts` 收入合同 type=object invisible=income_contract_amount == 0 states=- groups=-
  - `action_open_receipts` 收款登记 type=object invisible=receipt_amount == 0 states=- groups=-
  - `action_open_output_invoices` 销项发票 type=object invisible=output_invoice_amount == 0 states=- groups=-
  - `action_open_payable_contracts` 应付合同 type=object invisible=payable_contract_amount == 0 states=- groups=-
  - `action_open_supplier_contracts` 供应商合同 type=object invisible=supplier_contract_amount == 0 states=- groups=-
  - `action_open_material_costs` 材料成本 type=object invisible=material_cost_amount == 0 states=- groups=-
  - `action_open_labor_costs` 劳务分包 type=object invisible=labor_cost_amount == 0 states=- groups=-
  - `action_open_lease_costs` 租赁机械 type=object invisible=lease_cost_amount == 0 states=- groups=-
  - `action_open_expenses` 费用报销 type=object invisible=expense_cost_amount == 0 states=- groups=-
  - `action_open_salary` 工资登记 type=object invisible=salary_cost_amount == 0 states=- groups=-
  - `action_open_input_invoices` 进项发票 type=object invisible=input_invoice_amount == 0 states=- groups=-
  - `action_open_payments` 付款执行 type=object invisible=paid_amount == 0 states=- groups=-

### `sc.construction.diary`

- Label: 施工日志
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; done=已完成; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_done`, `action_cancel`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('cancel', 'legacy_confirmed') states=- groups=-

### `sc.contract.event`

- Label: 合同履约事件
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已审批; rejected=已驳回; done=已完成; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_done`, `action_reject`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 审批通过 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reject` 驳回 type=object invisible=state != 'submitted' states=- groups=-
  - `action_done` 完成 type=object invisible=state != 'approved' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('done', 'cancel') states=- groups=-

### `sc.dashboard.cockpit.fact`

- Label: 驾驶舱业务事实
- State fields: `state`
  - `state`: draft=草稿; in_progress=办理中; done=已完成; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_done`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ['draft', 'in_progress'] states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ['done', 'cancel'] states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state == 'draft' states=- groups=-

### `sc.document.admin.document`

- Label: 资料证照办理单
- State fields: `state`
  - `state`: draft=草稿; in_progress=办理中; done=已完成; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_done`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ['draft', 'in_progress'] states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ['done', 'cancel'] states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state == 'draft' states=- groups=-

### `sc.edition.release.snapshot`

- Label: SC Edition Release Snapshot
- State fields: `state`
  - `state`: candidate=Candidate; approved=Approved; released=Released; superseded=Superseded
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_approve`, `action_release`, `action_supersede`
- Header/form buttons:
  - `action_approve` 审批 type=object invisible=state != 'candidate' states=- groups=-
  - `action_release` 发布 type=object invisible=state not in ('candidate', 'approved') states=- groups=-
  - `action_supersede` 废弃 type=object invisible=state not in ('released', 'approved') states=- groups=-

### `sc.equipment.plan`

- Label: 设备计划
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 确认计划 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('approved', 'cancel') states=- groups=-

### `sc.equipment.price`

- Label: 设备价格库
- State fields: `state`
  - `state`: draft=草稿; active=生效; inactive=停用
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_activate`, `action_deactivate`, `action_reset_draft`
- Header/form buttons:
  - `action_activate` 生效 type=object invisible=state == 'active' states=- groups=-
  - `action_deactivate` 停用 type=object invisible=state != 'active' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state == 'draft' states=- groups=-

### `sc.equipment.request`

- Label: 设备申请
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 确认申请 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('approved', 'cancel') states=- groups=-

### `sc.equipment.settlement`

- Label: 设备结算
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_confirm` 确认结算 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('confirmed', 'cancel') states=- groups=-

### `sc.equipment.usage`

- Label: 设备使用登记
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_confirm` 确认使用 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('confirmed', 'cancel') states=- groups=-

### `sc.expense.claim`

- Label: 费用与保证金单据
- State fields: `state`
  - `state`: draft=草稿; submit=已提交; approved=已批准; done=已完成; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_done`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_submit` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_finance_user
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `action_approve` 批准 type=object invisible=state != 'submit' or validation_status != 'validated' states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_done` 完成 type=object invisible=state != 'approved' states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_cancel` 取消 type=object invisible=state in ['done', 'legacy_confirmed', 'cancel'] states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=not company_contractor_responsibility_summary_id states=- groups=-
  - `action_submit` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_finance_user
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `action_approve` 批准 type=object invisible=state != 'submit' or validation_status != 'validated' states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_done` 完成 type=object invisible=state != 'approved' states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_cancel` 取消 type=object invisible=state in ['done', 'legacy_confirmed', 'cancel'] states=- groups=smart_construction_core.group_sc_cap_finance_manager
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=not company_contractor_responsibility_summary_id states=- groups=-

### `sc.expense.contract.ledger`

- Label: 统一支出合同台账
- State fields: `state`
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_source_record` 打开来源合同 type=object invisible=- states=- groups=-

### `sc.expense.reimbursement.summary`

- Label: 报销统计
- State fields: `state`
  - `state`: draft=草稿; submit=已提交; approved=已批准; done=已完成; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_expense_claims` 查看报销单据 type=object invisible=claim_count == 0 states=- groups=-

### `sc.finance.business.fact`

- Label: 项目收付款来源明细
- State fields: `state`
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_source_record` 打开来源单据 type=object invisible=- states=- groups=-
  - `action_open_business_entry` 进入同类办理 type=object invisible=- states=- groups=-

### `sc.finance.business.project.summary`

- Label: 项目收付款汇总
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_finance_facts` 查看来源明细 type=object invisible=- states=- groups=-
  - `action_open_business_entry` 进入正式办理 type=object invisible=business_domain not in ['deduction_clearing', 'tax_deduction', 'guarantee_deposit'] states=- groups=-

### `sc.finance.counterparty.position.summary`

- Label: 往来对象资金总览
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_project_positions` 查看项目资金往来 type=object invisible=- states=- groups=-
  - `action_open_finance_facts` 查看收付款明细 type=object invisible=- states=- groups=-
  - `action_open_interfund_facts` 查看借还调拨明细 type=object invisible=- states=- groups=-

### `sc.finance.project.capital.position`

- Label: 项目资金总览
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_finance_facts` 查看收付款明细 type=object invisible=- states=- groups=-
  - `action_open_interfund_facts` 查看借还调拨明细 type=object invisible=- states=- groups=-
  - `action_open_project_borrow_company_entry` 项目借公司款 type=object invisible=- states=- groups=-
  - `action_open_project_repay_company_entry` 项目还公司款 type=object invisible=- states=- groups=-
  - `action_open_account_transfer_entry` 账户调拨 type=object invisible=- states=- groups=-
  - `action_open_guarantee_entry` 保证金办理 type=object invisible=- states=- groups=-

### `sc.finance.project.counterparty.position`

- Label: 项目与对象资金往来
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_finance_facts` 查看收付款明细 type=object invisible=- states=- groups=-
  - `action_open_interfund_facts` 查看借还调拨明细 type=object invisible=- states=- groups=-
  - `action_open_company_borrow_entry` 项目借公司款 type=object invisible=counterparty_type != 'company' states=- groups=-
  - `action_open_company_repay_entry` 项目还公司款 type=object invisible=counterparty_type != 'company' states=- groups=-
  - `action_open_contractor_borrow_entry` 承包人借项目款 type=object invisible=counterparty_type != 'partner' states=- groups=-
  - `action_open_contractor_repay_entry` 承包人还项目款 type=object invisible=counterparty_type != 'partner' states=- groups=-
  - `action_open_account_transfer_entry` 账户调拨 type=object invisible=counterparty_type not in ['company', 'project', 'internal'] states=- groups=-

### `sc.financing.loan`

- Label: 融资与借款登记
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; done=已完成; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_done`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=-
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('cancel', 'legacy_confirmed') states=- groups=-

### `sc.fund.account`

- Label: 资金账户
- State fields: `state`
  - `state`: active=启用; inactive=停用
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.fund.account.operation`

- Label: 资金账户操作单
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; done=已完成; cancelled=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_done`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_confirm` 确认 type=object invisible=state != 'draft' states=- groups=-
  - `action_done` 完成 type=object invisible=state != 'confirmed' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('done', 'cancelled') states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state != 'cancelled' states=- groups=-

### `sc.fund.daily.summary`

- Label: 企业资金日报汇总
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_snapshot_facts` 查看企业资金日报 type=object invisible=line_count == 0 states=- groups=-

### `sc.general.contract`

- Label: 综合合同
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; signed=已签署; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' or validation_status in ['waiting', 'pending'] states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_contract_user,smart_construction_core.group_sc_cap_contract_manager
  - `validate_tier` 审批通过 type=object invisible=not can_review states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review states=- groups=-
  - `action_signed` 已签署 type=object invisible=state not in ('draft', 'confirmed') states=- groups=smart_construction_core.group_sc_cap_contract_manager
  - `action_cancel` 取消 type=object invisible=state in ('cancel', 'legacy_confirmed') states=- groups=smart_construction_core.group_sc_cap_contract_manager

### `sc.hazard.source`

- Label: 危险源
- State fields: `state`
  - `state`: draft=草稿; reported=已上报; controlled=已管控; closed=已关闭
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_close`

### `sc.history.todo`

- Label: Historical Workflow Todo
- State fields: `state`
  - `state`: todo=待处理; acknowledged=已确认; resolved=已处理; archived=已归档
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_acknowledge` 确认已读 type=object invisible=state != 'todo' states=- groups=-
  - `action_resolve` 标记处理 type=object invisible=state not in ('todo', 'acknowledged') states=- groups=-
  - `action_archive` 归档 type=object invisible=state == 'archived' states=- groups=-
  - `action_reset_todo` 重新打开 type=object invisible=state == 'todo' states=- groups=smart_construction_core.group_sc_cap_config_admin
  - `action_open_target_record` 打开目标记录 type=object invisible=not target_res_id states=- groups=-
  - `action_open_source_audit` 打开审批审计 type=object invisible=- states=- groups=-

### `sc.hr.payroll.document`

- Label: 人事薪酬办理单
- State fields: `state`
  - `state`: draft=草稿; in_progress=办理中; done=已完成; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_done`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ['draft', 'in_progress'] states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ['done', 'cancel'] states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state == 'draft' states=- groups=-

### `sc.income.contract.ledger`

- Label: 统一收入合同台账
- State fields: `state`
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_source_record` 打开来源合同 type=object invisible=- states=- groups=-

### `sc.interfund.movement.fact`

- Label: 借款还款与调拨明细
- State fields: `state`
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_source_record` 打开来源单据 type=object invisible=- states=- groups=-
  - `action_open_business_entry` 进入同类办理 type=object invisible=- states=- groups=-

### `sc.interfund.movement.project.summary`

- Label: 项目借还调拨汇总
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_interfund_facts` 查看来源明细 type=object invisible=- states=- groups=-
  - `action_open_business_entry` 进入正式办理 type=object invisible=- states=- groups=-

### `sc.invoice.analysis.summary`

- Label: 发票分析报表
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_income_contracts` 收入合同 type=object invisible=- states=- groups=-
  - `action_open_company_invoices` 公司发票 type=object invisible=- states=- groups=-
  - `action_open_individual_invoices` 个体发票 type=object invisible=- states=- groups=-

### `sc.invoice.category.summary`

- Label: 发票分类汇总表
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; registered=已登记; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_invoices` 查看发票登记 type=object invisible=- states=- groups=-

### `sc.invoice.cost.progress.summary`

- Label: 发票成本进度报表
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_progress_receipts` 工程进度收款 type=object invisible=- states=- groups=-
  - `action_open_output_invoices` 销项发票 type=object invisible=- states=- groups=-
  - `action_open_input_invoices` 进项发票 type=object invisible=- states=- groups=-

### `sc.invoice.registration`

- Label: 发票登记
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; registered=已登记; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_register`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=-
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `action_register` 已登记 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('cancel', 'legacy_confirmed') states=- groups=-

### `sc.labor.plan`

- Label: 劳务计划
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 确认计划 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('approved', 'cancel') states=- groups=-

### `sc.labor.price`

- Label: 劳务价格库
- State fields: `state`
  - `state`: draft=草稿; active=生效; inactive=停用
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_activate`, `action_deactivate`, `action_reset_draft`
- Header/form buttons:
  - `action_activate` 生效 type=object invisible=state == 'active' states=- groups=-
  - `action_deactivate` 停用 type=object invisible=state != 'active' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state == 'draft' states=- groups=-

### `sc.labor.request`

- Label: 劳务申请
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 确认申请 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('approved', 'cancel') states=- groups=-

### `sc.labor.settlement`

- Label: 劳务结算
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_confirm` 确认结算 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('confirmed', 'cancel') states=- groups=-

### `sc.labor.settlement.candidate`

- Label: 劳务结算候选
- State fields: `candidate_state`
  - `candidate_state`: ready=可核对; needs_review=需复核
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_usage_lines` 查看用工来源 type=object invisible=- states=- groups=-
  - `action_create_draft_labor_settlement` 生成结算草稿 type=object invisible=candidate_state != 'ready' states=- groups=-

### `sc.labor.usage`

- Label: 劳务用工
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_confirm` 确认用工 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('confirmed', 'cancel') states=- groups=-

### `sc.legacy.business.entity.map`

- Label: 旧库业务核算主体映射
- State fields: `mapping_state`
  - `mapping_state`: candidate=候选; confirmed=已确认; conflict=冲突; ignored=忽略
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_mark_conflict`, `action_ignore`
- Header/form buttons:
  - `action_confirm` 确认映射 type=object invisible=mapping_state == 'confirmed' states=- groups=-
  - `action_mark_conflict` 标记冲突 type=object invisible=mapping_state == 'conflict' states=- groups=-
  - `action_ignore` 忽略 type=object invisible=mapping_state == 'ignored' states=- groups=-

### `sc.legacy.department`

- Label: Legacy Organization Department Fact
- State fields: `state`
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.legacy.equipment.lease.fact`

- Label: 历史设备/租赁事实
- State fields: `state`
  - `state`: legacy_confirmed=历史已确认; cancel=历史作废
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.legacy.income.invoice.fact`

- Label: 历史收入票据事实
- State fields: `state`
  - `state`: legacy_confirmed=历史已确认; cancel=历史作废
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.legacy.labor.subcontract.fact`

- Label: 历史劳务/分包事实
- State fields: `state`
  - `state`: legacy_confirmed=历史已确认; cancel=历史作废
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.legacy.material.detail`

- Label: 物料档案
- State fields: `promotion_state`
  - `promotion_state`: archived=档案; promoted=历史技术关联
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.legacy.material.stock.fact`

- Label: 历史物资库存事实
- State fields: `state`
  - `state`: legacy_confirmed=历史已确认; cancel=历史作废
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.legacy.partner.map`

- Label: 旧库往来单位映射
- State fields: `mapping_state`, `suggested_state`
  - `mapping_state`: candidate=候选; confirmed=已确认; conflict=冲突; ignored=忽略
  - `suggested_state`: fact_partner_candidate=事实往来候选; duplicate_across_carriers=跨主体重复; duplicate_same_carrier_or_empty_tax=同主体/空税号重复; tax_code_conflict=税号冲突
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_mark_conflict`, `action_ignore`
- Header/form buttons:
  - `action_confirm` 确认映射 type=object invisible=mapping_state == 'confirmed' states=- groups=-
  - `action_mark_conflict` 标记冲突 type=object invisible=mapping_state == 'conflict' states=- groups=-
  - `action_ignore` 忽略 type=object invisible=mapping_state == 'ignored' states=- groups=-

### `sc.legacy.project.map`

- Label: 旧库项目映射
- State fields: `mapping_state`, `suggested_state`
  - `mapping_state`: candidate=候选; confirmed=已确认; conflict=冲突; ignored=忽略
  - `suggested_state`: project_candidate=项目候选; single_source_project_candidate=单来源项目候选; not_real_project_review=非真实项目复核; ignored_test_candidate=测试项目忽略
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_mark_conflict`, `action_ignore`
- Header/form buttons:
  - `action_confirm` 确认映射 type=object invisible=mapping_state == 'confirmed' states=- groups=-
  - `action_mark_conflict` 标记冲突 type=object invisible=mapping_state == 'conflict' states=- groups=-
  - `action_ignore` 忽略 type=object invisible=mapping_state == 'ignored' states=- groups=-

### `sc.legacy.purchase.contract.fact`

- Label: 历史采购/一般合同事实
- State fields: `state`
  - `state`: draft=草稿; submit=已提交; approved=已批准; signed=已签署; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`

### `sc.legacy.scbs.material.map`

- Label: SCBS旧库材料映射
- State fields: `mapping_state`
  - `mapping_state`: candidate=候选; confirmed=已确认; create_required=需新建材料档案; conflict=冲突; ignored=忽略
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_mark_conflict`, `action_mark_create_required`, `action_ignore`
- Header/form buttons:
  - `action_confirm` 确认映射 type=object invisible=mapping_state == 'confirmed' states=- groups=-
  - `action_mark_create_required` 标记需新建 type=object invisible=mapping_state == 'create_required' states=- groups=-
  - `action_mark_conflict` 标记冲突 type=object invisible=mapping_state == 'conflict' states=- groups=-
  - `action_ignore` 忽略 type=object invisible=mapping_state == 'ignored' states=- groups=-

### `sc.legacy.self.funding.fact`

- Label: 历史自筹资金事实
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=not company_contractor_responsibility_summary_id states=- groups=-
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=not company_contractor_responsibility_summary_id states=- groups=-

### `sc.legacy.tender.registration.fact`

- Label: 历史投标报名事实
- State fields: `state`
  - `state`: legacy_confirmed=历史已确认; cancel=历史作废
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.legacy.user.role`

- Label: Legacy User Role Assignment Fact
- State fields: `projection_state`
  - `projection_state`: pending=Pending; projected=Projected; unmapped=Unmapped
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.material.acceptance`

- Label: 材料进场验收
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; accepted=验收通过; rejected=验收不通过; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_accept`, `action_reject`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `action_accept` 验收通过 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_reject` 验收不通过 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_reset_draft` 退回草稿 type=object invisible=state not in ('submitted', 'rejected') states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_cancel` 取消 type=object invisible=state in ('accepted', 'cancel') states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_load_purchase_request_lines` 带入申请明细 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `action_load_purchase_order_lines` 带入采购明细 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager

### `sc.material.inbound`

- Label: 材料入库单
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; received=已入库; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_receive`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `action_receive` 确认入库 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_cancel` 取消 type=object invisible=state in ('received', 'cancel') states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_load_acceptance_lines` 带入验收明细 type=object invisible=- states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager

### `sc.material.outbound`

- Label: 材料出库单
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; issued=已出库; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_issue`, `action_reset_draft`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `action_issue` 确认出库 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_cancel` 取消 type=object invisible=state in ('issued', 'cancel') states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_open_transfer_inbound` 查看调入入库 type=object invisible=outbound_type != 'transfer' or not transfer_inbound_id states=- groups=smart_construction_core.group_sc_cap_material_read,smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager

### `sc.material.purchase.request`

- Label: 材料采购申请
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `action_approve` 确认申请 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager,smart_construction_core.group_sc_cap_purchase_manager
  - `action_create_rfq` 生成询价单 type=object invisible=state != 'approved' states=- groups=smart_construction_core.group_sc_cap_purchase_user,smart_construction_core.group_sc_cap_purchase_manager,smart_construction_core.group_sc_cap_material_manager
  - `action_create_purchase_order` 生成采购订单 type=object invisible=state != 'approved' states=- groups=smart_construction_core.group_sc_cap_purchase_manager,smart_construction_core.group_sc_cap_material_manager
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_cancel` 取消 type=object invisible=state in ('approved', 'cancel') states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_view_rfqs`  type=object invisible=- states=- groups=-
  - `action_view_purchase_orders`  type=object invisible=- states=- groups=-

### `sc.material.rental.order`

- Label: 周转材料租赁单
- State fields: `state`
  - `state`: draft=草稿; active=租赁中; returned=已退还; settled=已结算; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_activate`, `action_return`, `action_settle`, `action_cancel`
- Header/form buttons:
  - `action_activate` 确认租赁 type=object invisible=state != 'draft' states=- groups=-
  - `action_return` 确认退还 type=object invisible=state != 'active' states=- groups=-
  - `action_settle` 完成结算 type=object invisible=state != 'returned' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('settled', 'cancel') states=- groups=-

### `sc.material.rental.plan`

- Label: 周转材料租赁计划
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 确认 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('approved', 'cancel') states=- groups=-

### `sc.material.rental.settlement`

- Label: 周转材料租赁结算
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; confirmed=已确认; paid=已支付; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_paid`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_confirm` 确认结算 type=object invisible=state != 'submitted' states=- groups=-
  - `action_paid` 确认支付 type=object invisible=state != 'confirmed' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('paid', 'cancel') states=- groups=-

### `sc.material.rfq`

- Label: 材料询比价
- State fields: `state`
  - `state`: draft=草稿; submitted=已发起; selected=已定价; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_select`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 发起询价 type=object invisible=state != 'draft' states=- groups=smart_construction_core.group_sc_cap_purchase_user,smart_construction_core.group_sc_cap_purchase_manager,smart_construction_core.group_sc_cap_material_manager
  - `action_select` 确定报价 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_purchase_manager,smart_construction_core.group_sc_cap_material_manager
  - `action_create_purchase_order` 生成采购订单 type=object invisible=state == 'cancel' states=- groups=smart_construction_core.group_sc_cap_purchase_manager,smart_construction_core.group_sc_cap_material_manager
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_purchase_manager,smart_construction_core.group_sc_cap_material_manager
  - `action_cancel` 取消 type=object invisible=state in ('selected', 'cancel') states=- groups=smart_construction_core.group_sc_cap_purchase_manager,smart_construction_core.group_sc_cap_material_manager

### `sc.material.settlement`

- Label: 材料结算
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=smart_construction_core.group_sc_cap_material_user,smart_construction_core.group_sc_cap_material_manager
  - `action_confirm` 确认结算 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_create_remaining_payment_request` 生成剩余付款申请 type=object invisible=state != 'confirmed' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_cancel` 取消 type=object invisible=state in ('confirmed', 'cancel') states=- groups=smart_construction_core.group_sc_cap_material_manager
  - `action_open_payment_request`  type=object invisible=payment_request_count == 0 states=- groups=-

### `sc.material.stock.summary`

- Label: 库存统计表（新）
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_stock_in_lines` 入库来源 type=object invisible=in_qty == 0 and in_amount == 0 states=- groups=-
  - `action_open_stock_out_lines` 出库来源 type=object invisible=out_qty == 0 and out_amount == 0 states=- groups=-
  - `action_open_all_stock_lines` 全部明细 type=object invisible=- states=- groups=-

### `sc.office.admin.document`

- Label: 人事行政审批单
- State fields: `state`
  - `state`: draft=草稿; in_progress=办理中; done=已完成; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_done`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ['draft', 'in_progress'] states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ['done', 'cancel'] states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state == 'draft' states=- groups=-

### `sc.output.invoice.adjustment`

- Label: 销项变更登记
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_cancel`
- Header/form buttons:
  - `action_confirm` 确认红冲 type=object invisible=state != 'draft' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state != 'draft' states=- groups=-

### `sc.partner.business.fact.line`

- Label: 客户供应商关联业务明细
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_source_record` 打开来源单据 type=object invisible=- states=- groups=-

### `sc.partner.import.review`

- Label: 客户供应商导入复核
- State fields: `review_state`
  - `review_state`: candidate=待复核; resolved=已处理; ignored=忽略
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_ignore`, `action_resolve_customer`, `action_resolve_supplier`, `action_resolve_customer_supplier`
- Header/form buttons:
  - `action_resolve_customer` 确认为客户 type=object invisible=review_state != 'candidate' states=- groups=-
  - `action_resolve_supplier` 确认为供应商 type=object invisible=review_state != 'candidate' states=- groups=-
  - `action_resolve_customer_supplier` 确认为客户+供应商 type=object invisible=review_state != 'candidate' states=- groups=-
  - `action_ignore` 忽略 type=object invisible=review_state == 'ignored' states=- groups=-

### `sc.payment.execution`

- Label: 付款执行
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; paid=已付款; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_paid`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=-
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `action_paid` 已付款 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 撤销付款 type=object invisible=state != 'paid' states=- groups=-
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=not company_contractor_responsibility_summary_id states=- groups=-

### `sc.plan`

- Label: 计划
- State fields: `state`, `attainment_state`
  - `state`: draft=草稿; confirmed=已确认; in_progress=执行中; done=已完成; cancel=已取消
  - `attainment_state`: not_started=未开始; on_track=正常; due_soon=即将逾期; overdue=已逾期; done=已完成
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_done`, `action_start`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_confirm` 确认 type=object invisible=state != 'draft' states=- groups=-
  - `action_start` 开始执行 type=object invisible=state != 'confirmed' states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ('confirmed', 'in_progress') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('done', 'cancel') states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state == 'draft' states=- groups=-

### `sc.plan.line`

- Label: 计划节点
- State fields: `state`
  - `state`: draft=未开始; in_progress=执行中; done=已完成; blocked=受阻; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.plan.report`

- Label: 计划汇报
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; accepted=已确认; rejected=已退回
- Approval fields: `reject_reason`
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.plan.version`

- Label: 计划版本
- State fields: `state`
  - `state`: draft=草稿; approved=已确认
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.plan.warning.log`

- Label: 计划预警日志
- State fields: `state`
  - `state`: open=未处理; closed=已关闭
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.product.policy`

- Label: SC Product Release Policy
- State fields: `state`
  - `state`: draft=Draft; preview=Preview; stable=Stable; archived=Archived
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_freeze_candidate` 冻结候选快照 type=object invisible=- states=- groups=-

### `sc.project.document`

- Label: 工程资料
- State fields: `state`
  - `state`: draft=草稿; review=审核中; done=已归档; cancel=作废
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_to_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交审批 type=object invisible=- states=- groups=-
  - `action_approve` 归档 type=object invisible=- states=- groups=-
  - `action_cancel` 作废 type=object invisible=- states=- groups=-
  - `action_reset_to_draft` 重置为草稿 type=object invisible=- states=- groups=-

### `sc.project.next_action.rule`

- Label: 项目下一步行动规则
- State fields: `lifecycle_state`
  - `lifecycle_state`: <callable>
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.project.operation.summary`

- Label: 项目经营统计表
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_project` 查看项目 type=object invisible=not project_id states=- groups=-
  - `action_open_source_fact` 旧统计事实 type=object invisible=- states=- groups=-

### `sc.project.stage.requirement.item`

- Label: 项目阶段要求项
- State fields: `lifecycle_state`
  - `lifecycle_state`: draft=草稿; in_progress=在建; paused=停工; done=竣工; closing=结算中; warranty=保修期; closed=关闭
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.project.structure`

- Label: 项目工程结构
- State fields: `state`
  - `state`: draft=草稿; active=生效; archived=归档
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.quality.issue`

- Label: 质量问题
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; rectifying=整改中; rechecking=待复验; closed=已闭环; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_close`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('closed', 'cancel') states=- groups=-

### `sc.receipt.income`

- Label: 收款与收入登记
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; received=已收款; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_received`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=-
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `action_received` 已收款 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('cancel', 'legacy_confirmed') states=- groups=-
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=not company_contractor_responsibility_summary_id states=- groups=-

### `sc.receipt.invoice.line`

- Label: 收款发票明细
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_attachments` 附件 type=object invisible=- states=- groups=-

### `sc.release.action`

- Label: SC Release Action
- State fields: `state`
  - `state`: pending=Pending; running=Running; done=Done; failed=Failed; canceled=Canceled
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.safety.disclosure`

- Label: 安全交底
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`

### `sc.safety.issue`

- Label: 安全问题
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; rectifying=整改中; rechecking=待复验; closed=已闭环; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_close`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-

### `sc.safety.patrol.task`

- Label: 安全巡检任务
- State fields: `state`
  - `state`: draft=草稿; planned=已计划; done=已完成; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_done`, `action_reset_draft`, `action_cancel`

### `sc.safety.plan`

- Label: 安全施工方案
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已审批; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 审批通过 type=object invisible=state != 'submitted' states=- groups=-

### `sc.salary.summary`

- Label: 工资统计表
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_salary_documents` 查看工资登记 type=object invisible=document_count == 0 states=- groups=-

### `sc.scene`

- Label: SC Scene
- State fields: `state`
  - `state`: draft=Draft; published=Published; archived=Archived
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_publish` 发布 type=object invisible=state == 'published' states=- groups=-
  - `action_archive` 归档 type=object invisible=state == 'archived' states=- groups=-

### `sc.scene.snapshot`

- Label: SC Scene Release Snapshot
- State fields: `state`
  - `state`: draft=Draft; stable=Stable; archived=Archived
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.self.funding.registration`

- Label: 自筹垫付/退回办理
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; done=已完成; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_done`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=-
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=- states=- groups=-

### `sc.settlement.adjustment`

- Label: 结算调整
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; cancel=已取消; legacy_confirmed=历史已确认
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_settlement_user
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=smart_construction_core.group_sc_cap_settlement_manager
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=smart_construction_core.group_sc_cap_settlement_manager
  - `action_cancel` 取消 type=object invisible=state != 'confirmed' states=- groups=smart_construction_core.group_sc_cap_settlement_manager

### `sc.settlement.order`

- Label: 结算单
- State fields: `state`
  - `state`: draft=草稿; submit=提交; approve=批准; done=完成; cancel=取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_done`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_submit` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=smart_construction_core.group_sc_cap_business_initiator,smart_construction_core.group_sc_cap_settlement_user
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=smart_construction_core.group_sc_cap_settlement_manager
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=smart_construction_core.group_sc_cap_settlement_manager
  - `action_approve` 批准 type=object invisible=state != 'submit' or validation_status != 'validated' states=- groups=smart_construction_core.group_sc_cap_settlement_manager
  - `action_done` 完成 type=object invisible=state not in ['approve'] states=- groups=smart_construction_core.group_sc_cap_settlement_manager
  - `action_cancel` 取消 type=object invisible=state in ['done','cancel'] states=- groups=smart_construction_core.group_sc_cap_settlement_manager

### `sc.subcontract.plan`

- Label: 分包计划
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 确认计划 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('approved', 'cancel') states=- groups=-

### `sc.subcontract.price`

- Label: 分包价格库
- State fields: `state`
  - `state`: draft=草稿; active=生效; inactive=停用
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_activate`, `action_deactivate`, `action_reset_draft`
- Header/form buttons:
  - `action_activate` 生效 type=object invisible=state != 'draft' states=- groups=-
  - `action_deactivate` 停用 type=object invisible=state != 'active' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'inactive' states=- groups=-

### `sc.subcontract.register`

- Label: 分包登记
- State fields: `state`
  - `state`: draft=草稿; active=已登记; closed=已关闭; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_close`, `action_register`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_register` 确认登记 type=object invisible=state != 'draft' states=- groups=-
  - `action_close` 关闭 type=object invisible=state != 'active' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'active' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('closed', 'cancel') states=- groups=-

### `sc.subcontract.request`

- Label: 分包申请
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; approved=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 确认申请 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('approved', 'cancel') states=- groups=-

### `sc.subcontract.settlement`

- Label: 分包结算
- State fields: `state`
  - `state`: draft=草稿; submitted=已提交; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_confirm` 确认结算 type=object invisible=state != 'submitted' states=- groups=-
  - `action_reset_draft` 退回草稿 type=object invisible=state != 'submitted' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('confirmed', 'cancel') states=- groups=-

### `sc.subscription`

- Label: SC Subscription
- State fields: `state`
  - `state`: trial=Trial; active=Active; paused=Paused; canceled=Canceled
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `sc.tax.deduction.registration`

- Label: 抵扣登记
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; deducted=已抵扣; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_deduct`, `action_cancel`
- Header/form buttons:
  - `action_confirm` 确认 type=object invisible=state != 'draft' states=- groups=-
  - `action_deduct` 已抵扣 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('cancel', 'legacy_confirmed') states=- groups=-
  - `action_view_company_contractor_responsibility_summary` 查看责任余额 type=object invisible=not company_contractor_responsibility_summary_id states=- groups=-

### `sc.tender.guarantee.summary`

- Label: 投标保证金报表
- State fields: -
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_tender_registration` 投标报名来源 type=object invisible=- states=- groups=-
  - `action_open_pay_guarantee` 付保证金 type=object invisible=pay_guarantee_amount == 0 states=- groups=-
  - `action_open_pay_guarantee_refund` 付保证金退回 type=object invisible=pay_guarantee_refund_amount == 0 states=- groups=-
  - `action_open_self_funding` 自筹保证金 type=object invisible=self_funding_amount == 0 states=- groups=-
  - `action_open_self_funding_refund` 自筹保证金退回 type=object invisible=self_funding_refund_amount == 0 states=- groups=-

### `sc.treasury.ledger`

- Label: 资金台账
- State fields: `state`
  - `state`: posted=已入账; void=作废
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_open_payment_request` 打开申请 type=object invisible=not payment_request_id states=- groups=-
  - `action_open_settlement` 打开结算单 type=object invisible=not settlement_id and linked_settlement_count == 0 states=- groups=-

### `sc.treasury.reconciliation`

- Label: 资金对账
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; reconciled=已对账; legacy_confirmed=历史已确认; cancel=已取消
- Approval fields: `validation_status`, `can_review`, `review_ids`, `rejected`, `reject_reason`
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_reconcile`, `action_cancel`, `validate_tier`, `reject_tier`, `action_on_tier_approved`, `action_on_tier_rejected`
- Header/form buttons:
  - `action_confirm` 提交审批 type=object invisible=state != 'draft' or validation_status in ('waiting', 'pending', 'validated') states=- groups=-
  - `validate_tier` 审批通过 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `reject_tier` 审批驳回 type=object invisible=not can_review or validation_status not in ('waiting', 'pending') states=- groups=-
  - `action_reconcile` 对账完成 type=object invisible=state not in ('draft', 'confirmed') states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ('cancel', 'legacy_confirmed') states=- groups=-

### `sc.workbench.item`

- Label: 工作台事项
- State fields: `state`
  - `state`: draft=草稿; in_progress=办理中; done=已完成; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_submit`, `action_done`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_done` 完成 type=object invisible=state not in ['draft', 'in_progress'] states=- groups=-
  - `action_cancel` 取消 type=object invisible=state in ['done', 'cancel'] states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state == 'draft' states=- groups=-

### `sc.workflow.def`

- Label: SC Legacy Workflow Definition
- State fields: `state`
  - `state`: draft=草稿; published=已发布
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_publish` 发布 type=object invisible=state != 'draft' states=- groups=-
  - `action_draft` 回到草稿 type=object invisible=state != 'published' states=- groups=-

### `sc.workflow.instance`

- Label: SC Legacy Workflow Instance
- State fields: `state`
  - `state`: draft=草稿; running=进行中; done=完成; rejected=已驳回; cancelled=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reject`, `action_cancel`
- Header/form buttons:
  - `action_submit` 提交审批 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 审批通过 type=object invisible=state != 'running' states=- groups=-
  - `action_reject` 驳回 type=object invisible=state != 'running' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state not in ['draft','running'] states=- groups=-

### `stock.move`

- Label: Stock Move
- State fields: `state`
  - `state`: draft=New; waiting=Waiting Another Move; confirmed=Waiting Availability; partially_available=Partially Available; assigned=Available; done=Done; cancel=Cancelled
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_get_account_moves` 会计分录 type=object invisible=- states=- groups=account.group_account_readonly

### `stock.picking`

- Label: Transfer
- State fields: `state`
  - `state`: draft=Draft; waiting=Waiting Another Operation; confirmed=Waiting; assigned=Ready; done=Done; cancel=Cancelled
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: `action_confirm`, `action_cancel`
- Header/form buttons:
  - `action_confirm` 标记为待办 type=object invisible=state != 'draft' states=- groups=base.group_user
  - `action_assign` 检查可用量 type=object invisible=not show_check_availability states=- groups=base.group_user
  - `button_validate` 验证 type=object invisible=state in ('draft', 'confirmed', 'done', 'cancel') states=- groups=stock.group_stock_user
  - `button_validate` 验证 type=object invisible=state in ('waiting', 'assigned', 'done', 'cancel') states=- groups=stock.group_stock_user
  - `do_print_picking` 打印 type=object invisible=state != 'assigned' states=- groups=stock.group_stock_user
  - `action_open_label_type` 标签打印 type=object invisible=- states=- groups=-
  - `368` 打印 type=action invisible=state != 'done' states=- groups=base.group_user
  - `386` 退回 type=action invisible=state != 'done' states=- groups=base.group_user
  - `action_cancel` 取消 type=object invisible=state not in ('assigned', 'confirmed', 'draft', 'waiting') states=- groups=base.group_user
  - `action_see_returns`  type=object invisible=return_count == 0 states=- groups=-
  - `action_see_move_scrap` 报废 type=object invisible=not has_scrap_move states=- groups=-
  - `action_see_packages` 包裹 type=object invisible=not has_packages states=- groups=-
  - `364`  type=action invisible=state != 'done' or not has_tracking states=- groups=stock.group_production_lot
  - `action_view_reception_report`  type=object invisible=not show_allocation states=- groups=stock.group_reception_report
  - `action_picking_move_tree`  type=object invisible=(is_locked or state == 'done') or state == 'done' and is_locked states=- groups=base.group_no_one
  - `action_detailed_operations`  type=object invisible=- states=- groups=-
  - `action_assign_serial`  type=object invisible=not display_assign_serial states=- groups=-
  - `action_product_forecast_report`  type=object invisible=quantity == 0 and forecast_availability <= 0 or (parent.picking_type_code == 'outgoing' and state != 'draft') states=- groups=-
  - `action_product_forecast_report`  type=object invisible=quantity > 0 or forecast_availability > 0 or (parent.picking_type_code == 'outgoing' and state != 'draft') states=- groups=-
  - `action_put_in_pack` 放入包裹 type=object invisible=state in ('draft', 'done', 'cancel') states=- groups=stock.group_tracking_lot
  - ... 1 more

### `tender.bid`

- Label: 投标管理
- State fields: `state`
  - `state`: prepare=准备投标; estimating=造价测算; submitted=已提交; waiting=等待开标; won=中标; lost=未中标
- Approval fields: `review_ids`
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -
- Header/form buttons:
  - `action_to_estimating` 进入造价测算 type=object invisible=- states=- groups=-
  - `action_to_submitted` 提交投标 type=object invisible=- states=- groups=-
  - `action_to_waiting` 等待开标 type=object invisible=- states=- groups=-
  - `action_mark_won` 中标 type=object invisible=- states=- groups=-
  - `action_mark_lost` 未中标 type=object invisible=- states=- groups=-
  - `action_to_prepare` 重回准备 type=object invisible=- states=- groups=-
  - `514`  type=action invisible=- states=- groups=-

### `tender.doc.purchase`

- Label: 投标文件购买申请
- State fields: `state`
  - `state`: draft=草稿; submitted=审批中; approved=已通过; rejected=已驳回
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_submit`, `action_approve`, `action_reject`, `action_reset_draft`
- Header/form buttons:
  - `action_submit` 提交 type=object invisible=state != 'draft' states=- groups=-
  - `action_approve` 通过 type=object invisible=state not in ['draft', 'submitted'] states=- groups=-
  - `action_reject` 驳回 type=object invisible=state in ['approved', 'rejected'] states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state == 'draft' states=- groups=-

### `tender.doc.review`

- Label: 投标文件审查
- State fields: `state`
  - `state`: draft=草稿; reviewing=审查中; approved=已通过; rejected=已驳回
- Approval fields: -
- Tier definitions: 0
- Workflow contract: uncovered
- Workflow methods: -

### `tender.guarantee`

- Label: 投标保证金
- State fields: `state`
  - `state`: draft=草稿; confirmed=已确认; cancel=已取消
- Approval fields: -
- Tier definitions: 0
- Workflow contract: covered
- Workflow methods: `action_confirm`, `action_reset_draft`, `action_cancel`
- Header/form buttons:
  - `action_confirm` 确认 type=object invisible=state == 'confirmed' states=- groups=-
  - `action_cancel` 取消 type=object invisible=state == 'cancel' states=- groups=-
  - `action_reset_draft` 重置草稿 type=object invisible=state == 'draft' states=- groups=-

