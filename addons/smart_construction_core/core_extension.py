# -*- coding: utf-8 -*-
import logging
from copy import deepcopy
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
    USER_CONFIRMED_FORMAL_LIST_ACTION_XMLIDS,
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


def _sc_text(value) -> str:
    return str(value or "").strip()


def _sc_field_code(node: dict) -> str:
    return _sc_text(node.get("fieldCode") or node.get("name") or node.get("field"))


def _sc_set_project_label(node: dict, field_name: str, label: str) -> None:
    code = _sc_field_code(node)
    if code != field_name:
        return
    node["label"] = label
    node["string"] = label
    field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
    field_info["label"] = label
    field_info["string"] = label
    node["fieldInfo"] = field_info
    if isinstance(node.get("field_info"), dict):
        node["field_info"]["label"] = label
        node["field_info"]["string"] = label
    component_config = node.get("componentConfig") if isinstance(node.get("componentConfig"), dict) else {}
    relation_entry = component_config.get("relationEntry") if isinstance(component_config.get("relationEntry"), dict) else {}
    ui_labels = relation_entry.get("ui_labels") if isinstance(relation_entry.get("ui_labels"), dict) else {}
    if ui_labels:
        ui_labels["dialog_title"] = "%s：搜索更多" % label
        relation_entry["ui_labels"] = ui_labels
        component_config["relationEntry"] = relation_entry
        node["componentConfig"] = component_config


def _sc_prune_and_label_project_nodes(value):
    if isinstance(value, list):
        out = []
        for item in value:
            pruned = _sc_prune_and_label_project_nodes(item)
            if pruned is not None:
                out.append(pruned)
        return out
    if not isinstance(value, dict):
        return value
    if _sc_field_code(value) == "user_id" or _sc_text(value.get("widgetId")) == "field.user_id":
        return None
    node = dict(value)
    for field_name, label in {
        "partner_id": "业主单位",
        "owner_id": "业主单位",
        "manager_id": "项目经理",
        "responsibility_ids": "项目责任分工",
        "collaborator_ids": "项目协作成员",
    }.items():
        _sc_set_project_label(node, field_name, label)
    for key in ("children", "tabs", "pages", "nodes", "items", "widgetList"):
        if isinstance(node.get(key), list):
            node[key] = _sc_prune_and_label_project_nodes(node[key])
    return node


def _sc_project_field_widget(field_name: str, label: str, field_type: str, *, relation: str = "") -> dict:
    config = {"fieldType": field_type}
    if relation:
        config["relation"] = relation
    return {
        "widgetId": "field.%s" % field_name,
        "widgetType": "table" if field_type in {"one2many", "many2many"} else "select",
        "fieldCode": field_name,
        "label": label,
        "span": 12,
        "componentKey": "sc.table.data" if field_type in {"one2many", "many2many"} else "sc.select.remote",
        "capabilities": [],
        "componentConfig": config,
    }


def _sc_project_field_node(field_name: str, label: str, field_type: str, *, relation: str = "") -> dict:
    widget = _sc_project_field_widget(field_name, label, field_type, relation=relation)
    return {
        "type": "field",
        "name": field_name,
        "string": label,
        "label": label,
        "fieldInfo": {
            "name": field_name,
            "label": label,
            "string": label,
            "type": field_type,
            "relation": relation,
            "widget": widget["widgetType"],
        },
        "field_info": {
            "name": field_name,
            "label": label,
            "string": label,
            "type": field_type,
            "relation": relation,
            "widget": widget["widgetType"],
        },
        "widget": widget["widgetType"],
        "componentKey": widget["componentKey"],
        "componentConfig": deepcopy(widget["componentConfig"]),
        "widgetId": widget["widgetId"],
    }


def _sc_node_has_field(value, field_name: str) -> bool:
    if isinstance(value, list):
        return any(_sc_node_has_field(item, field_name) for item in value)
    if not isinstance(value, dict):
        return False
    if _sc_field_code(value) == field_name:
        return True
    return any(_sc_node_has_field(value.get(key), field_name) for key in ("children", "tabs", "pages", "nodes", "items", "widgetList"))


