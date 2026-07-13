# -*- coding: utf-8 -*-
import logging

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
from odoo.addons.smart_construction_core.core_extension_api_policy import (
    get_api_data_create_execution_policy_contribution,
    get_api_data_mutation_policy_contribution,
    get_api_data_unlink_allowed_model_contributions,
    get_api_data_write_allowlist_contributions,
    get_file_download_allowed_model_contributions,
    get_file_upload_allowed_model_contributions,
    get_intent_permission_model_acl_policy_contribution,
    get_model_code_mapping_contributions,
    get_server_action_window_map_contributions,
    smart_core_api_data_create_execution_policy,
    smart_core_api_data_mutation_policy,
    smart_core_api_data_search_fields,
    smart_core_api_data_unlink_allowed_models,
    smart_core_api_data_write_allowlist,
    smart_core_file_download_allowed_models,
    smart_core_file_download_auth_subject,
    smart_core_file_upload_allowed_models,
    smart_core_intent_permission_model_acl_policy,
    smart_core_legacy_visible_business_column_labels,
    smart_core_model_code_mapping,
    smart_core_server_action_window_map,
)
from odoo.addons.smart_construction_core.core_extension_policy_catalog import (
    CRITICAL_SCENE_TARGET_OVERRIDES,
    CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES,
    INDUSTRY_CREATE_FIELD_FALLBACKS,
    NAV_ACTION_SCENE_MAP,
    NAV_MENU_SCENE_MAP,
    NAV_MODEL_VIEW_SCENE_MAP,
    ROLE_GROUPS_CAPABILITY_FALLBACK,
    ROLE_GROUPS_EXPLICIT,
    ROLE_PRECEDENCE,
    ROLE_SURFACE_OVERRIDES,
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
