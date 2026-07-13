# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List

from odoo import fields
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
from odoo.addons.smart_construction_core.core_extension_contract_projection import (
    smart_core_finalize_unified_page_contract_v2,
    smart_core_normalize_projected_contract_data,
    smart_core_normalize_unified_page_contract_v2,
)
from odoo.addons.smart_construction_core.core_extension_capabilities import (
    build_capability_contribution_item,
)
from odoo.addons.smart_construction_core.core_extension_form_actions import (
    build_payment_form_business_action_contract,
)
from odoo.addons.smart_construction_core.core_extension_intents import (
    get_intent_handler_contributions,
)
from odoo.addons.smart_construction_core.core_extension_system_init import (
    apply_system_init_profile_overrides,
)
from odoo.addons.smart_construction_core.core_extension_navigation_policy import (
    smart_core_business_config_admin_group_xmlids,
    smart_core_business_config_form_settings_refs,
    smart_core_business_config_approval_policy_refs,
    smart_core_native_config_root_menu_xmlid,
    smart_core_native_config_delivery_excluded_menu_xmlids,
    smart_core_lowcode_system_config_menu_xmlids,
    smart_core_lowcode_config_recovery_parent_menu_xmlids,
    smart_core_business_root_menu_xmlid,
    smart_core_relation_entry_policy,
    smart_core_model_specific_form_contract_policy,
    smart_core_form_field_aliases,
    smart_core_menu_delivery_token_policy,
    smart_core_business_nav_group_display_order,
    smart_core_product_policy_catalog_source,
    smart_core_product_policy_catalog_base_keys,
    smart_core_default_product_policy_specs,
    smart_core_product_policy_catalog_label,
    smart_core_platform_legacy_ownership_module,
    smart_core_resolve_release_actor_role_codes,
    smart_core_resolve_usage_actor_role_codes,
    smart_core_default_release_snapshot_role_code,
    smart_core_industry_extension_module_names,
    smart_core_app_shell_contract,
    smart_core_scene_entry_orchestrator_specs,
    smart_core_user_data_acceptance_nav_contract,
)
from odoo.addons.smart_construction_core.core_extension_workspace_facts import (
    _build_enterprise_enablement_contract,
    _build_home_block_contract_rows,
    _build_payment_action_rows,
    _build_project_action_rows,
    _build_risk_action_rows,
    _build_role_entry_contract_rows,
    _build_task_action_rows,
)
from odoo.addons.smart_construction_core.core_extension_services import (
    smart_core_scene_package_service_class,
    smart_core_scene_governance_service_class,
    smart_core_describe_project_capabilities,
    smart_core_build_portal_dashboard,
    smart_core_build_capability_matrix,
    smart_core_get_project_insight,
    smart_core_build_portal_execute_button_contract,
    smart_core_build_project_execution_service,
    smart_core_build_project_dashboard_service,
    smart_core_build_project_plan_bootstrap_service,
    smart_core_build_cost_tracking_service,
    smart_core_build_payment_slice_service,
    smart_core_build_settlement_slice_service,
)
from odoo.addons.smart_construction_core.core_extension_projected_contracts import (
    smart_core_finalize_projected_contract_data,
)
from odoo.addons.smart_construction_core.core_extension_policy_catalog import (
    API_DATA_MUTATION_POLICIES,
    API_DATA_WRITE_ALLOWLIST,
    DRAFT_DELETE_ALLOWED_STATES,
    FILE_ATTACHMENT_ALLOWED_LEGACY_MODEL_PREFIXES,
    FILE_ATTACHMENT_ALLOWED_MODEL_EXACT,
    FILE_ATTACHMENT_ALLOWED_MODEL_PREFIXES,
    FILE_ATTACHMENT_EXCLUDED_MODEL_PREFIXES,
    FILE_DOWNLOAD_ALLOWED_MODELS,
    FILE_UPLOAD_ALLOWED_MODELS,
    CRITICAL_SCENE_TARGET_OVERRIDES,
    CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES,
    INDUSTRY_CREATE_FIELD_FALLBACKS,
    LEGACY_VISIBLE_BUSINESS_COLUMN_LABELS_BY_MODEL,
    MODEL_CODE_MAPPING,
    NAV_ACTION_SCENE_MAP,
    NAV_MENU_SCENE_MAP,
    NAV_MODEL_VIEW_SCENE_MAP,
    ROLE_GROUPS_CAPABILITY_FALLBACK,
    ROLE_GROUPS_EXPLICIT,
    ROLE_PRECEDENCE,
    ROLE_SURFACE_OVERRIDES,
    SERVER_ACTION_WINDOW_MAP,
)

