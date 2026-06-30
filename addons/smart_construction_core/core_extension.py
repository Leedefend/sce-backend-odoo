# -*- coding: utf-8 -*-
import logging
from copy import deepcopy
from typing import Any, Dict, List

from odoo import fields
from odoo.exceptions import AccessError
from odoo.addons.smart_core.utils.backend_contract_boundaries import APPROVAL_POLICY_INTENTS

_logger = logging.getLogger(__name__)


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
        "manager_id": "项目负责人",
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


ROLE_SURFACE_OVERRIDES = {
    "business_config_admin": {
        "label": "业务配置管理员",
        "landing_scene_candidates": ["projects.list", "projects.ledger", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_root",
            "smart_construction_core.menu_sc_business_config_center",
        ],
    },
    "owner": {
        "landing_scene_candidates": ["projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
        ],
    },
    "pm": {
        "landing_scene_candidates": ["portal.dashboard", "projects.ledger", "projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
            "smart_construction_core.menu_sc_cost_center",
        ],
        "menu_blocklist_xmlids": ["smart_construction_core.menu_sc_project_manage"],
    },
    "finance": {
        "landing_scene_candidates": ["finance.payment_requests", "projects.ledger", "projects.list"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_finance_center",
            "smart_construction_core.menu_sc_settlement_center",
            "smart_construction_core.menu_payment_request",
        ],
    },
    "executive": {
        "landing_scene_candidates": ["portal.dashboard", "project.management", "projects.list", "projects.ledger", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_root",
            "smart_construction_core.menu_sc_projection_root",
            "smart_construction_core.menu_sc_project_center",
        ],
    },
}

ROLE_GROUPS_EXPLICIT = {
    "business_config_admin": {
        "smart_construction_core.group_sc_cap_business_config_admin",
    },
    "executive": {
        "smart_construction_custom.group_sc_role_executive",
    },
    "pm": {
        "smart_construction_custom.group_sc_role_pm",
        "smart_construction_custom.group_sc_role_project_manager",
        "smart_construction_custom.group_sc_role_project_user",
        "smart_construction_core.group_sc_role_project_manager",
    },
    "finance": {
        "smart_construction_custom.group_sc_role_finance",
        "smart_construction_custom.group_sc_role_payment_manager",
        "smart_construction_custom.group_sc_role_payment_user",
        "smart_construction_custom.group_sc_role_payment_read",
        "smart_construction_core.group_sc_role_finance_manager",
        "smart_construction_core.group_sc_role_finance_user",
    },
}

ROLE_GROUPS_CAPABILITY_FALLBACK = {
    "pm": {
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_project_user",
    },
    "finance": {
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    },
}

ROLE_PRECEDENCE = ("business_config_admin", "executive", "pm", "finance")

NAV_MENU_SCENE_MAP = {
    "smart_construction_core.menu_sc_project_initiation": "projects.intake",
    "smart_construction_core.menu_sc_project_project": "projects.list",
    "smart_construction_core.menu_sc_project_management_scene": "project.management",
    "smart_construction_core.menu_sc_project_cost_code": "config.project_cost_code",
    "smart_construction_core.menu_sc_root": "projects.list",
    "smart_construction_core.menu_sc_project_dashboard": "projects.dashboard",
    "smart_construction_core.menu_sc_history_todo": "workspace.home",
    "smart_construction_core.menu_sc_operating_metrics_project": "dashboard.company",
    "smart_construction_core.menu_sc_dashboard_cost_cockpit_fact": "cost.control",
    "smart_construction_demo.menu_sc_project_dashboard_showcase": "projects.dashboard_showcase",
    "smart_construction_core.menu_sc_dictionary": "data.dictionary",
    "smart_construction_core.menu_payment_request": "finance.payment_requests",
}

NAV_ACTION_SCENE_MAP = {
    "smart_construction_core.action_project_initiation": "projects.intake",
    "smart_construction_core.action_sc_project_list": "projects.list",
    "smart_construction_core.action_project_dashboard": "projects.dashboard",
    "smart_construction_demo.action_project_dashboard_showcase": "projects.dashboard_showcase",
    "smart_construction_core.action_project_dictionary": "data.dictionary",
    "smart_construction_core.action_project_cost_code": "config.project_cost_code",
    "smart_construction_core.action_sc_dashboard_cost_cockpit_fact": "cost.control",
    "smart_construction_core.action_payment_request": "finance.payment_requests",
    "smart_construction_core.action_payment_request_my": "finance.payment_requests",
}

NAV_MODEL_VIEW_SCENE_MAP = {
    ("project.project", "list"): "projects.list",
    ("project.project", "form"): "projects.intake",
    ("payment.request", "list"): "finance.payment_requests",
    ("payment.request", "form"): "finance.payment_requests",
}

SERVER_ACTION_WINDOW_MAP = {
    "smart_construction_core.action_exec_structure_entry": "smart_construction_core.action_exec_structure_wbs",
}

