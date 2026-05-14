# 表单结构标准化静态审计

## 结论摘要

- 扫描 XML form 视图：322
- 完整 form：180
- 继承片段：142
- 可直接标准化：25
- 需契约层生成默认页签：104
- 需补语义标注：43
- 需补 XML 主结构：8

本审计只读扫描声明式 XML，不连接数据库，不合并运行态继承视图。继承片段需要下一阶段通过 Odoo registry 合并后的 `fields_view_get/get_view` 再做运行态确认。

## 分类分布

| classification | views |
| --- | --- |
| inherit_fragment | 142 |
| contract_auto_with_default_tabs | 104 |
| needs_semantic_annotation | 43 |
| auto_standardizable | 25 |
| needs_xml_structure | 8 |

## 模块分布

| module | views |
| --- | --- |
| smart_construction_core | 310 |
| smart_core | 5 |
| sc_norm_engine | 4 |
| smart_construction_scene | 2 |
| smart_construction_demo | 1 |

## 可作为标准化输入的样本

| model | xmlid | score | features |
| --- | --- | --- | --- |
| construction.contract.expense | view_construction_contract_expense_form | 14 | statusbar,notebook |
| construction.contract | view_construction_contract_form | 14 | statusbar,notebook |
| construction.contract.income | view_construction_contract_income_form | 14 | statusbar,notebook |
| sc.document.admin.document | view_sc_document_admin_document_form | 14 | statusbar,notebook |
| sc.fund.account | view_sc_fund_account_form | 14 | statusbar,notebook |
| sc.fund.account.operation | view_sc_fund_account_operation_form | 14 | statusbar,notebook |
| sc.general.contract | view_sc_general_contract_form | 14 | statusbar,notebook |
| sc.hr.payroll.document | view_sc_hr_payroll_document_form | 14 | statusbar,notebook |
| sc.material.acceptance | view_sc_material_acceptance_form | 14 | statusbar,notebook |
| sc.material.inbound | view_sc_material_inbound_form | 14 | statusbar,notebook |
| sc.material.outbound | view_sc_material_outbound_form | 14 | statusbar,notebook |
| sc.material.purchase.request | view_sc_material_purchase_request_form | 14 | statusbar,notebook |
| sc.material.rfq | view_sc_material_rfq_form | 14 | statusbar,notebook |
| sc.material.settlement | view_sc_material_settlement_form | 14 | statusbar,notebook |
| sc.office.admin.document | view_sc_office_admin_document_form | 14 | statusbar,notebook |
| sc.partner.import.review | view_sc_partner_import_review_form | 14 | statusbar,notebook |
| sc.settlement.order | view_sc_settlement_order_form | 14 | statusbar,notebook |
| project.boq.line | view_project_boq_line_form | 13 | notebook |
| project.budget | view_project_budget_form | 13 | notebook |
| sc.approval.policy | view_sc_approval_policy_form | 13 | notebook |

## 优先处理缺口样本

| model | xmlid | score | classification | gaps |
| --- | --- | --- | --- | --- |
| sc.norm.import.wizard | view_sc_norm_import_wizard | 5 | needs_xml_structure | missing_sheet;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| material.plan.to.rfq.wizard | view_material_plan_to_rfq_wizard | 5 | needs_xml_structure | missing_sheet;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.boq.import.wizard | view_project_boq_import_wizard | 5 | needs_xml_structure | missing_sheet;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.project | view_project_overview_form | 5 | needs_xml_structure | missing_group;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.quick.create.wizard | view_project_quick_create_wizard_form | 5 | needs_xml_structure | missing_sheet;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.task.from.boq.wizard | view_project_task_from_boq_wizard | 5 | needs_xml_structure | missing_sheet;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.approval.scope.user.wizard | view_sc_approval_scope_user_wizard_form | 5 | needs_xml_structure | missing_sheet;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.scene.governance.wizard | view_sc_scene_governance_wizard_form | 5 | needs_xml_structure | missing_sheet;missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.norm.chapter | view_sc_norm_chapter_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| payment.ledger | view_payment_ledger_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.budget.cost.alloc | view_project_budget_cost_alloc_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.cost.code | view_project_cost_code_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.cost.ledger | view_project_cost_ledger_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.funding.baseline | view_project_funding_baseline_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| project.progress.entry | view_project_progress_entry_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| quota.import.wizard | view_quota_import_wizard_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.capability | view_sc_capability_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.check.standard.item | view_sc_check_standard_item_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.dictionary | view_sc_dictionary_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.legacy.expense.deposit.fact | view_sc_legacy_expense_deposit_fact_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.legacy.finance.auxiliary.fact | view_sc_legacy_finance_auxiliary_fact_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.legacy.financing.loan.fact | view_sc_legacy_financing_loan_fact_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.legacy.invoice.tax.fact | view_sc_legacy_invoice_tax_fact_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.legacy.receipt.income.fact | view_sc_legacy_receipt_income_fact_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.legacy.workflow.audit | view_sc_legacy_workflow_audit_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.legacy.workflow.detail.fact | view_sc_legacy_workflow_detail_fact_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.pack.installation | view_sc_pack_installation_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.pack.registry | view_sc_pack_registry_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.project.stage.requirement.item | view_sc_project_stage_requirement_item_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.project.stage.requirement.wizard | view_sc_project_stage_requirement_wizard | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.risk.item | view_sc_risk_item_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.risk.library | view_sc_risk_library_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.safety.patrol.task | view_sc_safety_patrol_task_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.scene.version | view_sc_scene_version_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.workflow.node | view_sc_workflow_node_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| tender.opening | view_tender_opening_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.scene.governance.log | view_sc_scene_governance_log_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.entitlement | view_sc_entitlement_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.ops.job | view_sc_ops_job_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |
| sc.subscription | view_sc_subscription_form | 7 | contract_auto_with_default_tabs | missing_labelled_group;missing_notebook;missing_page;missing_labelled_page;missing_statusbar;missing_button_box;missing_chatter |

## 判定口径

- `auto_standardizable`：已有 `sheet/group/notebook/page`，并带有足够标题或锚点，可直接进入项目式契约标准化。
- `contract_auto_with_default_tabs`：已有主信息区，但缺少 notebook/page，可由契约层生成“主信息/明细/来源追溯/备注”等默认页签。
- `needs_semantic_annotation`：结构基本存在，但缺少标题或 `data-sc-anchor`，建议补少量语义标注。
- `needs_xml_structure`：缺少 `sheet` 或 `group`，契约层难以稳定判断主信息结构，建议先补 XML 主骨架。
- `inherit_fragment`：静态 XML 只是继承补丁，需运行态合并后确认。