def _sc_append_project_responsibility_group(contract: dict, *, include_collaborators: bool) -> None:
    layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
    if not tree:
        return
    children = []
    if not _sc_node_has_field(tree, "responsibility_ids"):
        children.append(_sc_project_field_node("responsibility_ids", "项目责任分工", "one2many", relation="project.responsibility"))
    if include_collaborators and not _sc_node_has_field(tree, "collaborator_ids"):
        children.append(_sc_project_field_node("collaborator_ids", "项目协作成员", "many2many", relation="res.users"))
    if not children:
        return
    group = {
        "type": "group",
        "name": "sc_project_responsibility_collaboration",
        "containerId": "sc_project_responsibility_collaboration",
        "containerType": "group",
        "string": "项目责任与协作",
        "label": "项目责任与协作",
        "children": children,
        "widgetList": [
            _sc_project_field_widget("responsibility_ids", "项目责任分工", "one2many", relation="project.responsibility"),
            *(
                [_sc_project_field_widget("collaborator_ids", "项目协作成员", "many2many", relation="res.users")]
                if include_collaborators else []
            ),
        ],
    }
    target = tree[0] if isinstance(tree[0], dict) else None
    if target is None:
        return
    if isinstance(target.get("children"), list):
        target["children"].append(group)
    else:
        tree.append(group)
    layout["containerTree"] = tree
    registry = layout.get("componentRegistry") if isinstance(layout.get("componentRegistry"), dict) else {}
    registry["sc.table.data"] = {"componentKey": "sc.table.data"}
    layout["componentRegistry"] = registry
    contract["layoutContract"] = layout
    status = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    widget_status = [row for row in status.get("widgetStatus", []) if isinstance(row, dict) and _sc_text(row.get("widgetId")) != "field.user_id"]
    field_names = ["responsibility_ids"]
    if include_collaborators:
        field_names.append("collaborator_ids")
    for field_name in field_names:
        widget_id = "field.%s" % field_name
        if not any(_sc_text(row.get("widgetId")) == widget_id for row in widget_status):
            widget_status.append({"widgetId": widget_id, "visible": True, "readonly": False, "required": False, "disabled": False, "auth": "edit"})
    status["widgetStatus"] = widget_status
    contract["statusContract"] = status


def smart_core_finalize_unified_page_contract_v2(env, contract, context):
    if not isinstance(contract, dict):
        return None
    context = context if isinstance(context, dict) else {}
    source = context.get("source_contract") if isinstance(context.get("source_contract"), dict) else {}
    head = source.get("head") if isinstance(source.get("head"), dict) else {}
    model = _sc_text(source.get("model") or head.get("model"))
    view_type = _sc_text(source.get("view_type") or head.get("view_type") or (context or {}).get("view_type")).lower()
    render_profile = _sc_text(source.get("render_profile") or head.get("render_profile") or (((context or {}).get("meta") or {}).get("params") or {}).get("render_profile")).lower()
    out = deepcopy(contract)
    _sc_inject_workflow_contract(env, out, source, model=model, view_type=view_type)
    _sc_normalize_construction_diary_form(out, source, model=model, view_type=view_type)
    if model != "project.project" or view_type != "form":
        return out if out != contract else None
    layout = out.get("layoutContract") if isinstance(out.get("layoutContract"), dict) else {}
    tree = layout.get("containerTree") if isinstance(layout.get("containerTree"), list) else []
    layout["containerTree"] = _sc_prune_and_label_project_nodes(tree)
    out["layoutContract"] = layout
    status = out.get("statusContract") if isinstance(out.get("statusContract"), dict) else {}
    if isinstance(status.get("widgetStatus"), list):
        status["widgetStatus"] = [
            row for row in status["widgetStatus"]
            if not (isinstance(row, dict) and _sc_text(row.get("widgetId")) == "field.user_id")
        ]
        out["statusContract"] = status
    _sc_append_project_responsibility_group(out, include_collaborators=render_profile != "create")
    return out


def smart_core_normalize_projected_contract_data(env, data, context):
    del env, context
    if not isinstance(data, dict):
        return None
    out = deepcopy(data)
    _sc_general_contract_tax_contract(out)
    return out if out != data else None


def smart_core_normalize_unified_page_contract_v2(env, contract, context):
    del env
    if not isinstance(contract, dict):
        return None
    source = (context or {}).get("source_contract") if isinstance(context, dict) else {}
    source = source if isinstance(source, dict) else {}
    out = deepcopy(contract)
    _sc_general_contract_tax_contract(out, source_contract=source)
    _sc_normalize_general_contract_company_form(out, source_contract=source)
    return out if out != contract else None