FILE_ATTACHMENT_ALLOWED_MODEL_EXACT = {
    "payment.ledger",
    "payment.request",
    "payment.request.line",
    "sc.legacy.fund.confirmation.document",
    "sc.legacy.invoice.tax.fact",
    "sc.legacy.payment.residual.fact",
}
FILE_ATTACHMENT_ALLOWED_MODEL_PREFIXES = ("construction.", "project.", "quota.", "sc.", "tender.")
FILE_ATTACHMENT_ALLOWED_LEGACY_MODEL_PREFIXES = ("sc.legacy.",)
FILE_ATTACHMENT_EXCLUDED_MODEL_PREFIXES = (
    "sc.legacy.",
    "sc.ops.",
    "sc.pack.",
    "sc.scene.",
    "sc.subscription.",
    "sc.usage.",
    "sc.workbench.",
    "ui.form.",
)
FILE_UPLOAD_ALLOWED_MODELS = ["project.project", "project.task", "payment.request"]
FILE_DOWNLOAD_ALLOWED_MODELS = ["project.project", "project.task", "payment.request"]
API_DATA_WRITE_ALLOWLIST = {
    "project.project": ["name", "description", "date_start"],
    "project.task": ["name", "description", "date_deadline", "project_id"],
    "purchase.order.line": ["name", "order_id"],
    "res.partner": ["name", "email", "phone", "sc_supplier_type", "sc_supplier_type_ids"],
}
API_DATA_MUTATION_POLICIES = {
    "sc.legacy.receipt.income.fact": {
        "allowed_ops": ["create", "write"],
        "allowed": False,
        "reason_code": "READONLY_PROJECTION_MUTATION_DENIED",
        "message": "历史事实投影为只读数据，不允许通过业务办理接口创建或修改。",
        "source": "smart_construction_core",
    },
}

DRAFT_DELETE_ALLOWED_STATES = ("cancel", "cancelled", "draft")


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

MODEL_CODE_MAPPING = {
    "project": "project.project",
    "task": "project.task",
}

CRITICAL_SCENE_TARGET_OVERRIDES = {
    "projects.list",
    "projects.detail",
    "projects.intake",
    "projects.ledger",
    "projects.execution",
    "projects.dashboard",
    "project.management",
    "my_work.workspace",
    "portal.dashboard",
    "finance.payment_requests",
}

CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES = {
    "my_work.workspace": "/my-work",
}
INDUSTRY_CREATE_FIELD_FALLBACKS = {
    "project.project": {
        "selection_defaults": {
            "privacy_visibility": "followers",
            "rating_status": "stage",
            "last_update_status": "to_define",
            "rating_status_period": "monthly",
        }
    }
}

def _as_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("zh_CN", "en_US"):
            text = str(value.get(key) or "").strip()
            if text:
                return text
        return ""
    return str(value or "").strip()


def _safe_search_read(env, model_name: str, domain: List[Any], fields: List[str], limit: int = 6) -> List[Dict[str, Any]]:
    if model_name not in env:
        return []
    model = env[model_name]
    try:
        return model.search_read(domain, fields=fields, limit=limit, order="write_date desc, id desc")
    except AccessError:
        return []
    except Exception as exc:
        _logger.warning("[smart_core_extend_system_init] search_read failed model=%s error=%s", model_name, exc)
        return []


def _model_has_field(env, model_name: str, field_name: str) -> bool:
    if model_name not in env:
        return False
    return field_name in env[model_name]._fields


def _step_status_label(status: str) -> str:
    key = str(status or "").strip().lower()
    if key == "active":
        return "进行中"
    if key in {"done", "completed"}:
        return "已完成"
    if key in {"pending", "todo", "planned"}:
        return "待开始"
    return "后端未提供步骤状态标签"


def _build_enterprise_enablement_contract(env, user) -> Dict[str, Any]:
    company = getattr(user, "company_id", None)
    company_id = int(getattr(company, "id", 0) or 0)
    company_name = str(getattr(company, "name", "") or "").strip()
    steps = [
        {
            "key": "enterprise_company",
            "label": "企业信息",
            "status": "active" if company_id else "pending",
            "status_label": _step_status_label("active" if company_id else "pending"),
            "entry_xmlid": "smart_enterprise_base.action_enterprise_company",
            "action_xmlid": "smart_enterprise_base.action_enterprise_company",
            "next_hint": "请先补齐企业基础信息。",
            "target": {"action_id": 0, "menu_id": 0, "route": ""},
        },
        {
            "key": "enterprise_department",
            "label": "组织结构",
            "status": "pending",
            "status_label": _step_status_label("pending"),
            "entry_xmlid": "smart_enterprise_base.action_enterprise_department",
            "action_xmlid": "smart_enterprise_base.action_enterprise_department",
            "next_hint": "请补齐部门与岗位结构。",
            "target": {"action_id": 0, "menu_id": 0, "route": ""},
        },
        {
            "key": "enterprise_user",
            "label": "用户设置",
            "status": "pending",
            "status_label": _step_status_label("pending"),
            "entry_xmlid": "smart_enterprise_base.action_enterprise_user",
            "action_xmlid": "smart_enterprise_base.action_enterprise_user",
            "next_hint": "请完成用户、角色和账号初始化。",
            "target": {"action_id": 0, "menu_id": 0, "route": ""},
        },
    ]
    return {
        "mainline": {
            "version": "v1",
            "phase": "sprint1" if company_id else "bootstrap",
            "theme": "enterprise_enablement",
            "entry_root_xmlid": "smart_enterprise_base.menu_enterprise_base_root",
            "current_company_id": company_id,
            "current_company_name": company_name,
            "primary_action": steps[0].get("target") or {},
            "steps": steps,
        }
    }