_logger = logging.getLogger(__name__)

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

def _state_unlink_policy(
    model_name: str,
    business_label: str,
    allowed_states=DRAFT_DELETE_ALLOWED_STATES,
    state_field: str = "state",
):
    return {
        "allowed": True,
        "delete_mode": "unlink",
        "policy_kind": "state_limited_business_document",
        "state_field": state_field,
        "allowed_states": list(allowed_states),
        "reason_code": "DRAFT_BUSINESS_DOCUMENT_DELETE_ALLOWED",
        "message": f"允许删除未形成业务事实的{business_label}；仅限草稿/取消等未提交状态，并继续受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    }


API_DATA_DRAFT_UNLINK_POLICIES = {
    "construction.contract": _state_unlink_policy("construction.contract", "合同记录"),
    "construction.contract.income": _state_unlink_policy("construction.contract.income", "收入合同"),
    "construction.contract.expense": _state_unlink_policy("construction.contract.expense", "支出合同"),
    "payment.request": _state_unlink_policy("payment.request", "付款申请"),
    "sc.general.contract": _state_unlink_policy("sc.general.contract", "综合合同"),
    "sc.expense.claim": _state_unlink_policy("sc.expense.claim", "费用与保证金单据"),
    "sc.financing.loan": _state_unlink_policy("sc.financing.loan", "融资借款单据"),
    "sc.invoice.registration": _state_unlink_policy("sc.invoice.registration", "发票登记单据"),
    "sc.payment.execution": _state_unlink_policy("sc.payment.execution", "付款执行单"),
    "sc.receipt.income": _state_unlink_policy("sc.receipt.income", "收款收入登记"),
    "sc.fund.account.operation": _state_unlink_policy("sc.fund.account.operation", "资金账户操作单"),
    "sc.self.funding.registration": _state_unlink_policy("sc.self.funding.registration", "自筹资金登记"),
    "sc.tax.deduction.registration": _state_unlink_policy("sc.tax.deduction.registration", "税票抵扣登记"),
    "sc.settlement.order": _state_unlink_policy("sc.settlement.order", "结算单"),
    "sc.settlement.adjustment": _state_unlink_policy("sc.settlement.adjustment", "结算调整单"),
    "project.material.plan": _state_unlink_policy("project.material.plan", "材料计划"),
    "sc.material.purchase.request": _state_unlink_policy("sc.material.purchase.request", "材料采购申请"),
    "sc.material.acceptance": _state_unlink_policy("sc.material.acceptance", "材料验收单"),
    "sc.material.inbound": _state_unlink_policy("sc.material.inbound", "材料入库单"),
    "sc.material.outbound": _state_unlink_policy("sc.material.outbound", "材料出库单"),
    "sc.material.rfq": _state_unlink_policy("sc.material.rfq", "材料询比价"),
    "sc.material.settlement": _state_unlink_policy("sc.material.settlement", "材料结算单"),
    "sc.material.rental.plan": _state_unlink_policy("sc.material.rental.plan", "材料租赁计划"),
    "sc.material.rental.order": _state_unlink_policy("sc.material.rental.order", "材料租赁订单"),
    "sc.material.rental.settlement": _state_unlink_policy("sc.material.rental.settlement", "材料租赁结算"),
    "sc.labor.plan": _state_unlink_policy("sc.labor.plan", "劳务计划"),
    "sc.labor.request": _state_unlink_policy("sc.labor.request", "劳务申请"),
    "sc.labor.usage": _state_unlink_policy("sc.labor.usage", "劳务使用记录"),
    "sc.labor.settlement": _state_unlink_policy("sc.labor.settlement", "劳务结算"),
    "sc.labor.price": _state_unlink_policy("sc.labor.price", "劳务价格单"),
    "sc.equipment.plan": _state_unlink_policy("sc.equipment.plan", "设备计划"),
    "sc.equipment.request": _state_unlink_policy("sc.equipment.request", "设备申请"),
    "sc.equipment.usage": _state_unlink_policy("sc.equipment.usage", "设备使用记录"),
    "sc.equipment.settlement": _state_unlink_policy("sc.equipment.settlement", "设备结算"),
    "sc.equipment.price": _state_unlink_policy("sc.equipment.price", "设备价格单"),
    "sc.safety.plan": _state_unlink_policy("sc.safety.plan", "安全方案"),
    "sc.safety.disclosure": _state_unlink_policy("sc.safety.disclosure", "安全交底"),
    "sc.safety.issue": _state_unlink_policy("sc.safety.issue", "安全问题"),
    "sc.safety.patrol.task": _state_unlink_policy("sc.safety.patrol.task", "安全巡检任务"),
    "sc.quality.issue": _state_unlink_policy("sc.quality.issue", "质量问题"),
    "sc.quality.rectification": _state_unlink_policy(
        "sc.quality.rectification",
        "质量整改记录",
        ("submitted", "rectifying", "rechecking", "cancel"),
        state_field="issue_state",
    ),
    "sc.quality.recheck": _state_unlink_policy(
        "sc.quality.recheck",
        "质量复验记录",
        ("rectifying", "rechecking", "cancel"),
        state_field="issue_state",
    ),
    "sc.safety.rectification": _state_unlink_policy(
        "sc.safety.rectification",
        "安全整改记录",
        ("submitted", "rectifying", "rechecking", "cancel"),
        state_field="issue_state",
    ),
    "sc.safety.recheck": _state_unlink_policy(
        "sc.safety.recheck",
        "安全复验记录",
        ("rectifying", "rechecking", "cancel"),
        state_field="issue_state",
    ),
    "sc.construction.diary": _state_unlink_policy("sc.construction.diary", "施工日志"),
    "project.progress.entry": _state_unlink_policy("project.progress.entry", "进度填报"),
    "project.risk.action": _state_unlink_policy("project.risk.action", "风险措施"),
    "sc.plan": _state_unlink_policy("sc.plan", "项目计划"),
    "sc.plan.line": _state_unlink_policy("sc.plan.line", "项目计划明细"),
    "sc.plan.version": _state_unlink_policy("sc.plan.version", "计划版本"),
    "sc.plan.report": _state_unlink_policy("sc.plan.report", "计划上报"),
    "tender.bid": _state_unlink_policy("tender.bid", "投标主单", ("prepare", "estimating")),
    "tender.doc.purchase": _state_unlink_policy("tender.doc.purchase", "投标文件购买申请"),
    "tender.doc.review": _state_unlink_policy("tender.doc.review", "投标文件审查"),
    "tender.guarantee": _state_unlink_policy("tender.guarantee", "投标保证金"),
}
API_DATA_UNLINK_POLICIES = {
    "construction.contract": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理合同记录；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "construction.contract.income": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理收入合同记录；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "construction.contract.expense": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理支出合同记录；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "hr.department": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理组织部门；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "payment.request": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理付款申请；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "payment.request.line": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理付款申请明细；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "project.cost.code": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理成本科目；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "project.dictionary": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理业务字典；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "project.task": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许删除任务记录；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "project.tags": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "RELATION_MAINTENANCE_DELETE_ALLOWED",
        "message": "允许删除项目标签等关系维护数据；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "res.partner": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理客户/供应商资料；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "sc.approval.policy": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理审批策略；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "sc.approval.step": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理审批步骤；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "sc.document.admin.document": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理行政档案；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "sc.hr.payroll.document": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理薪酬档案；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "sc.office.admin.document": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理办公行政资料；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "sc.project.stage.requirement.item": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理阶段要求；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
    "sc.supplier.type": {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "DELETE_POLICY_ALLOWED",
        "message": "允许业务配置管理员整理供应商类型；仍受模型 ACL 与记录规则约束。",
        "source": "smart_construction_core",
    },
}
API_DATA_UNLINK_POLICIES.update(API_DATA_DRAFT_UNLINK_POLICIES)
API_DATA_UNLINK_ALLOWED_MODELS = list(API_DATA_UNLINK_POLICIES)

def smart_core_identity_profile(env):
    return {
        "role_surface_map": ROLE_SURFACE_OVERRIDES,
        "role_groups_explicit": ROLE_GROUPS_EXPLICIT,
        "role_groups_capability_fallback": ROLE_GROUPS_CAPABILITY_FALLBACK,
        "role_precedence": ROLE_PRECEDENCE,
    }


def smart_core_nav_scene_maps(env):
    return {
        "menu_scene_map": dict(NAV_MENU_SCENE_MAP),
        "action_xmlid_scene_map": dict(NAV_ACTION_SCENE_MAP),
        "model_view_scene_map": dict(NAV_MODEL_VIEW_SCENE_MAP),
    }


def smart_core_surface_aliases(env):
    del env
    return {
        "construction_pm_v1": "workspace_default_v1",
    }


def smart_core_runtime_business_config_productization_sources(env):
    del env
    return [
        "smart_construction_custom.user_menu_preference",
    ]


def smart_core_resolve_record_context_config(env, params):
    del env, params
    return {
        "model": "project.project",
        "label": "当前项目",
        "placeholder": "搜索项目名称",
        "selected_id_param": "selected_id",
    }


def smart_core_critical_scene_target_overrides(env):
    return set(CRITICAL_SCENE_TARGET_OVERRIDES)


def smart_core_critical_scene_target_route_overrides(env):
    return dict(CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES)


def get_server_action_window_map_contributions(env):
    return dict(SERVER_ACTION_WINDOW_MAP)


def get_file_upload_allowed_model_contributions(env):
    return sorted(set(FILE_UPLOAD_ALLOWED_MODELS) | _business_attachment_allowed_models(env))


def get_file_download_allowed_model_contributions(env):
    return sorted(set(FILE_DOWNLOAD_ALLOWED_MODELS) | _business_attachment_allowed_models(env))


def _business_attachment_allowed_models(env):
    out = set()
    try:
        models = env["ir.model"].sudo().search([])
    except Exception:
        return out
    for row in models:
        model_name = str(row.model or "").strip()
        if not model_name:
            continue
        legacy_attachment_model = model_name.startswith(FILE_ATTACHMENT_ALLOWED_LEGACY_MODEL_PREFIXES)
        if (
            model_name not in FILE_ATTACHMENT_ALLOWED_MODEL_EXACT
            and not legacy_attachment_model
            and model_name.startswith(FILE_ATTACHMENT_EXCLUDED_MODEL_PREFIXES)
        ):
            continue
        if (
            model_name not in FILE_ATTACHMENT_ALLOWED_MODEL_EXACT
            and not legacy_attachment_model
            and not model_name.startswith(FILE_ATTACHMENT_ALLOWED_MODEL_PREFIXES)
        ):
            continue
        if model_name not in env:
            continue
        try:
            if getattr(env[model_name], "_transient", False) or getattr(env[model_name], "_abstract", False):
                continue
        except Exception:
            continue
        out.add(model_name)
    return out


def get_api_data_write_allowlist_contributions(env):
    return {
        str(model_name): list(field_names)
        for model_name, field_names in API_DATA_WRITE_ALLOWLIST.items()
    }


def get_api_data_mutation_policy_contribution(env, model_name: str, op: str):
    policy = API_DATA_MUTATION_POLICIES.get(str(model_name or "").strip())
    if not isinstance(policy, dict):
        return {"allowed": True, "reason_code": "OK", "source": "smart_construction_core"}
    allowed_ops = {
        str(item or "").strip().lower()
        for item in (policy.get("allowed_ops") or [])
        if str(item or "").strip()
    }
    normalized_op = str(op or "").strip().lower()
    if allowed_ops and normalized_op not in allowed_ops:
        return {"allowed": True, "reason_code": "OK", "source": "smart_construction_core"}
    out = dict(policy)
    out["op"] = normalized_op
    out["model"] = str(model_name or "").strip()
    return out


def _is_contract_tax_rate_quick_create(env, vals: dict) -> bool:
    safe_vals = vals if isinstance(vals, dict) else {}
    if (
        safe_vals.get("type_tax_use") == "none"
        and safe_vals.get("amount_type") == "percent"
        and safe_vals.get("price_include") is False
        and safe_vals.get("tax_group_id")
    ):
        try:
            group = env["account.tax.group"].sudo().browse(int(safe_vals.get("tax_group_id") or 0)).exists()
        except Exception:
            group = env["account.tax.group"].browse()
        if group and group.name == "合同税率":
            return True
    return False


def get_intent_permission_model_acl_policy_contribution(env, intent_name: str, model_name: str, access_mode: str, params: dict):
    if (
        str(intent_name or "").strip() == "api.data"
        and str(model_name or "").strip() == "account.tax"
        and str(access_mode or "").strip() == "create"
    ):
        raw_params = params if isinstance(params, dict) else {}
        payload = raw_params.get("params") if isinstance(raw_params.get("params"), dict) else raw_params
        if isinstance(raw_params.get("payload"), dict):
            payload = raw_params.get("payload")
        vals = payload.get("vals") or payload.get("values") if isinstance(payload, dict) else {}
        if _is_contract_tax_rate_quick_create(env, vals if isinstance(vals, dict) else {}):
            return {
                "skip_model_acl": True,
                "reason_code": "CONTRACT_TAX_RATE_QUICK_CREATE",
                "source": "smart_construction_core",
            }
    return {"skip_model_acl": False, "source": "smart_construction_core"}


def get_api_data_create_execution_policy_contribution(env, model_name: str, vals: dict, ctx: dict, params: dict):
    model = str(model_name or "").strip()
    safe_vals = vals if isinstance(vals, dict) else {}
    if model != "account.tax":
        return {"sudo": False, "source": "smart_construction_core"}
    if _is_contract_tax_rate_quick_create(env, safe_vals):
        return {
            "allowed": True,
            "sudo": True,
            "reason_code": "CONTRACT_TAX_RATE_QUICK_CREATE",
            "source": "smart_construction_core",
        }
    return {
        "allowed": False,
        "sudo": False,
        "reason_code": "ACCOUNT_TAX_NATIVE_CREATE_FORBIDDEN",
        "message": "税率只能通过合同税率百分比快建，不能维护原生会计税种。",
        "source": "smart_construction_core",
    }


def get_api_data_unlink_allowed_model_contributions(env):
    policies = {
        str(model_name): dict(policy)
        for model_name, policy in API_DATA_UNLINK_POLICIES.items()
    }
    policies["project.project"] = {
        "allowed": True,
        "delete_mode": "unlink",
        "reason_code": "PROJECT_MASTER_DELETE_ALLOWED",
        "message": "允许删除无业务依赖的项目主数据；继续受模型 ACL、记录规则与项目依赖阻断约束。",
        "source": "smart_construction_core",
        "dependency_guard": "project.project._raise_project_unlink_blockers",
    }
    return policies


def get_model_code_mapping_contributions(env):
    return dict(MODEL_CODE_MAPPING)


def smart_core_register(registry):
    """Compatibility loader for smart_core.core.extension_loader."""
    if not isinstance(registry, dict):
        return
    try:
        from odoo.addons.smart_construction_core.handlers.project_dashboard import (
            ProjectDashboardHandler,
        )

        registry["project.dashboard"] = ProjectDashboardHandler
    except Exception as exc:
        _logger.warning("[smart_core_register] skip project.dashboard explicit registration: %s", exc)
    for item in get_intent_handler_contributions():
        if not isinstance(item, dict):
            continue
        intent_name = str(item.get("intent") or "").strip()
        handler = item.get("handler")
        if intent_name and handler is not None:
            registry[intent_name] = handler


def get_capability_contributions(env, user):
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import (
            list_capabilities_for_user as registry_list_capabilities_for_user,
        )
    except Exception:
        return []
    try:
        capabilities = registry_list_capabilities_for_user(env, user)
    except Exception:
        return []
    if not isinstance(capabilities, list) or not capabilities:
        return []

    out = []
    for row in capabilities:
        item = build_capability_contribution_item(row)
        if item:
            out.append(item)
    return out


def get_capability_contributions_with_timings(env, user):
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import (
            list_capabilities_for_user_with_timings as registry_list_capabilities_for_user_with_timings,
        )
    except Exception:
        return [], {}
    try:
        capabilities, timings_ms = registry_list_capabilities_for_user_with_timings(env, user)
    except Exception:
        return [], {}
    if not isinstance(capabilities, list) or not capabilities:
        return [], timings_ms if isinstance(timings_ms, dict) else {}

    out = []
    for row in capabilities:
        item = build_capability_contribution_item(row)
        if item:
            out.append(item)
    return out, timings_ms if isinstance(timings_ms, dict) else {}


def get_capability_group_contributions(env):
    del env
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import CAPABILITY_GROUPS
    except Exception:
        return []
    out = []
    for item in CAPABILITY_GROUPS:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("source_module", "smart_construction_core")
        out.append(row)
    return out


def smart_core_list_capabilities_for_user(env, user):
    """Compatibility hook consumed by smart_core capability provider."""
    return get_capability_contributions(env, user)


def smart_core_capability_groups(env):
    """Compatibility hook consumed by smart_core capability provider."""
    return get_capability_group_contributions(env)


def get_create_field_fallback_contributions(env, model_name):
    del env
    return dict(INDUSTRY_CREATE_FIELD_FALLBACKS.get(str(model_name or ""), {}))


def smart_core_create_field_fallbacks(env, model_name):
    """Compatibility hook consumed by smart_core api.data handlers."""
    return get_create_field_fallback_contributions(env, model_name)


def smart_core_form_business_actions(env, model_name, record_id, contract):
    """Return model-level business action semantics for form contracts."""
    del contract
    model = str(model_name or "").strip()
    if model != "payment.request":
        return None
    try:
        record = env[model].browse(int(record_id or 0)).exists()
    except Exception:
        record = None
    if not record:
        return None
    try:
        from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
            PaymentRequestAvailableActionsHandler,
        )

        result = PaymentRequestAvailableActionsHandler(env, payload={"id": int(record.id)}).run(
            payload={"id": int(record.id)}
        )
    except Exception:
        return None

    data = result.get("data") if isinstance(result, dict) else {}
    return build_payment_form_business_action_contract(data)