def _sc_field_name(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    return _sc_text(node.get("name") or node.get("field") or node.get("fieldCode"))


def _sc_collect_field_nodes(nodes: Any, existing: dict[str, dict[str, Any]]) -> None:
    if isinstance(nodes, list):
        for item in nodes:
            _sc_collect_field_nodes(item, existing)
        return
    if not isinstance(nodes, dict):
        return
    if _sc_text(nodes.get("type")) == "field":
        name = _sc_field_name(nodes)
        if name and name not in existing:
            existing[name] = deepcopy(nodes)
    for key in ("children", "widgetList", "pages", "tabs", "nodes", "items", "containerTree"):
        _sc_collect_field_nodes(nodes.get(key), existing)


def _sc_set_v2_container_tree(contract: dict[str, Any], container_tree: list[Any]) -> None:
    layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    layout["containerTree"] = container_tree
    contract["layoutContract"] = layout
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    runtime["containerTree"] = container_tree
    contract["runtimeContract"] = runtime


def _sc_set_v2_widget_status(contract: dict[str, Any], widget_status: list[dict[str, Any]]) -> None:
    status = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    status["widgetStatus"] = widget_status
    contract["statusContract"] = status
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    runtime["widgetStatus"] = widget_status
    contract["runtimeContract"] = runtime


def _sc_set_v2_governance_patch(contract: dict[str, Any], key: str, patch: dict[str, Any]) -> None:
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    patches = runtime.get("governancePatches") if isinstance(runtime.get("governancePatches"), dict) else {}
    patches[key] = patch
    runtime["governancePatches"] = patches
    contract["runtimeContract"] = runtime
    meta = contract.get("meta") if isinstance(contract.get("meta"), dict) else {}
    meta_patches = meta.get("governance_patches") if isinstance(meta.get("governance_patches"), dict) else {}
    meta_patches[key] = patch
    meta["governance_patches"] = meta_patches
    contract["meta"] = meta


def _sc_normalize_construction_diary_form(contract: dict[str, Any], source_contract: dict[str, Any], *, model: str, view_type: str) -> None:
    if model != "sc.construction.diary" or view_type != "form":
        return
    groups: list[tuple[str, list[str]]] = [
        ("项目与日志", ["project_id", "date_diary", "diary_type", "title"]),
        ("现场情况", ["weather", "construction_unit", "project_manager", "manpower_count", "attendance_equipment"]),
        ("施工内容", ["description", "material_inspection_note", "hidden_acceptance_note", "next_plan"]),
        ("质量安全", ["quality_name", "safety_note", "test_block_note", "design_change_note"]),
        ("办理信息", ["handler_name", "note"]),
    ]
    ordered_fields = [name for _title, names in groups for name in names]
    labels = {
        "date_diary": "日志日期",
        "diary_type": "日志类型",
        "title": "日志标题",
        "description": "今日施工内容",
        "material_inspection_note": "材料进场/送检",
        "hidden_acceptance_note": "隐蔽工程验收",
        "next_plan": "下步计划",
        "quality_name": "质量事项",
        "safety_note": "安全情况",
        "test_block_note": "试块制作",
        "design_change_note": "设计变更/技术核定",
        "handler_name": "经办人",
    }
    required = {"project_id", "date_diary", "diary_type"}
    readonly = {"name", "document_no", "source_origin", "state"}
    field_map = source_contract.get("fields") if isinstance(source_contract.get("fields"), dict) else {}
    layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    existing: dict[str, dict[str, Any]] = {}
    _sc_collect_field_nodes(layout_contract.get("containerTree"), existing)

    def descriptor(name: str) -> dict[str, Any]:
        raw = field_map.get(name) if isinstance(field_map.get(name), dict) else {}
        label = labels.get(name) or raw.get("string") or raw.get("label") or name
        return {
            "name": name,
            "label": label,
            "string": label,
            "type": raw.get("type") or raw.get("ttype") or "char",
            "required": name in required,
            "readonly": name in readonly or bool(raw.get("readonly")),
            "domain": raw.get("domain") if isinstance(raw.get("domain"), list) else [],
            "context": raw.get("context") if isinstance(raw.get("context"), dict) else {},
            **({"relation": raw.get("relation")} if raw.get("relation") else {}),
            **({"selection": raw.get("selection")} if isinstance(raw.get("selection"), list) else {}),
        }

    def normalize_node(name: str) -> dict[str, Any]:
        node = deepcopy(existing.get(name) or {"type": "field", "name": name, "children": [], "widgetList": []})
        info = descriptor(name)
        label = _sc_text(info.get("label")) or name
        node.update({"type": "field", "name": name, "string": label, "label": label, "widgetId": f"field.{name}"})
        node["fieldInfo"] = {**(node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}), **info}
        node["field_info"] = {**(node.get("field_info") if isinstance(node.get("field_info"), dict) else {}), **info}
        config = node.get("componentConfig") if isinstance(node.get("componentConfig"), dict) else {}
        config.update({"fieldType": info.get("type"), "required": name in required, "readonly": bool(info.get("readonly"))})
        if info.get("selection"):
            config["selection"] = info.get("selection")
        if info.get("relation"):
            config["relation"] = info.get("relation")
        node["componentConfig"] = config
        return node

    container_tree: list[dict[str, Any]] = [{
        "type": "header",
        "name": "status",
        "children": [normalize_node("state")] if "state" in field_map or "state" in existing else [],
        "widgetList": [],
    }]
    for index, (title, names) in enumerate(groups, start=1):
        children = [normalize_node(name) for name in names if name in field_map or name in existing]
        if not children:
            continue
        container_tree.append({
            "type": "group",
            "name": "construction_diary_%s" % index,
            "string": title,
            "label": title,
            "children": children,
            "widgetList": [],
        })
    _sc_set_v2_container_tree(contract, container_tree)
    _sc_set_v2_widget_status(
        contract,
        [
            {
                "widgetId": f"field.{name}",
                "visible": True,
                "readonly": name in readonly,
                "required": name in required,
                "disabled": name in readonly,
                "auth": "readonly" if name in readonly else "edit",
            }
            for name in ["state"] + ordered_fields
        ],
    )
    _sc_set_v2_governance_patch(contract, "construction_diary_form", {
        "applied": True,
        "model": model,
        "visible_fields": ordered_fields,
        "hidden_reason": "construction_diary_handling_projection",
    })


