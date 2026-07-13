# -*- coding: utf-8 -*-
from odoo.addons.smart_core.core.delivery_menu_defaults import register_current_project_scope_model
from odoo.addons.smart_core.core.project_context import (
    register_business_scope_exempt_model,
    register_legacy_direct_acceptance_scope_model,
    register_legacy_project_scope_model,
    register_operation_strategy,
)
from odoo.addons.smart_core.app_config_engine.services.contract_service import (
    register_tautology_permission_guard_group_xmlid,
)
from odoo.addons.smart_core.core.release_navigation_contract_builder import register_legacy_release_navigation_leaf
from odoo.addons.smart_core.core.scene_ready_semantic_orchestration_bridge import register_advisory_handoff_family
from odoo.addons.smart_core.delivery.menu_service import (
    register_customer_acceptance_group_label,
    register_preview_group_anchor_skipped_label,
)
from odoo.addons.smart_core.model.ui_menu_config_policy import register_protected_node_excluded_fingerprint_token
from odoo.addons.smart_core.core.scene_contract_builder import (
    register_legacy_product_title,
    register_route_only_actions,
)
from odoo.addons.smart_core.core.unified_page_contract_v2_assembler import register_kanban_row_action
from odoo.addons.smart_core.handlers.form_field_configuration import register_form_field_label_override
from odoo.addons.smart_core.utils.contract_governance import (
    register_capability_group_profile,
    register_legacy_delete_only_model,
    register_legacy_field_presentation,
    register_legacy_kanban_row_action,
    register_legacy_project_form_governance_model,
    register_legacy_project_form_profile,
    register_legacy_project_kanban_governance_model,
    register_legacy_project_kanban_profile,
    register_legacy_project_task_form_profile,
    register_legacy_project_task_form_governance_model,
    register_legacy_record_context_clear_model,
    register_legacy_standard_list_profile,
    register_scene_semantic_profile,
)
from odoo.addons.smart_core.utils.reason_codes import (
    REASON_PAYMENT_ATTACHMENTS_REQUIRED,
    REASON_PAYMENT_FUNDING_BASELINE_INVALID,
    REASON_PAYMENT_FUNDING_CAP_EXCEEDED,
    REASON_PAYMENT_FUNDING_NOT_READY,
    REASON_PAYMENT_NOT_FULLY_PAID,
    REASON_PAYMENT_SETTLEMENT_NOT_READY,
    register_legacy_business_reason_meta,
)