def get_system_init_fact_contributions(env, user, context=None):
    """Return construction system.init facts contribution payload."""
    del context
    try:
        module_facts = {}

        task_rows = _build_task_action_rows(env, user)
        payment_rows = _build_payment_action_rows(env)
        risk_rows = _build_risk_action_rows(env)
        project_rows = _build_project_action_rows(env, user)

        module_facts["workspace_collections"] = {
            "task_items": task_rows,
            "payment_requests": payment_rows,
            "risk_actions": risk_rows,
            "project_actions": project_rows,
        }
        module_facts["workspace_collection_export_keys"] = [
            "task_items",
            "payment_requests",
            "risk_actions",
            "project_actions",
        ]

        module_facts["workspace_business_source"] = {
            "task_items": len(task_rows),
            "payment_requests": len(payment_rows),
            "risk_actions": len(risk_rows),
            "project_actions": len(project_rows),
        }

        role_entries = _build_role_entry_contract_rows(env)
        if role_entries:
            module_facts["role_entries"] = role_entries

        home_blocks = _build_home_block_contract_rows(env)
        if home_blocks:
            module_facts["home_blocks"] = home_blocks

        enterprise_enablement = _build_enterprise_enablement_contract(env, user)
        if enterprise_enablement:
            module_facts["enterprise_enablement"] = enterprise_enablement

        return {
            "module": "smart_construction_core",
            "facts": module_facts,
            "collections": module_facts.get("workspace_collections") or {},
            "meta": {
                "source": "smart_construction_core",
                "status": "active",
            },
        }
    except Exception as exc:
        _logger.warning("[get_system_init_fact_contributions] failed: %s", exc)
        return None


