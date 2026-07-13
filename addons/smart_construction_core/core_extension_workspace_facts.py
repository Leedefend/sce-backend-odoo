# -*- coding: utf-8 -*-
import logging
from typing import Any, Dict, List

from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


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