def _build_task_action_rows(env, user) -> List[Dict[str, Any]]:
    task_fields = ["id", "name", "project_id", "date_deadline", "write_date"]
    if _model_has_field(env, "project.task", "sc_state"):
        task_fields.append("sc_state")
    if _model_has_field(env, "project.task", "kanban_state"):
        task_fields.append("kanban_state")
    user_domain: List[Any] = []
    if _model_has_field(env, "project.task", "user_id"):
        task_fields.append("user_id")
        user_domain.append(("user_id", "=", user.id))
    if _model_has_field(env, "project.task", "user_ids"):
        task_fields.append("user_ids")
        user_domain.append(("user_ids", "in", [user.id]))
    if len(user_domain) == 2:
        scoped_user_domain = ["|"] + user_domain
    else:
        scoped_user_domain = list(user_domain)
    rows = _safe_search_read(
        env,
        "project.task",
        domain=[("sc_state", "in", ["draft", "ready", "in_progress"])] + scoped_user_domain,
        fields=task_fields,
        limit=6,
    ) if _model_has_field(env, "project.task", "sc_state") else []
    if not rows:
        rows = _safe_search_read(
            env,
            "project.task",
            domain=[("sc_state", "in", ["draft", "ready", "in_progress"])],
            fields=task_fields,
            limit=6,
        ) if _model_has_field(env, "project.task", "sc_state") else []
    if not rows and _model_has_field(env, "project.task", "kanban_state"):
        rows = _safe_search_read(
            env,
            "project.task",
            domain=[("kanban_state", "in", ["normal", "blocked"])] + scoped_user_domain,
            fields=task_fields,
            limit=6,
        )
    if not rows and _model_has_field(env, "project.task", "kanban_state"):
        rows = _safe_search_read(
            env,
            "project.task",
            domain=[("kanban_state", "in", ["normal", "blocked"])],
            fields=task_fields,
            limit=6,
        )
    result: List[Dict[str, Any]] = []
    for row in rows:
        task_name = _as_text(row.get("name")) or "待办任务"
        state = _as_text(row.get("sc_state") or row.get("kanban_state"))
        status = "urgent" if state == "in_progress" else "normal"
        project_name = ""
        project_raw = row.get("project_id")
        if isinstance(project_raw, list) and len(project_raw) > 1:
            project_name = _as_text(project_raw[1])
        result.append(
            {
                "id": f"task-{row.get('id')}",
                "title": task_name,
                "description": f"项目任务待处理：{project_name}" if project_name else "项目任务待处理",
                "status": status,
                "count": 1,
                "source_detail": "factual_record",
                "due_date": row.get("date_deadline"),
            }
        )
    return result


def _build_payment_action_rows(env) -> List[Dict[str, Any]]:
    rows = _safe_search_read(
        env,
        "payment.request",
        domain=[("state", "in", ["draft", "submit", "approve", "approved"])],
        fields=["id", "name", "project_id", "state", "amount", "date_request", "write_date"],
        limit=6,
    )
    result: List[Dict[str, Any]] = []
    for row in rows:
        req_name = _as_text(row.get("name")) or "付款申请"
        amount = row.get("amount") or 0
        project_name = ""
        project_raw = row.get("project_id")
        if isinstance(project_raw, list) and len(project_raw) > 1:
            project_name = _as_text(project_raw[1])
        result.append(
            {
                "id": f"payment-{row.get('id')}",
                "title": f"付款申请待审批 · {req_name}",
                "description": f"{project_name} 申请金额 {amount}" if project_name else f"申请金额 {amount}",
                "status": "urgent",
                "amount": amount,
                "count": 1,
                "source_detail": "factual_record",
                "deadline": row.get("date_request"),
            }
        )
    return result