def smart_core_extend_system_init(data, env, user):
    """Compatibility hook: write construction facts only under data['ext_facts']."""
    if not isinstance(data, dict):
        return data

    contribution = get_system_init_fact_contributions(env, user)
    ext_facts = data.get("ext_facts")
    if not isinstance(ext_facts, dict):
        ext_facts = {}
    if isinstance(contribution, dict):
        module_key = str(contribution.get("module") or "smart_construction_core").strip() or "smart_construction_core"
        facts_payload = contribution.get("facts") if isinstance(contribution.get("facts"), dict) else {}
        ext_facts[module_key] = dict(facts_payload)
    data["ext_facts"] = ext_facts
    return apply_system_init_profile_overrides(data, ext_facts)


def smart_core_server_action_window_map(env):
    return get_server_action_window_map_contributions(env)


def smart_core_file_upload_allowed_models(env):
    return get_file_upload_allowed_model_contributions(env)


def smart_core_file_download_allowed_models(env):
    return get_file_download_allowed_model_contributions(env)


def smart_core_file_download_auth_subject(env, attachment, current_subject):
    del current_subject
    try:
        if "payment.request" not in env:
            return None
        parent_request = env["payment.request"].sudo().search(
            [("attachment_ids", "in", attachment.id)],
            limit=1,
        )
    except Exception:
        return None
    if not parent_request:
        return None
    return {"model": "payment.request", "res_id": parent_request.id}


