# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any, Dict, List

from odoo import fields
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)

def as_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("zh_CN", "en_US"):
            text = str(value.get(key) or "").strip()
            if text:
                return text
        return ""
    return str(value or "").strip()

def safe_search_read(env, model_name: str, domain: List[Any], fields: List[str], limit: int = 6) -> List[Dict[str, Any]]:
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

def model_has_field(env, model_name: str, field_name: str) -> bool:
    if model_name not in env:
        return False
    return field_name in env[model_name]._fields

def step_status_label(status: str) -> str:
    key = str(status or "").strip().lower()
    if key == "active":
        return "进行中"
    if key in {"done", "completed"}:
        return "已完成"
    if key in {"pending", "todo", "planned"}:
        return "待开始"
    return "后端未提供步骤状态标签"

def build_enterprise_enablement_contract(env, user) -> Dict[str, Any]:
    company = getattr(user, "company_id", None)
    company_id = int(getattr(company, "id", 0) or 0)
    company_name = str(getattr(company, "name", "") or "").strip()
    steps = [
        {
            "key": "enterprise_company",
            "label": "企业信息",
            "status": "active" if company_id else "pending",
            "status_label": step_status_label("active" if company_id else "pending"),
            "entry_xmlid": "smart_enterprise_base.action_enterprise_company",
            "action_xmlid": "smart_enterprise_base.action_enterprise_company",
            "next_hint": "请先补齐企业基础信息。",
            "target": {"action_id": 0, "menu_id": 0, "route": ""},
        },
        {
            "key": "enterprise_department",
            "label": "组织结构",
            "status": "pending",
            "status_label": step_status_label("pending"),
            "entry_xmlid": "smart_enterprise_base.action_enterprise_department",
            "action_xmlid": "smart_enterprise_base.action_enterprise_department",
            "next_hint": "请补齐部门与岗位结构。",
            "target": {"action_id": 0, "menu_id": 0, "route": ""},
        },
        {
            "key": "enterprise_user",
            "label": "用户设置",
            "status": "pending",
            "status_label": step_status_label("pending"),
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

def build_task_action_rows(env, user) -> List[Dict[str, Any]]:
    task_fields = ["id", "name", "project_id", "date_deadline", "write_date"]
    if model_has_field(env, "project.task", "sc_state"):
        task_fields.append("sc_state")
    if model_has_field(env, "project.task", "kanban_state"):
        task_fields.append("kanban_state")
    user_domain: List[Any] = []
    if model_has_field(env, "project.task", "user_id"):
        task_fields.append("user_id")
        user_domain.append(("user_id", "=", user.id))
    if model_has_field(env, "project.task", "user_ids"):
        task_fields.append("user_ids")
        user_domain.append(("user_ids", "in", [user.id]))
    if len(user_domain) == 2:
        scoped_user_domain = ["|"] + user_domain
    else:
        scoped_user_domain = list(user_domain)
    rows = safe_search_read(
        env,
        "project.task",
        domain=[("sc_state", "in", ["draft", "ready", "in_progress"])] + scoped_user_domain,
        fields=task_fields,
        limit=6,
    ) if model_has_field(env, "project.task", "sc_state") else []
    if not rows:
        rows = safe_search_read(
            env,
            "project.task",
            domain=[("sc_state", "in", ["draft", "ready", "in_progress"])],
            fields=task_fields,
            limit=6,
        ) if model_has_field(env, "project.task", "sc_state") else []
    if not rows and model_has_field(env, "project.task", "kanban_state"):
        rows = safe_search_read(
            env,
            "project.task",
            domain=[("kanban_state", "in", ["normal", "blocked"])] + scoped_user_domain,
            fields=task_fields,
            limit=6,
        )
    if not rows and model_has_field(env, "project.task", "kanban_state"):
        rows = safe_search_read(
            env,
            "project.task",
            domain=[("kanban_state", "in", ["normal", "blocked"])],
            fields=task_fields,
            limit=6,
        )
    result: List[Dict[str, Any]] = []
    for row in rows:
        task_name = as_text(row.get("name")) or "待办任务"
        state = as_text(row.get("sc_state") or row.get("kanban_state"))
        status = "urgent" if state == "in_progress" else "normal"
        project_name = ""
        project_raw = row.get("project_id")
        if isinstance(project_raw, list) and len(project_raw) > 1:
            project_name = as_text(project_raw[1])
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

def build_payment_action_rows(env) -> List[Dict[str, Any]]:
    rows = safe_search_read(
        env,
        "payment.request",
        domain=[("state", "in", ["draft", "submit", "approve", "approved"])],
        fields=["id", "name", "project_id", "state", "amount", "date_request", "write_date"],
        limit=6,
    )
    result: List[Dict[str, Any]] = []
    for row in rows:
        req_name = as_text(row.get("name")) or "付款申请"
        amount = row.get("amount") or 0
        project_name = ""
        project_raw = row.get("project_id")
        if isinstance(project_raw, list) and len(project_raw) > 1:
            project_name = as_text(project_raw[1])
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

def build_risk_action_rows(env) -> List[Dict[str, Any]]:
    actionable_rows = safe_search_read(
        env,
        "project.risk.action",
        domain=[("state", "in", ["open", "claimed", "escalated"])],
        fields=["id", "name", "state", "risk_level", "project_id", "write_date"],
        limit=6,
    )
    if actionable_rows:
        result: List[Dict[str, Any]] = []
        for row in actionable_rows:
            state = as_text(row.get("state")).lower()
            status = "urgent" if state in {"open", "escalated"} else "normal"
            title = as_text(row.get("name")) or "风险事项"
            project_name = ""
            project_raw = row.get("project_id")
            if isinstance(project_raw, list) and len(project_raw) > 1:
                project_name = as_text(project_raw[1])
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

    rows = safe_search_read(
        env,
        "project.risk",
        domain=[],
        fields=["id", "name", "health_state", "write_date"],
        limit=6,
    )
    if not rows:
        rows = safe_search_read(
            env,
            "project.project",
            domain=[("health_state", "in", ["risk", "warn"])],
            fields=["id", "name", "health_state", "write_date"],
            limit=6,
        )
    if not rows:
        task_fields = ["id", "name", "project_id", "date_deadline", "write_date"]
        if model_has_field(env, "project.task", "sc_state"):
            task_fields.append("sc_state")
        if model_has_field(env, "project.task", "kanban_state"):
            task_fields.append("kanban_state")
        overdue_rows = safe_search_read(
            env,
            "project.task",
            domain=[("date_deadline", "<", fields.Datetime.now())],
            fields=task_fields,
            limit=6,
        )
        result: List[Dict[str, Any]] = []
        for row in overdue_rows:
            task_name = as_text(row.get("name")) or "逾期任务"
            project_name = ""
            project_raw = row.get("project_id")
            if isinstance(project_raw, list) and len(project_raw) > 1:
                project_name = as_text(project_raw[1])
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
        health = as_text(row.get("health_state"))
        status = "urgent" if health == "risk" else "normal"
        title = as_text(row.get("name")) or "风险事项"
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

def build_project_action_rows(env, user) -> List[Dict[str, Any]]:
    rows = safe_search_read(
        env,
        "project.project",
        domain=[("active", "=", True)],
        fields=["id", "name", "health_state", "lifecycle_state", "write_date", "user_id", "manager_id"],
        limit=6,
    )
    result: List[Dict[str, Any]] = []
    for row in rows:
        health = as_text(row.get("health_state"))
        lifecycle = as_text(row.get("lifecycle_state"))
        title = as_text(row.get("name")) or "项目事项"
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

def dictionary_fields(env) -> List[str]:
    fields_to_read = ["code", "name", "value_json", "sequence"]
    for field_name in ("scope_type", "scope_ref"):
        if model_has_field(env, "sc.dictionary", field_name):
            fields_to_read.append(field_name)
    return fields_to_read

def build_role_entry_contract_rows(env) -> List[Dict[str, Any]]:
    rows = safe_search_read(
        env,
        "sc.dictionary",
        domain=[("type", "=", "role_entry"), ("active", "=", True)],
        fields=dictionary_fields(env),
        limit=200,
    )
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        scope_type = as_text(row.get("scope_type")) or "global"
        scope_ref = as_text(row.get("scope_ref"))
        role_code = ""
        if scope_type == "role":
            role_code = scope_ref
        elif scope_type in {"global", "company"}:
            role_code = "__global__"
        if not role_code:
            continue

        value_json = row.get("value_json") if isinstance(row.get("value_json"), dict) else {}
        entry_key = (
            as_text(row.get("code"))
            or as_text(value_json.get("entry_key"))
            or as_text(row.get("name"))
        )
        if not entry_key:
            continue

        entry_type = as_text(value_json.get("entry_type")) or "menu"
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

def build_home_block_contract_rows(env) -> List[Dict[str, Any]]:
    rows = safe_search_read(
        env,
        "sc.dictionary",
        domain=[("type", "=", "home_block"), ("active", "=", True)],
        fields=dictionary_fields(env),
        limit=200,
    )
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        scope_type = as_text(row.get("scope_type")) or "global"
        scope_ref = as_text(row.get("scope_ref"))
        role_code = ""
        if scope_type == "role":
            role_code = scope_ref
        elif scope_type == "global":
            role_code = "__global__"
        if not role_code:
            continue

        value_json = row.get("value_json") if isinstance(row.get("value_json"), dict) else {}
        block_key = (
            as_text(row.get("code"))
            or as_text(value_json.get("block_key"))
            or as_text(row.get("name"))
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

def apply_system_init_profile_overrides(data: dict) -> dict:
    ext_facts = data.get("ext_facts")
    if not isinstance(ext_facts, dict):
        ext_facts = {}
    workspace_keyword_overrides = ext_facts.get("workspace_keyword_overrides")
    if not isinstance(workspace_keyword_overrides, dict):
        workspace_keyword_overrides = {}
    business_action_scene_labels = dict(
        workspace_keyword_overrides.get("business_action_scene_labels")
        if isinstance(workspace_keyword_overrides.get("business_action_scene_labels"), dict)
        else {}
    )
    business_action_scene_labels.update(
        {
            "finance.payment_requests": "支付申请",
            "project.management": "项目管理",
            "projects.dashboard": "项目管理",
            "risk.center": "风险中心",
            "workspace.risk": "风险中心",
        }
    )
    token_labels = list(
        workspace_keyword_overrides.get("business_action_title_token_labels")
        if isinstance(workspace_keyword_overrides.get("business_action_title_token_labels"), list)
        else []
    )
    token_labels.extend(
        [
            {"token": "支付", "label": "支付申请"},
            {"token": "项目", "label": "项目管理"},
            {"token": "风险", "label": "风险中心"},
        ]
    )
    token_sets = dict(
        workspace_keyword_overrides.get("token_sets")
        if isinstance(workspace_keyword_overrides.get("token_sets"), dict)
        else {}
    )
    token_sets.update(
        {
            "build_urgent_capability_tokens": [
                "risk",
                "approval",
                "payment",
                "settlement",
                "风险",
                "审批",
                "支付",
                "结算",
            ],
            "build_risk_semantic_tokens": [
                "risk",
                "alert",
                "warning",
                "exception",
                "overdue",
                "blocked",
                "critical",
                "urgent",
                "payment",
                "cost",
                "contract",
                "delay",
                "风险",
                "预警",
                "异常",
                "逾期",
                "阻塞",
                "严重",
                "紧急",
                "支付",
                "成本",
                "合同",
                "延期",
            ],
        }
    )
    source_scene_routes = dict(
        workspace_keyword_overrides.get("source_scene_routes")
        if isinstance(workspace_keyword_overrides.get("source_scene_routes"), dict)
        else {}
    )
    source_scene_routes.update(
        {
            "cost": "workspace.cost",
            "boq": "workspace.cost",
            "成本": "workspace.cost",
            "payment": "workspace.home",
            "finance": "workspace.home",
            "支付": "workspace.home",
            "财务": "workspace.home",
            "project": "workspace.list",
            "项目": "workspace.list",
        }
    )
    workspace_keyword_overrides["business_action_scene_labels"] = business_action_scene_labels
    workspace_keyword_overrides["business_action_title_token_labels"] = token_labels
    workspace_keyword_overrides["token_sets"] = token_sets
    workspace_keyword_overrides["source_scene_routes"] = source_scene_routes
    workspace_keyword_overrides["extension_collection_keys"] = [
        "today_actions",
        "tasks",
        "project_actions",
        "task_items",
        "payment_requests",
        "risk_actions",
        "risk",
        "project_tasks",
    ]
    workspace_keyword_overrides["preferred_business_sources"] = [
        "today_actions",
        "tasks",
        "project_actions",
        "task_items",
        "payment_requests",
        "risk_actions",
        "risk",
        "project_tasks",
    ]
    ext_facts["workspace_keyword_overrides"] = workspace_keyword_overrides
    page_profile_overrides = ext_facts.get("page_profile_overrides")
    if not isinstance(page_profile_overrides, dict):
        page_profile_overrides = {}
    page_texts = page_profile_overrides.get("page_texts") if isinstance(page_profile_overrides.get("page_texts"), dict) else {}
    login_texts = dict(page_texts.get("login") if isinstance(page_texts.get("login"), dict) else {})
    login_texts.update(
        {
            "brand_name": "智能施工企业管理平台",
            "brand_subtitle": "工程项目全生命周期管理系统",
            "brand_slogan": "让项目透明 · 让合同可控 · 让资金协同 · 让风险可预警",
            "capability_project": "项目全过程管理",
            "capability_contract_cost": "合同成本联动",
            "capability_fund": "资金支付协同",
            "capability_risk": "风险预警驾驶舱",
            "value_line_1": "让项目透明",
            "value_line_2": "让合同可控",
            "value_line_3": "让资金协同",
            "value_line_4": "让风险可预警",
        }
    )
    home_texts = dict(page_texts.get("home") if isinstance(page_texts.get("home"), dict) else {})
    home_texts.update(
        {
            "hero_lead": "围绕项目经营、风险与审批，优先处理今天最关键事项。",
            "todo_label_approval": "审核付款申请",
            "todo_label_contract": "查看合同异常",
            "todo_keywords_approval": "付款,支付,approval,审批",
            "todo_keywords_contract": "合同,contract",
            "action_enter_approval": "审核付款申请",
            "action_enter_contract": "查看合同异常",
            "action_enter_keywords_approval": "payment,付款,支付,approval,审批",
            "action_enter_keywords_contract": "contract,合同",
        }
    )
    my_work_texts = dict(page_texts.get("my_work") if isinstance(page_texts.get("my_work"), dict) else {})
    my_work_texts.update(
        {
            "action_view_project": "查看项目",
            "model_label_project_task": "项目任务",
            "model_label_project_project": "项目主数据",
        }
    )
    action_texts = dict(page_texts.get("action") if isinstance(page_texts.get("action"), dict) else {})
    action_texts.update(
        {
            "intent_title_contract": "合同执行：优先识别付款与变更风险",
            "intent_summary_contract": "先看执行率与付款状态，再进入异常合同处理。",
            "intent_action_contract_todo": "处理合同待办",
            "empty_title_contract": "当前暂无合同记录",
            "empty_hint_contract": "可前往“我的工作”查看合同待办，或进入风险驾驶舱追踪履约风险。",
            "primary_action_contract": "处理合同待办",
            "intent_title_project": "项目视角：先判断是否可控",
            "intent_action_project_todo": "查看项目待办",
            "empty_title_project": "当前暂无项目记录",
            "empty_hint_project": "建议进入“我的工作”处理项目待办，或去风险驾驶舱查看全局状态。",
            "primary_action_project": "查看项目待办",
            "empty_reason_wbs": "当前尚未生成执行结构数据，可先在项目立项或工程结构中创建后再查看。",
            "intent_title_cost": "成本执行：先回答是否超支",
            "intent_summary_cost": "优先关注超支金额与超支项，再下钻到具体偏差来源。",
            "intent_action_cost_todo": "处理成本待办",
            "empty_title_cost": "当前暂无成本记录",
            "empty_hint_cost": "可前往“我的工作”处理成本待办，或进入风险驾驶舱继续巡检。",
            "primary_action_cost": "处理超支待办",
            "surface_kind_keywords_contract": "contract,合同",
            "surface_kind_keywords_cost": "cost,成本",
            "surface_kind_keywords_project": "project,项目",
            "columns_contract_bucket_amount": "amount_total,contract_amount,金额,合同额",
            "columns_contract_bucket_payment": "paid,payment,付款,支付",
            "columns_contract_bucket_identity": "title,name,合同",
            "columns_cost_bucket_overrun": "over,overrun,超支,偏差",
            "columns_cost_bucket_identity": "title,name,项目",
            "columns_project_bucket_identity": "title,name,项目",
            "columns_project_bucket_payment": "payment,付款",
            "columns_project_bucket_cost": "cost,成本",
        }
    )
    record_texts = dict(page_texts.get("record") if isinstance(page_texts.get("record"), dict) else {})
    record_texts.update(
        {
            "summary_status_stage": "项目执行阶段",
            "next_action_contract": "查看合同",
            "next_action_cost": "查看成本",
            "fallback_details_title": "项目详情",
            "project_pay_prefix": "付款比 ",
            "project_pay_unset": "付款比未配置",
        }
    )
    page_texts.update({"login": login_texts, "home": home_texts, "my_work": my_work_texts, "action": action_texts, "record": record_texts})
    page_profile_overrides["page_texts"] = page_texts
    ext_facts["page_profile_overrides"] = page_profile_overrides
    data["ext_facts"] = ext_facts
    return data