def _build_risk_action_rows(env) -> List[Dict[str, Any]]:
    actionable_rows = _safe_search_read(
        env,
        "project.risk.action",
        domain=[("state", "in", ["open", "claimed", "escalated"])],
        fields=["id", "name", "state", "risk_level", "project_id", "write_date"],
        limit=6,
    )
    if actionable_rows:
        result: List[Dict[str, Any]] = []
        for row in actionable_rows:
            state = _as_text(row.get("state")).lower()
            status = "urgent" if state in {"open", "escalated"} else "normal"
            title = _as_text(row.get("name")) or "风险事项"
            project_name = ""
            project_raw = row.get("project_id")
            if isinstance(project_raw, list) and len(project_raw) > 1:
                project_name = _as_text(project_raw[1])
            result.append(
                {
                    "id": f"risk-action-{row.get('id')}",
                    "title": f"风险处置 · {title}",
                    "description": f"{project_name} 风险状态：{state}" if project_name else f"风险状态：{state}",
                    "status": status,
                    "count": 1,
                    "risk_action_id": int(row.get("id") or 0),
                    "source_detail": "factual_record",
                }
            )
        return result

    rows = _safe_search_read(
        env,
        "project.risk",
        domain=[],
        fields=["id", "name", "health_state", "write_date"],
        limit=6,
    )
    if not rows:
        rows = _safe_search_read(
            env,
            "project.project",
            domain=[("health_state", "in", ["risk", "warn"])],
            fields=["id", "name", "health_state", "write_date"],
            limit=6,
        )
    if not rows:
        task_fields = ["id", "name", "project_id", "date_deadline", "write_date"]
        if _model_has_field(env, "project.task", "sc_state"):
            task_fields.append("sc_state")
        if _model_has_field(env, "project.task", "kanban_state"):
            task_fields.append("kanban_state")
        overdue_rows = _safe_search_read(
            env,
            "project.task",
            domain=[("date_deadline", "<", fields.Datetime.now())],
            fields=task_fields,
            limit=6,
        )
        result: List[Dict[str, Any]] = []
        for row in overdue_rows:
            task_name = _as_text(row.get("name")) or "逾期任务"
            project_name = ""
            project_raw = row.get("project_id")
            if isinstance(project_raw, list) and len(project_raw) > 1:
                project_name = _as_text(project_raw[1])
            result.append(
                {
                    "id": f"task-risk-{row.get('id')}",
                    "title": f"任务逾期风险 · {task_name}",
                    "description": f"{project_name} 存在逾期任务，请优先跟进。" if project_name else "存在逾期任务，请优先跟进。",
                    "status": "urgent",
                    "count": 1,
                    "model": "project.task",
                    "record_id": int(row.get("id") or 0),
                    "task_id": int(row.get("id") or 0),
                    "deadline": row.get("date_deadline"),
                    "source_detail": "factual_record",
                }
            )
        if result:
            return result
    result: List[Dict[str, Any]] = []
    for row in rows:
        health = _as_text(row.get("health_state"))
        status = "urgent" if health == "risk" else "normal"
        title = _as_text(row.get("name")) or "风险事项"
        result.append(
            {
                "id": f"risk-{row.get('id')}",
                "title": f"项目风险预警 · {title}",
                "description": "项目健康状态异常，请优先跟进。",
                "status": status,
                "count": 1,
                "project_id": int(row.get("id") or 0),
                "name": title,
                "source_detail": "factual_record",
            }
        )
    return result


def _build_project_action_rows(env, user) -> List[Dict[str, Any]]:
    rows = _safe_search_read(
        env,
        "project.project",
        domain=[("active", "=", True)],
        fields=["id", "name", "health_state", "lifecycle_state", "write_date", "user_id", "manager_id"],
        limit=6,
    )
    result: List[Dict[str, Any]] = []
    for row in rows:
        health = _as_text(row.get("health_state"))
        lifecycle = _as_text(row.get("lifecycle_state"))
        title = _as_text(row.get("name")) or "项目事项"
        if health in {"risk", "warn"} or lifecycle in {"draft", "in_progress"}:
            status = "urgent" if health == "risk" else "normal"
            result.append(
                {
                    "id": f"project-{row.get('id')}",
                    "title": f"项目跟进 · {title}",
                    "description": "项目状态需要关注，请进入项目管理跟进。",
                    "status": status,
                    "count": 1,
                    "source_detail": "factual_record",
                }
            )
    return result


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


def _dictionary_fields(env) -> List[str]:
    fields_to_read = ["code", "name", "value_json", "sequence"]
    for field_name in ("scope_type", "scope_ref"):
        if _model_has_field(env, "sc.dictionary", field_name):
            fields_to_read.append(field_name)
    return fields_to_read


def _build_role_entry_contract_rows(env) -> List[Dict[str, Any]]:
    rows = _safe_search_read(
        env,
        "sc.dictionary",
        domain=[("type", "=", "role_entry"), ("active", "=", True)],
        fields=_dictionary_fields(env),
        limit=200,
    )
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        scope_type = _as_text(row.get("scope_type")) or "global"
        scope_ref = _as_text(row.get("scope_ref"))
        role_code = ""
        if scope_type == "role":
            role_code = scope_ref
        elif scope_type in {"global", "company"}:
            role_code = "__global__"
        if not role_code:
            continue

        value_json = row.get("value_json") if isinstance(row.get("value_json"), dict) else {}
        entry_key = (
            _as_text(row.get("code"))
            or _as_text(value_json.get("entry_key"))
            or _as_text(row.get("name"))
        )
        if not entry_key:
            continue

        entry_type = _as_text(value_json.get("entry_type")) or "menu"
        is_enabled = value_json.get("is_enabled")
        if isinstance(is_enabled, bool):
            enabled = is_enabled
        else:
            enabled = True
        sequence = int(row.get("sequence") or 10)

        grouped.setdefault(role_code, []).append(
            {
                "entry_key": entry_key,
                "entry_type": entry_type,
                "is_enabled": enabled,
                "sequence": sequence,
            }
        )

    contract_rows: List[Dict[str, Any]] = []
    for role_code, entries in grouped.items():
        sorted_entries = sorted(
            entries,
            key=lambda item: (
                int(item.get("sequence") or 10),
                str(item.get("entry_key") or ""),
            ),
        )
        contract_rows.append(
            {
                "role_code": role_code,
                "entries": sorted_entries,
            }
        )

    return sorted(contract_rows, key=lambda item: str(item.get("role_code") or ""))