def smart_core_legacy_visible_business_column_labels(env):
    del env
    return LEGACY_VISIBLE_BUSINESS_COLUMN_LABELS_BY_MODEL


def smart_core_api_data_write_allowlist(env):
    return get_api_data_write_allowlist_contributions(env)


def smart_core_api_data_mutation_policy(env, model_name: str, op: str):
    return get_api_data_mutation_policy_contribution(env, model_name, op)


def smart_core_intent_permission_model_acl_policy(env, intent_name: str, model_name: str, access_mode: str, params: dict):
    return get_intent_permission_model_acl_policy_contribution(env, intent_name, model_name, access_mode, params)


def smart_core_api_data_create_execution_policy(env, model_name: str, vals: dict, ctx: dict, params: dict):
    return get_api_data_create_execution_policy_contribution(env, model_name, vals, ctx, params)


def smart_core_api_data_unlink_allowed_models(env):
    return get_api_data_unlink_allowed_model_contributions(env)


def smart_core_api_data_search_fields(env, model_name: str):
    try:
        from .models.support.p1_daily_business_visible_alias_fields import (
            LABEL_SOURCE_OVERRIDES,
            MODEL_LABEL_SOURCE_OVERRIDES,
            P1_ALIAS_COMPAT_LABELS,
            P1_ALIAS_LABELS,
        )
        from .models.support.user_confirmed_formal_visible_fields import USER_CONFIRMED_FORMAL_VISIBLE_FIELDS
    except Exception:
        return []

    model_name = str(model_name or "").strip()
    labels = []
    for label in list(P1_ALIAS_LABELS.get(model_name) or []) + list(P1_ALIAS_COMPAT_LABELS.get(model_name) or []):
        value = str(label or "").strip()
        if value and value not in labels:
            labels.append(value)
    for entry in USER_CONFIRMED_FORMAL_VISIBLE_FIELDS.get(model_name) or []:
        label = str((entry or {}).get("label") or "").strip()
        if label and label not in labels:
            labels.append(label)
    model_overrides = MODEL_LABEL_SOURCE_OVERRIDES.get(model_name) or {}
    for label in model_overrides:
        value = str(label or "").strip()
        if value and value not in labels:
            labels.append(value)
    names = []
    for label in labels:
        for field_name in list(model_overrides.get(label) or []) + list(LABEL_SOURCE_OVERRIDES.get(label) or []):
            value = str(field_name or "").strip()
            if value and value not in names:
                names.append(value)
    if env is None:
        return names
    try:
        model_fields = getattr(env[model_name], "_fields", {}) or {}
    except Exception:
        return names
    return [field_name for field_name in names if field_name in model_fields]


def smart_core_model_code_mapping(env):
    return get_model_code_mapping_contributions(env)