def apply_core_extension_bootstrap():
    register_current_project_scope_model("project.project")
    register_legacy_project_scope_model("project.project")
    register_operation_strategy("direct")
    register_operation_strategy("joint")
    register_legacy_direct_acceptance_scope_model("sc.legacy.direct.acceptance.fact", direct_strategy="direct")
    for _business_scope_exempt_model in (
        "sc.document.admin.document",
        "sc.hr.payroll.document",
        "sc.legacy.user.profile",
        "res.partner",
    ):
        register_business_scope_exempt_model(_business_scope_exempt_model)
    register_form_field_label_override("project.project", "manager_id", "项目经理")
    for _reason_code, _reason_meta in (
        (
            REASON_PAYMENT_ATTACHMENTS_REQUIRED,
            {
                "retryable": False,
                "error_category": "validation",
                "suggested_action": "upload_attachment",
            },
        ),
        (
            REASON_PAYMENT_SETTLEMENT_NOT_READY,
            {
                "retryable": False,
                "error_category": "business_state",
                "suggested_action": "complete_settlement_approval",
            },
        ),
        (
            REASON_PAYMENT_FUNDING_NOT_READY,
            {
                "retryable": False,
                "error_category": "business_state",
                "suggested_action": "setup_project_funding",
            },
        ),
        (
            REASON_PAYMENT_FUNDING_BASELINE_INVALID,
            {
                "retryable": False,
                "error_category": "business_state",
                "suggested_action": "fix_project_funding_baseline",
            },
        ),
        (
            REASON_PAYMENT_FUNDING_CAP_EXCEEDED,
            {
                "retryable": False,
                "error_category": "business_state",
                "suggested_action": "adjust_payment_amount_or_funding",
            },
        ),
        (
            REASON_PAYMENT_NOT_FULLY_PAID,
            {
                "retryable": False,
                "error_category": "business_state",
                "suggested_action": "complete_payment_execution",
            },
        ),
    ):
        register_legacy_business_reason_meta(_reason_code, _reason_meta)
    for _capability_group_key, _capability_group_profile in (
        (
            "project_management",
            {"label": "项目管理", "icon": "briefcase", "key_prefixes": ["project.", "scene.project", "wbs.", "progress.", "tender."]},
        ),
        (
            "contract_management",
            {"label": "合同管理", "icon": "file-text", "key_prefixes": ["contract.", "settlement."]},
        ),
        (
            "cost_management",
            {"label": "成本管理", "icon": "calculator", "key_prefixes": ["cost.", "budget.", "boq."]},
        ),
        (
            "finance_management",
            {"label": "财务管理", "icon": "wallet", "key_prefixes": ["finance.", "payment.", "treasury."]},
        ),
        (
            "material_management",
            {"label": "资源管理", "icon": "boxes", "key_prefixes": ["material.", "purchase.", "stock."]},
        ),
    ):
        register_capability_group_profile(_capability_group_key, _capability_group_profile)
    for _scene_semantic_profile in (
        {"purpose": "项目推进", "code_prefixes": ["projects."], "code_contains": ["project"]},
        {"purpose": "资金与审批", "code_prefixes": ["finance."], "code_contains": ["payment"]},
        {"purpose": "合同履约", "code_prefixes": ["contracts."], "code_contains": ["contract"]},
    ):
        register_scene_semantic_profile(_scene_semantic_profile)
    _PROJECT_DASHBOARD_ROW_ACTION = {
        "key": "open_project_dashboard",
        "name": "open_project_dashboard",
        "label": "进入项目驾驶舱",
        "intent": "open_scene",
        "target": {
            "route": "/s/project.management",
            "scene_key": "project.management",
            "entry_intent": "project.dashboard.enter",
            "project_id": "${id}",
        },
        "trigger": "row_click",
        "level": "row",
        "target_scope": "row",
    }
    register_kanban_row_action(
        "project.project",
        _PROJECT_DASHBOARD_ROW_ACTION,
    )
    register_legacy_kanban_row_action("project.project", _PROJECT_DASHBOARD_ROW_ACTION)
    register_legacy_record_context_clear_model("project.project")
    register_legacy_delete_only_model("project.task")
    register_legacy_project_form_governance_model("project.project")
    register_legacy_project_form_profile(
        "project.project",
        {
            "primary_fields": [
                "name",
                "project_type_id",
                "project_category_id",
                "lifecycle_state",
                "stage_id",
                "manager_id",
                "user_id",
                "owner_id",
                "company_id",
                "start_date",
                "end_date",
                "contract_no",
                "budget_total",
                "location",
            ],
            "create_hidden_fields": [
                "project_code",
                "code",
                "company_id",
                "analytic_account_id",
                "lifecycle_state",
                "stage_id",
                "last_update_status",
                "privacy_visibility",
                "rating_status",
                "rating_status_period",
            ],
            "action_priorities": ["提交", "进入下一阶段", "创建项目", "保存", "查看任务"],
            "action_noise_markers": ["设置阶段", "评分", "cron", "ir_cron", "演示", "showcase"],
            "search_noise_markers": ["活动", "评分", "status_period"],
            "action_group_labels": {
                "basic": "基础操作",
                "workflow": "流程推进",
                "drilldown": "业务查看",
                "other": "更多操作",
            },
            "max_fields": 25,
        },
    )
    register_legacy_project_kanban_governance_model("project.project")
    register_legacy_project_kanban_profile(
        "project.project",
        {
            "title_field": "name",
            "primary_fields": ["name", "project_code", "manager_id"],
            "secondary_fields": ["stage_id", "lifecycle_state", "end_date", "budget_total"],
            "status_fields": ["lifecycle_state", "stage_id"],
            "max_meta": 4,
        },
    )
    register_legacy_project_task_form_governance_model("project.task")
    for _product_key, _product_title in (
        ("fr1", "FR-1 项目立项"),
        ("fr2", "FR-2 项目推进"),
        ("fr3", "FR-3 成本记录"),
        ("fr4", "FR-4 支付记录"),
        ("fr5", "FR-5 结算结果"),
    ):
        register_legacy_product_title(_product_key, _product_title)
    register_route_only_actions(
        "projects.intake",
        {
            "layout": "entry_cards",
            "primary_actions": [
                {
                    "key": "quick_project_create",
                    "label": "快速创建（推荐）",
                    "target": {"type": "route", "route": "/s/projects.intake?intake_mode=quick", "scene_key": "projects.intake"},
                }
            ],
            "secondary_actions": [
                {
                    "key": "standard_project_intake",
                    "label": "标准立项",
                    "target": {"type": "route", "route": "/s/projects.intake", "scene_key": "projects.intake"},
                }
            ],
        },
    )
    for _release_leaf in (
        {
            "key": "release.fr1.project_intake",
            "label": "FR-1 项目立项",
            "route": "/s/projects.intake",
            "scene_key": "projects.intake",
            "product_key": "fr1",
        },
        {
            "key": "release.fr2.project_flow",
            "label": "FR-2 项目推进",
            "route": "/release/fr2",
            "product_key": "fr2",
            "visible_roles": ("pm", "owner", "executive"),
        },
        {
            "key": "release.fr3.cost_tracking",
            "label": "FR-3 成本记录",
            "route": "/release/fr3",
            "product_key": "fr3",
            "visible_roles": ("pm", "owner", "executive"),
        },
        {
            "key": "release.fr4.payment_tracking",
            "label": "FR-4 支付记录",
            "route": "/release/fr4",
            "product_key": "fr4",
            "visible_roles": ("pm", "owner", "executive"),
        },
        {
            "key": "release.fr5.settlement_summary",
            "label": "FR-5 结算结果",
            "route": "/release/fr5",
            "product_key": "fr5",
            "visible_roles": ("pm", "owner", "executive"),
        },
    ):
        register_legacy_release_navigation_leaf(**_release_leaf)
    for _advisory_handoff_family in ("payment_approval", "payment_entry"):
        register_advisory_handoff_family(_advisory_handoff_family)
    for _config_menu_exclusion_token in ("用户验收", "用户数据验收", "用户核对菜单"):
        register_protected_node_excluded_fingerprint_token(_config_menu_exclusion_token)
    for _acceptance_menu_group_label in ("用户核对菜单", "用户验收"):
        register_customer_acceptance_group_label(_acceptance_menu_group_label)
        register_preview_group_anchor_skipped_label(_acceptance_menu_group_label)
    register_tautology_permission_guard_group_xmlid("project.group_project_manager")
    register_legacy_project_task_form_profile(
        "project.task",
        {
            "fields": [
                "name",
                "project_id",
                "stage_id",
                "sc_state",
                "user_ids",
                "date_deadline",
                "priority",
                "description",
            ],
            "field_labels": {
                "name": "任务名称",
                "project_id": "所属项目",
                "stage_id": "当前阶段",
                "sc_state": "执行状态",
                "user_ids": "执行人",
                "date_deadline": "截止日期",
                "priority": "优先级",
                "description": "执行说明",
            },
            "core_group_label": "任务基础信息",
            "description_group_label": "任务说明",
            "description_fields": ["description"],
        },
    )
    register_legacy_field_presentation(
        "project.project",
        "is_favorite",
        {
            "label": "我的收藏",
            "widget": "boolean_favorite",
            "cell_role": "favorite",
            "mutation": {
                "type": "field_toggle",
                "operation": "record_write",
                "field": "is_favorite",
                "value_type": "boolean",
            },
        },
    )
    register_legacy_standard_list_profile(
        {
            "profile_key": "project.project.list",
            "model_name": "project.project",
            "columns_order": [
                "name",
                "project_code",
                "owner_id",
                "sc_partner_display_name",
                "operation_strategy",
                "lifecycle_state",
                "user_id",
                "contract_amount",
                "dashboard_progress_rate",
                "write_date",
            ],
            "column_labels": {
                "name": "名称",
                "project_code": "项目编号",
                "owner_id": "业主单位",
                "sc_partner_display_name": "关联单位",
                "operation_strategy": "经营方式",
                "lifecycle_state": "项目状态",
                "user_id": "项目负责人",
                "contract_amount": "合同总额",
                "dashboard_progress_rate": "进度(%)",
                "write_date": "更新时间",
            },
            "row_primary": "name",
            "row_secondary": "",
            "status_field": "lifecycle_state",
            "strict_columns": True,
        }
    )
    register_legacy_standard_list_profile(
        {
            "profile_key": "project.task.list",
            "model_name": "project.task",
            "columns_order": [
                "name",
                "project_id",
                "user_ids",
                "stage_id",
                "sc_state",
                "date_deadline",
                "priority",
            ],
            "column_labels": {
                "name": "任务名称",
                "project_id": "所属项目",
                "user_ids": "执行人",
                "stage_id": "当前阶段",
                "sc_state": "执行状态",
                "date_deadline": "截止日期",
                "priority": "优先级",
            },
            "row_primary": "name",
            "row_secondary": "project_id",
            "status_field": "sc_state",
        }
    )


    register_legacy_standard_list_profile({
        "profile_key": "arrival_confirmation.list",
        "model_name": "sc.legacy.fund.confirmation.document",
        "columns_order": [
            "document_state",
            "document_no",
            "receipt_time",
            "project_name",
            "period_no",
            "actual_fund_amount",
            "deducted_amount_total",
            "paid_amount_total",
            "construction_unit_name",
            "contract_amount",
            "current_project_stage",
            "accumulated_invoice_amount",
            "previous_retained_balance",
            "attachment_links",
            "creator_name",
            "created_time",
        ],
        "column_labels": {
            "document_state": "单据状态",
            "document_no": "单据编号",
            "receipt_time": "时间",
            "project_name": "项目名称",
            "period_no": "期数",
            "actual_fund_amount": "本期收款",
            "deducted_amount_total": "本期代扣代缴合计",
            "paid_amount_total": "本期拨付金额合计",
            "construction_unit_name": "施工单位",
            "contract_amount": "合同金额",
            "current_project_stage": "目前形象进度",
            "accumulated_invoice_amount": "累计开票金额",
            "previous_retained_balance": "上期留存余额",
            "attachment_links": "附件",
            "creator_name": "录入人",
            "created_time": "录入时间",
        },
        "row_primary": "document_no",
        "row_secondary": "",
        "status_field": "document_state",
        "strict_columns": True,
    })

    register_legacy_standard_list_profile({
        "profile_key": "payment.request.list",
        "model_name": "payment.request",
        "columns_order": [
            "p1_visible_06fa8c6f628f",
            "p1_visible_8fa8662ad38f",
            "p1_visible_3e7255522b33",
            "p1_visible_2c346345746e",
            "p1_visible_ccfa1326c88f",
            "p1_visible_c00fc55a25b8",
            "p1_visible_9469a2ad32f8",
            "p1_visible_ae1abe750af6",
            "p1_visible_63c5facb9f66",
            "p1_visible_e0361480e3a5",
            "p1_visible_1874b0ce5103",
            "p1_visible_3759fcfc297a",
            "p1_visible_6cf6e39bece9",
            "p1_visible_a103d7cee046",
            "p1_visible_48a64eb40c71",
            "p1_visible_901384917949",
            "p1_visible_71e47f617269",
            "p1_visible_dfc25d77dc39",
        ],
        "column_labels": {
            "p1_visible_06fa8c6f628f": "单据状态",
            "p1_visible_8fa8662ad38f": "单据编号",
            "p1_visible_3e7255522b33": "项目名称",
            "p1_visible_2c346345746e": "申请日期",
            "p1_visible_ccfa1326c88f": "收款单位",
            "p1_visible_c00fc55a25b8": "申请付款金额",
            "p1_visible_9469a2ad32f8": "实际付款金额",
            "p1_visible_ae1abe750af6": "可用余额",
            "p1_visible_63c5facb9f66": "成本分类名称",
            "p1_visible_e0361480e3a5": "备注",
            "p1_visible_1874b0ce5103": "是否关联单据",
            "p1_visible_3759fcfc297a": "付款账号",
            "p1_visible_6cf6e39bece9": "金额大写",
            "p1_visible_a103d7cee046": "户名",
            "p1_visible_48a64eb40c71": "开户行",
            "p1_visible_901384917949": "账号",
            "p1_visible_71e47f617269": "填写人",
            "p1_visible_dfc25d77dc39": "录入时间",
        },
        "row_primary": "name",
        "row_secondary": "project_id",
        "status_field": "state",
    })

    register_legacy_standard_list_profile({
        "profile_key": "tax_deduction_registration.list",
        "model_name": "sc.tax.deduction.registration",
        "columns_order": [
            "p1_visible_06fa8c6f628f",
            "p1_visible_8fa8662ad38f",
            "p1_visible_3540b47897be",
            "p1_visible_3e7255522b33",
            "p1_visible_be5462bd6a62",
            "p1_visible_ada9a85eab00",
            "p1_visible_8acf4918f1f1",
            "p1_visible_ee19dd75350c",
            "p1_visible_eaa05c7105f7",
            "p1_visible_e0361480e3a5",
            "p1_visible_ee6a4d9e2956",
            "p1_visible_1e62803e196c",
        ],
        "column_labels": {
            "p1_visible_06fa8c6f628f": "单据状态",
            "p1_visible_8fa8662ad38f": "单据编号",
            "p1_visible_3540b47897be": "是否转出",
            "p1_visible_3e7255522b33": "项目名称",
            "p1_visible_be5462bd6a62": "开票单位",
            "p1_visible_ada9a85eab00": "发票号",
            "p1_visible_8acf4918f1f1": "抵扣税额",
            "p1_visible_ee19dd75350c": "抵扣总额",
            "p1_visible_eaa05c7105f7": "抵扣附加税",
            "p1_visible_e0361480e3a5": "备注",
            "p1_visible_ee6a4d9e2956": "录入人",
            "p1_visible_1e62803e196c": "单据日期",
        },
        "row_primary": "document_no",
        "row_secondary": "project_id",
        "status_field": "state",
    })

    register_legacy_standard_list_profile({
        "profile_key": "project.material.plan.list",
        "model_name": "project.material.plan",
        "columns_order": ["name", "project_id", "date_plan", "state"],
        "column_labels": {
            "name": "单号",
            "project_id": "项目",
            "date_plan": "需用日期",
            "state": "状态",
        },
        "row_primary": "name",
        "row_secondary": "project_id",
        "status_field": "state",
    })

    register_legacy_standard_list_profile({
        "profile_key": "tax_certificate_registration.list",
        "model_name": "sc.legacy.payment.residual.fact",
        "signature_any": ["tax_certificate_registration", "外经证登记"],
        "columns_order": [
            "document_state_label",
            "document_no",
            "project_name",
            "taxpayer_name",
            "taxpayer_identifier",
            "handler_phone",
            "regional_tax_contact",
            "regional_tax_contact_phone",
            "operation_address",
            "payment_method",
            "contract_name",
            "planned_amount",
            "contract_start_date",
            "contract_end_date",
            "partner_name",
            "counterparty_tax_identifier",
            "tax_report_management_no",
            "attachment_links",
            "creator_name",
            "created_time",
        ],
        "column_labels": {
            "document_state_label": "单据状态",
            "document_no": "单据编号",
            "project_name": "项目名称",
            "taxpayer_name": "纳税人名称",
            "taxpayer_identifier": "纳税人识别号",
            "handler_phone": "经办人联系电话",
            "regional_tax_contact": "区域所属税所联系人",
            "regional_tax_contact_phone": "区域所属税所联系人手机",
            "operation_address": "跨区域经营地址",
            "payment_method": "经营方式",
            "contract_name": "合同名称",
            "planned_amount": "合同金额",
            "contract_start_date": "合同开始日期",
            "contract_end_date": "合同结束日期",
            "partner_name": "合同相对方名称",
            "counterparty_tax_identifier": "合同相对方纳税人识别号",
            "tax_report_management_no": "跨区域涉税事项报验管理编号",
            "attachment_links": "附件",
            "creator_name": "录入人",
            "created_time": "录入时间",
        },
        "row_primary": "document_no",
        "row_secondary": "",
        "status_field": "document_state_label",
        "strict_columns": True,
    })