def _sc_replace_contract_content(contract: dict[str, Any], replacement: dict[str, Any]) -> None:
    if not isinstance(contract, dict) or not isinstance(replacement, dict):
        return
    contract.clear()
    contract.update(replacement)


def _sc_general_contract_tax_contract(contract: dict[str, Any], source_contract: dict[str, Any] | None = None) -> None:
    if not isinstance(contract, dict):
        return
    model = _sc_text(
        contract.get("model")
        or (source_contract or {}).get("model")
        or ((contract.get("head") or {}).get("model") if isinstance(contract.get("head"), dict) else "")
    )
    field_map = contract.get("fields") if isinstance(contract.get("fields"), dict) else {}
    source_fields = (source_contract or {}).get("fields") if isinstance((source_contract or {}).get("fields"), dict) else {}
    if model != "sc.general.contract" or ("tax_id" not in field_map and "tax_id" not in source_fields):
        return

    def is_tax_rate_node(value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        name = _sc_text(value.get("name") or value.get("field") or value.get("fieldCode"))
        widget_id = _sc_text(value.get("widgetId") or value.get("id"))
        return name == "tax_rate" or widget_id == "field.tax_rate"

    def is_tax_id_node(value: Any) -> bool:
        if not isinstance(value, dict):
            return False
        name = _sc_text(value.get("name") or value.get("field") or value.get("fieldCode"))
        widget_id = _sc_text(value.get("widgetId") or value.get("id"))
        return name == "tax_id" or widget_id == "field.tax_id"

    tax_field = field_map.get("tax_id") if isinstance(field_map.get("tax_id"), dict) else {}
    if not tax_field and isinstance(source_fields.get("tax_id"), dict):
        tax_field = source_fields.get("tax_id") or {}

    def tax_id_field_node(source_node: dict[str, Any]) -> dict[str, Any]:
        role = source_node.get("formStructureRole") if isinstance(source_node.get("formStructureRole"), dict) else {
            "role": "amount",
            "slot": "amount_progress",
            "group": "amounts",
        }
        descriptor = dict(tax_field or {})
        descriptor.update({"name": "tax_id", "label": "税率", "string": "税率", "type": "many2one", "widget": "many2one"})
        return {
            "type": "field",
            "name": "tax_id",
            "formStructureRole": role,
            "string": "税率",
            "label": "税率",
            "fieldInfo": descriptor,
            "widget": "many2one",
            "componentKey": "sc.input.many2one",
            "componentConfig": {"readonly": False, "required": False, "fieldType": "many2one"},
            "widgetId": "field.tax_id",
            "field_info": descriptor,
            "children": [],
            "widgetList": [],
        }

    def is_form_field_node(value: dict[str, Any]) -> bool:
        return _sc_text(value.get("type")) == "field" or isinstance(value.get("fieldInfo"), dict) or isinstance(value.get("field_info"), dict)

    def clean(value: Any):
        if isinstance(value, list):
            return [item for item in (clean(item) for item in value) if item is not None]
        if isinstance(value, dict):
            if is_tax_rate_node(value):
                return tax_id_field_node(value) if is_form_field_node(value) else None
            copied = {}
            for key, item in value.items():
                if key == "tax_rate":
                    continue
                copied[key] = clean(item)
            return copied
        return value

    cleaned = clean(contract)
    if isinstance(cleaned, dict):
        _sc_replace_contract_content(contract, cleaned)

    status_contract = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    widget_status = status_contract.get("widgetStatus") if isinstance(status_contract.get("widgetStatus"), list) else []
    tax_status_rows = [
        row for row in widget_status
        if isinstance(row, dict) and _sc_text(row.get("widgetId")) == "field.tax_id"
    ]
    if not tax_status_rows:
        tax_status_rows = [{"widgetId": "field.tax_id", "visible": True, "readonly": False, "required": False, "disabled": False, "auth": "edit"}]
        widget_status.extend(tax_status_rows)
    for row in tax_status_rows:
        row["visible"] = True
        row["readonly"] = False
        row["disabled"] = False
        row["auth"] = "edit"
    if widget_status:
        _sc_set_v2_widget_status(contract, [
            row for row in widget_status
            if not (isinstance(row, dict) and _sc_text(row.get("widgetId")) == "field.tax_rate")
        ])

    def has_tax_id_layout_node(value: Any) -> bool:
        if is_tax_id_node(value) and (_sc_text((value or {}).get("type")) == "field" or isinstance((value or {}).get("fieldInfo"), dict) or isinstance((value or {}).get("field_info"), dict)):
            return True
        if isinstance(value, list):
            return any(has_tax_id_layout_node(item) for item in value)
        if isinstance(value, dict):
            return any(has_tax_id_layout_node(item) for item in value.values())
        return False

    if has_tax_id_layout_node(contract):
        return
    layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    container_tree = layout_contract.get("containerTree") if isinstance(layout_contract.get("containerTree"), list) else []
    if not container_tree:
        return
    target_field_names = {"contract_amount", "amount_total", "amount_untaxed", "settlement_amount"}

    def append_after_amount_node(rows: list[Any]) -> bool:
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            name = _sc_text(row.get("name") or row.get("field") or row.get("fieldCode"))
            widget_id = _sc_text(row.get("widgetId"))
            if name in target_field_names or widget_id in {f"field.{name}" for name in target_field_names}:
                rows.insert(index + 1, tax_id_field_node(row))
                return True
            for key in ("children", "pages", "tabs", "nodes", "items", "widgetList"):
                children = row.get(key)
                if isinstance(children, list) and append_after_amount_node(children):
                    return True
        return False

    if append_after_amount_node(container_tree):
        _sc_set_v2_container_tree(contract, container_tree)


def _sc_form_layout_governance(source_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(source_contract, dict):
        return {}
    profile = source_contract.get("business_operation_profile")
    governance = profile.get("form_structure_governance") if isinstance(profile, dict) else {}
    return governance if isinstance(governance, dict) else {}


def _sc_form_layout_columns_from_governance(governance: dict[str, Any] | None, title: str = "") -> int:
    if not isinstance(governance, dict):
        return 0
    group_columns = governance.get("group_columns") if isinstance(governance.get("group_columns"), dict) else {}
    key = _sc_text(title)
    try:
        columns = int(group_columns.get(key) or 0) if key else 0
    except (TypeError, ValueError):
        columns = 0
    if columns <= 0:
        try:
            columns = int(governance.get("form_columns") or 0)
        except (TypeError, ValueError):
            columns = 0
    return columns if columns > 0 else 0


def _sc_apply_form_layout_governance_to_group(node: dict[str, Any], title: str = "", *, source_contract: dict[str, Any] | None = None) -> None:
    if not isinstance(node, dict):
        return
    resolved_title = _sc_text(title or node.get("string") or node.get("label") or node.get("title") or node.get("name"))
    columns = _sc_form_layout_columns_from_governance(_sc_form_layout_governance(source_contract), resolved_title)
    if columns <= 0:
        return
    node["cols"] = columns
    node["columns"] = columns
    attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
    attrs["col"] = str(columns)
    node["attributes"] = attrs


def _sc_normalize_general_contract_company_form(contract: dict[str, Any], source_contract: dict[str, Any] | None = None) -> None:
    if not isinstance(contract, dict):
        return
    model = _sc_text(
        contract.get("model")
        or (source_contract or {}).get("model")
        or ((contract.get("pageInfo") or {}).get("model") if isinstance(contract.get("pageInfo"), dict) else "")
        or ((contract.get("head") or {}).get("model") if isinstance(contract.get("head"), dict) else "")
    )
    view_type = _sc_text(
        contract.get("viewType")
        or ((contract.get("pageInfo") or {}).get("viewType") if isinstance(contract.get("pageInfo"), dict) else "")
        or (source_contract or {}).get("view_type")
    ).lower()
    if model != "sc.general.contract" or view_type != "form":
        return
    groups: list[tuple[str, list[str]]] = [
        ("合同基本信息", ["contract_name", "contract_no", "contract_type", "contract_direction", "project_id"]),
        ("合同方", ["partner_id", "partner_name_text", "credit_code", "contact_name", "contact_phone", "engineering_address", "bank_name", "bank_account"]),
        ("金额与条款", ["amount_total", "tax_id", "amount_untaxed", "currency_id", "payment_terms", "special_condition"]),
        ("签署与履约", ["contract_date", "expected_sign_date", "completion_date", "signing_place", "pricing_mode", "union_mode", "subcontract_mode"]),
        ("办理信息", ["applicant_name", "applicant_department", "handler_id", "purchase_engineer", "note"]),
    ]
    ordered_fields = [name for _title, names in groups for name in names]
    visible = set(ordered_fields)
    governance = _sc_form_layout_governance(source_contract)
    hidden_field_names = {_sc_text(item) for item in (governance.get("hidden_field_names") or []) if _sc_text(item)}
    visible.difference_update(hidden_field_names)
    labels = {
        "project_id": "关联项目",
        "partner_name_text": "合同方",
        "amount_total": "合同金额",
        "expected_sign_date": "预计签订日期",
        "signing_place": "签订地点",
        "subcontract_mode": "分包类型",
    }
    required = {"contract_name", "amount_total"}
    readonly = {"contract_no"}
    field_map = (source_contract or {}).get("fields") if isinstance((source_contract or {}).get("fields"), dict) else {}
    existing: dict[str, dict[str, Any]] = {}
    _sc_collect_field_nodes((contract.get("layoutContract") or {}).get("containerTree") if isinstance(contract.get("layoutContract"), dict) else [], existing)

    def descriptor(name: str) -> dict[str, Any]:
        raw = field_map.get(name) if isinstance(field_map.get(name), dict) else {}
        label = labels.get(name) or raw.get("string") or raw.get("label") or name
        return {
            "name": name,
            "label": label,
            "string": label,
            "type": raw.get("type") or raw.get("ttype") or "char",
            "required": name in required or bool(raw.get("required")),
            "readonly": name in readonly or bool(raw.get("readonly")),
            "domain": raw.get("domain") if isinstance(raw.get("domain"), list) else [],
            "context": raw.get("context") if isinstance(raw.get("context"), dict) else {},
            **({"relation": raw.get("relation")} if raw.get("relation") else {}),
            **({"selection": raw.get("selection")} if isinstance(raw.get("selection"), list) else {}),
        }

    def normalize_node(name: str) -> dict[str, Any]:
        node = deepcopy(existing.get(name) or {"type": "field", "name": name, "children": [], "widgetList": []})
        info = descriptor(name)
        label = _sc_text(info.get("label")) or name
        node.update({"type": "field", "name": name, "string": label, "label": label, "widgetId": f"field.{name}"})
        node["fieldInfo"] = {**(node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}), **info}
        node["field_info"] = {**(node.get("field_info") if isinstance(node.get("field_info"), dict) else {}), **info}
        config = node.get("componentConfig") if isinstance(node.get("componentConfig"), dict) else {}
        config.update({"fieldType": info.get("type"), "required": name in required, "readonly": bool(info.get("readonly"))})
        if info.get("selection"):
            config["selection"] = info.get("selection")
        if info.get("relation"):
            config["relation"] = info.get("relation")
        node["componentConfig"] = config
        return node

    container_tree: list[dict[str, Any]] = [{"type": "header", "name": "status", "children": [normalize_node("state")] if "state" in existing else [], "widgetList": []}]
    for index, (title, names) in enumerate(groups, start=1):
        children = [normalize_node(name) for name in names if name in visible and (name in field_map or name in existing)]
        if not children:
            continue
        group_node = {"type": "group", "name": "general_contract_%s" % index, "string": title, "label": title, "children": children, "widgetList": []}
        _sc_apply_form_layout_governance_to_group(group_node, title, source_contract=source_contract)
        container_tree.append(group_node)
    _sc_set_v2_container_tree(contract, container_tree)
    _sc_set_v2_widget_status(contract, [
        {
            "widgetId": f"field.{name}",
            "visible": True,
            "readonly": name in readonly,
            "required": name in required,
            "disabled": name in readonly,
            "auth": "readonly" if name in readonly else "edit",
        }
        for name in ["state"] + ordered_fields
        if name == "state" or name in visible
    ])
    _sc_set_v2_governance_patch(contract, "general_contract_company_form", {
        "applied": True,
        "model": model,
        "visible_fields": ordered_fields,
        "hidden_reason": "company_general_contract_handling_projection",
    })

    def replace_amount_label(value: Any) -> Any:
        if isinstance(value, str):
            return "合同金额" if value == "最终合同价" else value
        if isinstance(value, list):
            return [replace_amount_label(item) for item in value]
        if isinstance(value, dict):
            return {key: replace_amount_label(item) for key, item in value.items()}
        return value

    replaced = replace_amount_label(contract)
    if isinstance(replaced, dict):
        _sc_replace_contract_content(contract, replaced)


def _sc_inject_workflow_contract(env, contract, source, *, model, view_type):
    if view_type != "form" or not model:
        return
    if env is None or not getattr(env, "registry", None):
        return
    record_id = (
        source.get("record_id")
        or source.get("recordId")
        or ((source.get("head") or {}).get("record_id") if isinstance(source.get("head"), dict) else None)
    )
    try:
        record_id = int(record_id or 0)
    except Exception:
        record_id = 0
    if record_id <= 0:
        return
    try:
        if model not in env.registry:
            return
        record = env[model].browse(record_id).exists()
        if not record:
            return
        workflow_contract = env["sc.workflow.contract.service"].describe_record(record)
    except Exception:
        _logger.exception("Failed to inject workflow contract for %s,%s", model, record_id)
        return
    if not isinstance(workflow_contract, dict) or not workflow_contract:
        return
    contract["workflowContract"] = workflow_contract
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    runtime["workflowContract"] = workflow_contract
    contract["runtimeContract"] = runtime
    status = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    global_status = status.get("globalStatus") if isinstance(status.get("globalStatus"), dict) else {}
    editability = _sc_text(workflow_contract.get("editability"))
    if editability in {"readonly", "locked"}:
        global_status["pageAuth"] = "read"
    elif editability == "editable":
        global_status["pageAuth"] = "edit"
    global_status["workflowPhase"] = workflow_contract.get("businessPhase")
    global_status["approvalPhase"] = workflow_contract.get("approvalPhase")
    status["globalStatus"] = global_status
    contract["statusContract"] = status


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


def _user_confirmed_formal_list_action_ids(env):
    ids = set()
    for xmlid in USER_CONFIRMED_FORMAL_LIST_ACTION_XMLIDS:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec and rec.exists():
            ids.add(int(rec.id))
    return ids


def smart_core_finalize_projected_contract_data(env, data, context):
    if not isinstance(data, dict):
        return None
    head = data.get("head") if isinstance(data.get("head"), dict) else {}
    model = str(data.get("model") or head.get("model") or "").strip()
    view_type = str(data.get("view_type") or head.get("view_type") or (context or {}).get("view_type") or "").strip().lower()
    if model == "project.project" and (view_type == "form" or isinstance((data.get("views") or {}).get("form") if isinstance(data.get("views"), dict) else None, dict)):
        projected = dict(data)
        try:
            from odoo.addons.smart_construction_core.services.contract_governance_overrides import (
                _apply_project_ledger_form_surface_governance,
            )

            _apply_project_ledger_form_surface_governance(projected, "user")
            return projected
        except Exception:
            _logger.exception("Failed to finalize project form contract surface")
            return None
    try:
        action_id = int(data.get("action_id") or head.get("action_id") or 0)
    except Exception:
        action_id = 0
    list_profile = data.get("list_profile") if isinstance(data.get("list_profile"), dict) else {}
    column_policy = list_profile.get("column_policy") if isinstance(list_profile.get("column_policy"), dict) else {}
    if str(column_policy.get("reason") or "").strip() == "business_list_config_contract_authoritative":
        return None
    if not action_id or action_id not in _user_confirmed_formal_list_action_ids(env):
        return None
    action = env["ir.actions.act_window"].sudo().browse(action_id)
    if not action.exists() or not action.res_model:
        return None
    try:
        view_contract = (
            env["app.view.config"]
            .with_context(contract_action_id=action_id, contract_projection_readonly=True)
            ._generate_from_fields_view_get(action.res_model, "tree")
            .with_user(env.user)
            .sudo()
            .with_context(contract_action_id=action_id, contract_projection_readonly=True)
            .get_contract_api(filter_runtime=True, check_model_acl=True)
        )
    except Exception:
        _logger.exception("Failed to lock user-confirmed formal list contract for action_id=%s", action_id)
        return None
    if not isinstance(view_contract, dict):
        return None
    try:
        import xml.etree.ElementTree as ET

        view = action.view_id
        arch = view.arch_db if view and view.exists() else ""
        root = ET.fromstring(arch) if arch else None
        fields_get = env[action.res_model].sudo().fields_get()
        locked_columns = []
        locked_schema = []
        locked_order = ""
        if root is not None and root.tag in ("tree", "list"):
            locked_order = str(root.get("default_order") or "").strip()
            for node in root.findall(".//field[@name]"):
                name = str(node.get("name") or "").strip()
                if not name:
                    continue
                if str(node.get("column_invisible") or "").strip() in {"1", "True", "true"}:
                    continue
                meta = fields_get.get(name) or {}
                label = str(node.get("string") or meta.get("string") or name)
                locked_columns.append(name)
                locked_schema.append({
                    "name": name,
                    "label": label,
                    "string": label,
                    "type": meta.get("type") or "char",
                    "widget": node.get("widget") or "",
                    "optional": node.get("optional") or "",
                })
    except Exception:
        _logger.exception("Failed to parse locked tree view for action_id=%s", action_id)
        locked_columns = []
        locked_schema = []
        locked_order = ""

    locked = dict(data)
    views = dict(locked.get("views") if isinstance(locked.get("views"), dict) else {})
    tree = dict(view_contract)
    if locked_columns:
        tree["columns"] = locked_columns
        tree["columns_schema"] = locked_schema
    if locked_order:
        tree["order"] = locked_order
        tree["default_order"] = locked_order
    governance = dict(tree.get("governance") if isinstance(tree.get("governance"), dict) else {})
    governance["user_confirmed_formal_list_lock"] = {
        "applied": True,
        "action_id": action_id,
        "source": "action_bound_tree_view",
    }
    tree["governance"] = governance
    views["tree"] = tree
    locked["views"] = views

    fields_map = dict(locked.get("fields") if isinstance(locked.get("fields"), dict) else {})
    for row in tree.get("columns_schema") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        descriptor = dict(fields_map.get(name) if isinstance(fields_map.get(name), dict) else {})
        label = str(row.get("label") or row.get("string") or descriptor.get("string") or name)
        descriptor.update({
            "name": name,
            "string": label,
            "label": label,
            "type": row.get("type") or descriptor.get("type") or "char",
        })
        fields_map[name] = descriptor
    locked["fields"] = fields_map

    columns = [str(col or "").strip() for col in tree.get("columns") or [] if str(col or "").strip()]
    if columns:
        locked["list_profile"] = {
            **(locked.get("list_profile") if isinstance(locked.get("list_profile"), dict) else {}),
            "columns": columns,
            "column_labels": {
                str(row.get("name") or ""): str(row.get("label") or row.get("string") or row.get("name") or "")
                for row in tree.get("columns_schema") or []
                if isinstance(row, dict) and str(row.get("name") or "").strip()
            },
            "preference_policy": {
                "allow_visibility": False,
                "allow_order": False,
                "locked_columns": columns,
                "must_request_columns": columns,
            },
        }
    return locked


def smart_core_scene_package_service_class(env):
    del env
    from odoo.addons.smart_construction_scene.services.scene_package_service import (
        ScenePackageService,
    )

    return ScenePackageService


def smart_core_scene_governance_service_class(env):
    del env
    from odoo.addons.smart_construction_scene.services.scene_governance_service import (
        SceneGovernanceService,
    )

    return SceneGovernanceService


def smart_core_describe_project_capabilities(env, project):
    from odoo.addons.smart_construction_core.services.lifecycle_capability_service import (
        LifecycleCapabilityService,
    )

    return LifecycleCapabilityService(env).describe_project(project)


def smart_core_build_portal_dashboard(env):
    from odoo.addons.smart_construction_core.services.portal_dashboard_service import (
        PortalDashboardService,
    )

    return PortalDashboardService(env).build_dashboard()


def smart_core_build_capability_matrix(env):
    from odoo.addons.smart_construction_core.services.capability_matrix_service import (
        CapabilityMatrixService,
    )

    return CapabilityMatrixService(env).build_matrix()


def smart_core_get_project_insight(env, record, scene):
    from odoo.addons.smart_construction_core.services.insight.project_insight_service import (
        ProjectInsightService,
    )

    return ProjectInsightService(env).get_insight(record, scene=scene)


def smart_core_build_portal_execute_button_contract(env, model, res_id, method):
    from odoo.addons.smart_construction_core.services.portal_execute_button_service import (
        PortalExecuteButtonService,
    )

    return PortalExecuteButtonService(env).build_contract(
        model=model,
        res_id=res_id,
        method=method,
    )


def smart_core_build_project_execution_service(env):
    from odoo.addons.smart_construction_core.services.project_execution_service import (
        ProjectExecutionService,
    )

    return ProjectExecutionService(env)


def smart_core_build_project_dashboard_service(env):
    from odoo.addons.smart_construction_core.services.project_dashboard_service import (
        ProjectDashboardService,
    )

    return ProjectDashboardService(env)


def smart_core_build_project_plan_bootstrap_service(env):
    from odoo.addons.smart_construction_core.services.project_plan_bootstrap_service import (
        ProjectPlanBootstrapService,
    )

    return ProjectPlanBootstrapService(env)


def smart_core_build_cost_tracking_service(env):
    from odoo.addons.smart_construction_core.services.cost_tracking_service import (
        CostTrackingService,
    )

    return CostTrackingService(env)


def smart_core_build_payment_slice_service(env):
    from odoo.addons.smart_construction_core.services.payment_slice_service import (
        PaymentSliceService,
    )

    return PaymentSliceService(env)


def smart_core_build_settlement_slice_service(env):
    from odoo.addons.smart_construction_core.services.settlement_slice_service import (
        SettlementSliceService,
    )

    return SettlementSliceService(env)