def _build_home_block_contract_rows(env) -> List[Dict[str, Any]]:
    rows = _safe_search_read(
        env,
        "sc.dictionary",
        domain=[("type", "=", "home_block"), ("active", "=", True)],
        fields=_dictionary_fields(env),
        limit=200,
    )
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        scope_type = _as_text(row.get("scope_type")) or "global"
        scope_ref = _as_text(row.get("scope_ref"))
        role_code = ""
        if scope_type == "role":
            role_code = scope_ref
        elif scope_type == "global":
            role_code = "__global__"
        if not role_code:
            continue

        value_json = row.get("value_json") if isinstance(row.get("value_json"), dict) else {}
        block_key = (
            _as_text(row.get("code"))
            or _as_text(value_json.get("block_key"))
            or _as_text(row.get("name"))
        )
        if not block_key:
            continue

        is_enabled = value_json.get("is_enabled")
        if isinstance(is_enabled, bool):
            enabled = is_enabled
        else:
            enabled = True
        if not enabled:
            continue

        sequence = int(row.get("sequence") or 10)
        grouped.setdefault(role_code, []).append(
            {
                "block_key": block_key,
                "sequence": sequence,
            }
        )

    contract_rows: List[Dict[str, Any]] = []
    for role_code, blocks in grouped.items():
        sorted_blocks = sorted(
            blocks,
            key=lambda item: (
                int(item.get("sequence") or 10),
                str(item.get("block_key") or ""),
            ),
        )
        contract_rows.append(
            {
                "role_code": role_code,
                "blocks": [str(item.get("block_key") or "") for item in sorted_blocks if str(item.get("block_key") or "")],
            }
        )

    return sorted(contract_rows, key=lambda item: str(item.get("role_code") or ""))


def get_intent_handler_contributions():
    """Return construction intent handler contributions for platform loader."""
    try:
        from odoo.addons.smart_construction_core.handlers.system_ping_construction import (
            SystemPingConstructionHandler,
        )
        from odoo.addons.smart_construction_core.handlers.capability_describe import (
            CapabilityDescribeHandler,
        )
        from odoo.addons.smart_construction_core.handlers.my_work_summary import (
            MyWorkSummaryHandler,
        )
        from odoo.addons.smart_construction_core.handlers.my_work_complete import (
            MyWorkCompleteHandler,
            MyWorkCompleteBatchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.telemetry_track import (
            TelemetryTrackHandler,
        )
        from odoo.addons.smart_construction_core.handlers.capability_visibility_report import (
            CapabilityVisibilityReportHandler,
        )
        from odoo.addons.smart_construction_core.handlers.approval_policy_configuration import (
            ApprovalPolicyConfigGetHandler,
            ApprovalPolicyConfigSetHandler,
            ApprovalPolicyStepsSetHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_request_approval import (
            PaymentRequestApproveHandler,
            PaymentRequestDoneHandler,
            PaymentRequestRejectHandler,
            PaymentRequestSubmitHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
            PaymentRequestAvailableActionsHandler,
        )
        from odoo.addons.smart_construction_core.handlers.payment_request_execute import (
            PaymentRequestExecuteHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_dashboard import (
            ProjectDashboardHandler,
        )
        from odoo.addons.smart_construction_core.handlers.risk_action_execute import (
            RiskActionExecuteHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_initiation_enter import (
            ProjectInitiationEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_dashboard_open import (
            ProjectDashboardOpenHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_dashboard_enter import (
            ProjectDashboardEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_entry_context_resolve import (
            ProjectEntryContextResolveHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_entry_context_options import (
            ProjectEntryContextOptionsHandler,
        )
        from odoo.addons.smart_construction_core.handlers.business_evidence_trace import (
            BusinessEvidenceTraceHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_dashboard_block_fetch import (
            ProjectDashboardBlockFetchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_enter import (
            ProjectPlanBootstrapEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_plan_bootstrap_block_fetch import (
            ProjectPlanBootstrapBlockFetchHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_execution_enter import (
            ProjectExecutionEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.project_execution_block_fetch import (
            ProjectExecutionBlockFetchHandler,
        )
        try:
            from odoo.addons.smart_construction_core.handlers.project_execution_advance import (
                ProjectExecutionAdvanceHandler,
            )
        except Exception as exc:
            ProjectExecutionAdvanceHandler = None
            _logger.warning("[get_intent_handler_contributions] skip project_execution_advance: %s", exc)
        from odoo.addons.smart_construction_core.handlers.project_connection_transition import (
            ProjectConnectionTransitionHandler,
        )
        from odoo.addons.smart_construction_core.handlers.cost_tracking_enter import (
            CostTrackingEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.cost_tracking_block_fetch import (
            CostTrackingBlockFetchHandler,
        )
        try:
            from odoo.addons.smart_construction_core.handlers.cost_tracking_record_create import (
                CostTrackingRecordCreateHandler,
            )
        except Exception as exc:
            CostTrackingRecordCreateHandler = None
            _logger.warning("[get_intent_handler_contributions] skip cost_tracking_record_create: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.payment_slice_enter import (
                PaymentSliceEnterHandler,
            )
        except Exception as exc:
            PaymentSliceEnterHandler = None
            _logger.warning("[get_intent_handler_contributions] skip payment_slice_enter: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.payment_slice_block_fetch import (
                PaymentSliceBlockFetchHandler,
            )
        except Exception as exc:
            PaymentSliceBlockFetchHandler = None
            _logger.warning("[get_intent_handler_contributions] skip payment_slice_block_fetch: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.payment_slice_record_create import (
                PaymentSliceRecordCreateHandler,
            )
        except Exception as exc:
            PaymentSliceRecordCreateHandler = None
            _logger.warning("[get_intent_handler_contributions] skip payment_slice_record_create: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.settlement_slice_enter import (
                SettlementSliceEnterHandler,
            )
        except Exception as exc:
            SettlementSliceEnterHandler = None
            _logger.warning("[get_intent_handler_contributions] skip settlement_slice_enter: %s", exc)
        try:
            from odoo.addons.smart_construction_core.handlers.settlement_slice_block_fetch import (
                SettlementSliceBlockFetchHandler,
            )
        except Exception as exc:
            SettlementSliceBlockFetchHandler = None
            _logger.warning("[get_intent_handler_contributions] skip settlement_slice_block_fetch: %s", exc)
        from odoo.addons.smart_construction_core.handlers.workspace_home_enter import (
            WorkspaceHomeEnterHandler,
        )
        from odoo.addons.smart_construction_core.handlers.dashboard_company_enter import (
            DashboardCompanyEnterHandler,
        )
    except Exception as e:
        _logger.warning("[get_intent_handler_contributions] import handler failed: %s", e)
        return []

    mapping = [
        ("system.ping.construction", SystemPingConstructionHandler),
        ("capability.describe", CapabilityDescribeHandler),
        ("my.work.summary", MyWorkSummaryHandler),
        ("my.work.complete", MyWorkCompleteHandler),
        ("my.work.complete_batch", MyWorkCompleteBatchHandler),
        ("telemetry.track", TelemetryTrackHandler),
        ("capability.visibility.report", CapabilityVisibilityReportHandler),
        (APPROVAL_POLICY_INTENTS["config_get"], ApprovalPolicyConfigGetHandler),
        (APPROVAL_POLICY_INTENTS["config_set"], ApprovalPolicyConfigSetHandler),
        (APPROVAL_POLICY_INTENTS["steps_set"], ApprovalPolicyStepsSetHandler),
        ("payment.request.submit", PaymentRequestSubmitHandler),
        ("payment.request.approve", PaymentRequestApproveHandler),
        ("payment.request.reject", PaymentRequestRejectHandler),
        ("payment.request.done", PaymentRequestDoneHandler),
        ("payment.request.available_actions", PaymentRequestAvailableActionsHandler),
        ("payment.request.execute", PaymentRequestExecuteHandler),
        ("project.dashboard", ProjectDashboardHandler),
        ("project.dashboard.open", ProjectDashboardOpenHandler),
        ("project.dashboard.enter", ProjectDashboardEnterHandler),
        ("project.entry.context.resolve", ProjectEntryContextResolveHandler),
        ("project.entry.context.options", ProjectEntryContextOptionsHandler),
        ("business.evidence.trace", BusinessEvidenceTraceHandler),
        ("project.dashboard.block.fetch", ProjectDashboardBlockFetchHandler),
        ("project.plan_bootstrap.enter", ProjectPlanBootstrapEnterHandler),
        ("project.plan_bootstrap.block.fetch", ProjectPlanBootstrapBlockFetchHandler),
        ("project.execution.enter", ProjectExecutionEnterHandler),
        ("project.execution.block.fetch", ProjectExecutionBlockFetchHandler),
        ("project.execution.advance", ProjectExecutionAdvanceHandler),
        ("project.connection.transition", ProjectConnectionTransitionHandler),
        ("cost.tracking.enter", CostTrackingEnterHandler),
        ("cost.tracking.block.fetch", CostTrackingBlockFetchHandler),
        ("cost.tracking.record.create", CostTrackingRecordCreateHandler),
        ("payment.enter", PaymentSliceEnterHandler),
        ("payment.block.fetch", PaymentSliceBlockFetchHandler),
        ("payment.record.create", PaymentSliceRecordCreateHandler),
        ("settlement.enter", SettlementSliceEnterHandler),
        ("settlement.block.fetch", SettlementSliceBlockFetchHandler),
        ("project.initiation.enter", ProjectInitiationEnterHandler),
        ("risk.action.execute", RiskActionExecuteHandler),
        ("workspace.home.enter", WorkspaceHomeEnterHandler),
        ("dashboard.company.enter", DashboardCompanyEnterHandler),
    ]
    return [
        {
            "intent": intent,
            "handler": handler,
            "source_module": "smart_construction_core",
            "domain": "construction",
            "status": "active",
        }
        for intent, handler in mapping
        if handler is not None
    ]


def smart_core_register(registry):
    """Legacy loader shim for smart_core.core.extension_loader."""
    if not isinstance(registry, dict):
        return
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
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        if not key:
            continue
        identity_name = str(row.get("name") or row.get("ui_label") or key).strip() or key
        group_key = str(row.get("group_key") or "others").strip() or "others"
        intent_name = str(row.get("intent") or "ui.contract").strip() or "ui.contract"
        entry_target = row.get("entry_target") if isinstance(row.get("entry_target"), dict) else {}
        entry_scene_key = str(entry_target.get("scene_key") or "").strip()
        item = {
            "key": key,
            "name": identity_name,
            "domain": str(key.split(".")[0] if "." in key else "construction").strip() or "construction",
            "type": "entry",
            "source_module": "smart_construction_core",
            "owner_module": "smart_core",
            "status": str(row.get("status") or "ga").strip().lower() or "ga",
            "group_key": group_key,
            "group_label": str(row.get("group_label") or "").strip(),
            "group_icon": str(row.get("group_icon") or "").strip(),
            "group_sequence": int(row.get("group_sequence") or 0),
            "ui_label": str(row.get("ui_label") or identity_name).strip(),
            "ui_hint": str(row.get("ui_hint") or "").strip(),
            "intent": intent_name,
            "required_roles": [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()],
            "required_groups": [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()],
            "entry_target": dict(entry_target),
            "sequence": int(row.get("sequence") or 0),
            "tags": list(row.get("tags") or []),
            "identity": {
                "key": key,
                "name": identity_name,
                "domain": str(key.split(".")[0] if "." in key else "construction").strip() or "construction",
                "type": "entry",
                "version": "v1",
            },
            "ownership": {
                "owner_module": "smart_core",
                "source_module": "smart_construction_core",
                "source_kind": "industry_contribution",
            },
            "ui": {
                "label": str(row.get("ui_label") or identity_name).strip(),
                "hint": str(row.get("ui_hint") or "").strip(),
                "group_key": group_key,
                "icon": str(row.get("group_icon") or "").strip(),
                "sequence": int(row.get("sequence") or 0),
                "tags": list(row.get("tags") or []),
            },
            "binding": {
                "scene": {
                    "entry_scene_key": entry_scene_key,
                    "target_mode": str(entry_target.get("target_mode") or "scene").strip() or "scene",
                },
                "intent": {
                    "primary_intent": intent_name,
                },
                "contract": {
                    "subject": "scene",
                    "contract_type": "entry_contract",
                    "contract_version": "v1",
                },
                "exposure": {
                    "group_key": group_key,
                },
            },
            "permission": {
                "required_roles": [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()],
                "required_groups": [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()],
                "access_mode": "execute",
                "data_scope": "user_env",
            },
            "release": {
                "tier": "standard",
                "slice": "",
                "exposure_mode": "default",
                "approval_required": False,
                "feature_flag": "",
            },
            "lifecycle": {
                "status": str(row.get("status") or "ga").strip().lower() or "ga",
                "deprecated": False,
                "replacement_key": "",
                "introduced_in": "",
                "sunset_after": "",
            },
            "runtime": {
                "supports_entry": True,
                "supports_execute": False,
                "supports_batch": False,
                "safe_fallback": "workspace.home",
            },
            "audit": {
                "audit_enabled": True,
                "policy_trace_enabled": True,
                "owner_trace": "smart_construction_core.get_capability_contributions",
            },
        }
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
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        if not key:
            continue
        identity_name = str(row.get("name") or row.get("ui_label") or key).strip() or key
        group_key = str(row.get("group_key") or "others").strip() or "others"
        intent_name = str(row.get("intent") or "ui.contract").strip() or "ui.contract"
        entry_target = row.get("entry_target") if isinstance(row.get("entry_target"), dict) else {}
        entry_scene_key = str(entry_target.get("scene_key") or "").strip()
        item = {
            "key": key,
            "name": identity_name,
            "domain": str(key.split(".")[0] if "." in key else "construction").strip() or "construction",
            "type": "entry",
            "source_module": "smart_construction_core",
            "owner_module": "smart_core",
            "status": str(row.get("status") or "ga").strip().lower() or "ga",
            "group_key": group_key,
            "group_label": str(row.get("group_label") or "").strip(),
            "group_icon": str(row.get("group_icon") or "").strip(),
            "group_sequence": int(row.get("group_sequence") or 0),
            "ui_label": str(row.get("ui_label") or identity_name).strip(),
            "ui_hint": str(row.get("ui_hint") or "").strip(),
            "intent": intent_name,
            "required_roles": [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()],
            "required_groups": [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()],
            "entry_target": dict(entry_target),
            "sequence": int(row.get("sequence") or 0),
            "tags": list(row.get("tags") or []),
            "identity": {
                "key": key,
                "name": identity_name,
                "domain": str(key.split(".")[0] if "." in key else "construction").strip() or "construction",
                "type": "entry",
                "version": "v1",
            },
            "ownership": {
                "owner_module": "smart_core",
                "source_module": "smart_construction_core",
                "source_kind": "industry_contribution",
            },
            "ui": {
                "label": str(row.get("ui_label") or identity_name).strip(),
                "hint": str(row.get("ui_hint") or "").strip(),
                "group_key": group_key,
                "icon": str(row.get("group_icon") or "").strip(),
                "sequence": int(row.get("sequence") or 0),
                "tags": list(row.get("tags") or []),
            },
            "binding": {
                "scene": {
                    "entry_scene_key": entry_scene_key,
                    "target_mode": str(entry_target.get("target_mode") or "scene").strip() or "scene",
                },
                "intent": {
                    "primary_intent": intent_name,
                },
                "contract": {
                    "subject": "scene",
                    "contract_type": "entry_contract",
                    "contract_version": "v1",
                },
                "exposure": {
                    "group_key": group_key,
                },
            },
            "permission": {
                "required_roles": [str(x).strip() for x in (row.get("required_roles") or []) if str(x).strip()],
                "required_groups": [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()],
                "access_mode": "execute",
                "data_scope": "user_env",
            },
            "release": {
                "tier": "standard",
                "slice": "",
                "exposure_mode": "default",
                "approval_required": False,
                "feature_flag": "",
            },
            "lifecycle": {
                "status": str(row.get("status") or "ga").strip().lower() or "ga",
                "deprecated": False,
                "replacement_key": "",
                "introduced_in": "",
                "sunset_after": "",
            },
            "runtime": {
                "supports_entry": True,
                "supports_execute": False,
                "supports_batch": False,
                "safe_fallback": "workspace.home",
            },
            "audit": {
                "audit_enabled": True,
                "policy_trace_enabled": True,
                "owner_trace": "smart_construction_core.get_capability_contributions",
            },
        }
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
    """Legacy hook shim consumed by smart_core capability provider."""
    return get_capability_contributions(env, user)


def smart_core_capability_groups(env):
    """Legacy hook shim consumed by smart_core capability provider."""
    return get_capability_group_contributions(env)


def get_create_field_fallback_contributions(env, model_name):
    del env
    return dict(INDUSTRY_CREATE_FIELD_FALLBACKS.get(str(model_name or ""), {}))


def smart_core_create_field_fallbacks(env, model_name):
    """Legacy hook shim consumed by smart_core api.data handlers."""
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
    rows = data.get("actions") if isinstance(data, dict) and isinstance(data.get("actions"), list) else []
    primary_key = str(data.get("primary_action_key") or "") if isinstance(data, dict) else ""
    method_aliases = {
        "submit": ["action_submit"],
        "approve": ["action_approve", "action_set_approved", "validate_tier"],
        "reject": ["reject_tier", "action_on_tier_rejected"],
        "done": ["action_done"],
    }
    actions = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        action_key = str(row.get("key") or "").strip()
        if not action_key:
            continue
        methods = method_aliases.get(action_key, [str(row.get("method") or "").strip()])
        if action_key == "approve" and str(row.get("method") or "").strip() == "action_approval_decision":
            methods = ["action_approval_decision", *methods]
        for method in methods:
            if not method:
                continue
            actions.append(
                {
                    "key": f"payment_{action_key}",
                    "action_key": action_key,
                    "label": str(row.get("label") or action_key),
                    "kind": "mutation",
                    "level": "header",
                    "selection": "none",
                    "visible_profiles": ["edit", "readonly"],
                    "method": method,
                    "intent": str(row.get("execute_intent") or row.get("intent") or "payment.request.execute"),
                    "allowed": bool(row.get("allowed")),
                    "reason_code": str(row.get("reason_code") or ""),
                    "blocked_message": str(row.get("blocked_message") or ""),
                    "warning_message": str(row.get("warning_message") or ""),
                    "advisory_warnings": list(row.get("advisory_warnings") or []),
                    "advisory_reason_codes": list(row.get("advisory_reason_codes") or []),
                    "force_block_available": bool(row.get("force_block_available")),
                    "suggested_action": str(row.get("suggested_action") or ""),
                    "required_role_key": str(row.get("required_role_key") or ""),
                    "required_role_label": str(row.get("required_role_label") or ""),
                    "handoff_required": bool(row.get("handoff_required")),
                    "handoff_hint": str(row.get("handoff_hint") or ""),
                    "requires_reason": bool(row.get("requires_reason")),
                    "required_params": list(row.get("required_params") or []),
                    "primary": action_key == primary_key,
                    "mutation": {
                        "type": "record_action",
                        "model": "payment.request",
                        "operation": action_key,
                        "payload_schema": {
                            "id": "record_id",
                            "reason": "string" if bool(row.get("requires_reason")) else "",
                        },
                    },
                    "refresh_policy": {
                        "on_success": ["scene_projection"],
                        "mode": "reload_record",
                        "scope": "record",
                    },
                }
            )
    attachments = {
        "enabled": True,
        "label": "附件",
        "upload": {
            "intent": "file.upload",
            "max_bytes": 5 * 1024 * 1024,
            "accepted_types": [],
        },
        "download": {
            "intent": "file.download",
        },
        "ui_labels": {
            "upload": "上传附件",
            "uploading": "上传中...",
            "download": "下载",
            "upload_failed": "附件上传失败",
            "download_failed": "附件下载失败",
            "size_exceeded": "文件过大",
        },
    }
    return {"actions": actions, "attachments": attachments}


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
    """Legacy hook shim: write construction facts only under data['ext_facts']."""
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
    return data


def smart_core_server_action_window_map(env):
    return get_server_action_window_map_contributions(env)


def smart_core_file_upload_allowed_models(env):
    return get_file_upload_allowed_model_contributions(env)


def smart_core_file_download_allowed_models(env):
    return get_file_download_allowed_model_contributions(env)


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


USER_CONFIRMED_FORMAL_LIST_ACTION_XMLIDS = {
    "smart_construction_core.action_project_material_plan",
    "smart_construction_core.action_sc_labor_usage_ticket",
    "smart_construction_core.action_sc_labor_usage_casual",
    "smart_construction_core.action_sc_equipment_usage_shift_user_confirmed",
    "smart_construction_core.action_sc_material_quote_user_confirmed",
    "smart_construction_core.action_sc_subcontract_request_user_confirmed",
    "smart_construction_core.action_payment_request_user_payment_apply",
    "smart_construction_core.action_sc_payment_execution_partner_payment",
    "smart_construction_core.action_sc_legacy_fuel_card_fact",
    "smart_construction_core.action_sc_legacy_fuel_card_recharge_fact",
    "smart_construction_core.action_sc_expense_claim_deduction_paid",
    "smart_construction_core.action_sc_expense_claim_deduction_paid_refund",
}


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
