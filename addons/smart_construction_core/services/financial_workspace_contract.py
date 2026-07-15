# -*- coding: utf-8 -*-
"""Authoritative read-only contract for the core financial relationship workspace."""

from __future__ import annotations

from copy import deepcopy

from ..models.support import operating_metrics as opm


WORKSPACE_DECLARATIONS = {
    "project.project": {
        "kind": "project",
        "facts": [
            ("company_id", "公司", "relation"),
            ("partner_id", "往来方", "relation"),
        ],
        "relations": [
            {
                "key": "contracts",
                "label": "合同",
                "model": "construction.contract",
                "menu_xmlid": "smart_construction_core.menu_sc_construction_contract",
                "domain_field": "project_id",
                "identity_fields": ("name", "subject"),
            },
        ],
        "details": [],
    },
    "construction.contract": {
        "kind": "contract",
        "facts": [
            ("amount_total", "合同原始金额", "money"),
            ("amount_final", "当前 / 最终金额", "money"),
            ("paid_amount", "合同累计实付", "money"),
            ("company_id", "公司", "relation"),
            ("project_id", "项目", "relation"),
            ("partner_id", "往来方", "relation"),
            ("date_contract", "合同订立日期", "date"),
        ],
        "relations": [
            {
                "key": "project",
                "label": "项目",
                "field": "project_id",
                "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                "identity_fields": ("name",),
            },
            {
                "key": "settlements",
                "label": "结算",
                "model": "sc.settlement.order",
                "menu_xmlid": "smart_construction_core.menu_sc_settlement_order",
                "domain_field": "contract_id",
                "identity_fields": ("name", "title"),
            },
        ],
        "details": [
            {
                "key": "contract_lines",
                "label": "合同明细",
                "field": "line_ids",
                "columns": (("note", "明细", "text"), ("qty_contract", "数量", "number"), ("price_contract", "单价", "money"), ("amount_contract", "金额", "money")),
            },
        ],
    },
    "sc.settlement.order": {
        "kind": "settlement",
        "facts": [
            ("amount_total", "原始结算金额", "money"),
            ("deduction_amount", "调整 / 扣款金额", "money"),
            ("amount_after_adjustment", "调整后付款基数", "money"),
            ("__settlement_reserved", "已占额", "money"),
            ("__settlement_actual_paid", "实际已付", "money"),
            ("__settlement_remaining", "剩余可占额", "money"),
            ("company_id", "公司", "relation"),
            ("project_id", "项目", "relation"),
            ("partner_id", "往来方", "relation"),
            ("date_settlement", "结算日期", "date"),
        ],
        "relations": [
            {
                "key": "contract",
                "label": "合同",
                "field": "contract_id",
                "menu_xmlid": "smart_construction_core.menu_sc_construction_contract",
                "identity_fields": ("name", "subject"),
            },
            {
                "key": "payment_requests",
                "label": "付款申请",
                "field": "payment_request_ids",
                "menu_xmlid": "smart_construction_core.menu_sc_user_payment_apply_acceptance",
                "identity_fields": ("name",),
            },
        ],
        "details": [
            {
                "key": "settlement_lines",
                "label": "结算明细",
                "field": "line_ids",
                "columns": (("name", "明细", "text"), ("qty", "数量", "number"), ("price_unit", "单价", "money"), ("amount", "金额", "money")),
            },
        ],
    },
    "payment.request": {
        "kind": "payment_request",
        "facts": [
            ("amount", "申请金额", "money"),
            ("__request_reserved", "对结算占额", "money"),
            ("paid_amount_total", "实际台账金额", "money"),
            ("company_id", "公司", "relation"),
            ("project_id", "项目", "relation"),
            ("partner_id", "往来方", "relation"),
            ("date_request", "申请日期", "date"),
        ],
        "relations": [
            {
                "key": "contract",
                "label": "合同",
                "field": "contract_id",
                "menu_xmlid": "smart_construction_core.menu_sc_construction_contract",
                "identity_fields": ("name", "subject"),
            },
            {
                "key": "settlement",
                "label": "结算",
                "field": "settlement_id",
                "menu_xmlid": "smart_construction_core.menu_sc_settlement_order",
                "identity_fields": ("name", "title"),
            },
            {
                "key": "executions",
                "label": "付款执行",
                "model": "sc.payment.execution",
                "menu_xmlid": "smart_construction_core.menu_sc_payment_execution",
                "domain_field": "payment_request_id",
                "identity_fields": ("name", "document_no"),
            },
            {
                "key": "ledgers",
                "label": "实付 / 台账结果",
                "field": "ledger_line_ids",
                "identity_fields": ("ref",),
                "inline_only": True,
            },
        ],
        "details": [],
    },
    "sc.payment.execution": {
        "kind": "payment_execution",
        "facts": [
            ("planned_amount", "执行金额", "money"),
            ("paid_amount", "实际支付结果", "money"),
            ("company_id", "公司", "relation"),
            ("project_id", "项目", "relation"),
            ("partner_id", "往来方", "relation"),
            ("date_payment", "付款日期", "date"),
        ],
        "relations": [
            {
                "key": "payment_request",
                "label": "付款申请",
                "field": "payment_request_id",
                "menu_xmlid": "smart_construction_core.menu_sc_user_payment_apply_acceptance",
                "identity_fields": ("name",),
            },
            {
                "key": "contract",
                "label": "合同",
                "field": "contract_id",
                "menu_xmlid": "smart_construction_core.menu_sc_construction_contract",
                "identity_fields": ("name", "subject"),
            },
            {
                "key": "ledgers",
                "label": "实付 / 台账结果",
                "via_field": "payment_request_id",
                "target_field": "ledger_line_ids",
                "identity_fields": ("ref",),
                "inline_only": True,
            },
        ],
        "details": [],
    },
}


def inject_financial_workspace_runtime(env, contract, source, head, context, model, view_type, action_builder):
    """Attach the financial projection to V2 without teaching the platform assembler industry semantics."""
    params = ((context.get("meta") or {}).get("params") or {}) if isinstance(context, dict) else {}
    try:
        record_id = int(source.get("record_id") or source.get("res_id") or head.get("record_id")
                        or head.get("res_id") or params.get("record_id") or params.get("recordId") or 0)
    except (TypeError, ValueError):
        record_id = 0
    if not model or view_type != "form" or record_id <= 0:
        return
    payload = action_builder(env, model, record_id, source)
    if not isinstance(payload, dict):
        return
    runtime = dict(contract.get("runtimeContract") or {})
    if isinstance(payload.get("business_workspace"), dict):
        runtime["businessWorkspace"] = deepcopy(payload["business_workspace"])
    if isinstance(payload.get("actions"), list):
        runtime["businessActions"] = deepcopy(payload["actions"])
    contract["runtimeContract"] = runtime


def _text(value):
    return str(value or "").strip()


def _safe_record(record):
    if not record or not record.exists():
        return None
    try:
        record.check_access_rule("read")
        record.read(["display_name"])
    except Exception:
        return None
    return record


def _identity(record, fields):
    for field_name in fields or ():
        if field_name in record._fields:
            value = _text(record[field_name])
            if value and value not in {"New", "新建"}:
                return value
    return _text(record.display_name) or _text(record._description)


def _currency_payload(currency):
    if not currency:
        return None
    return {
        "id": int(currency.id),
        "name": _text(currency.name),
        "symbol": _text(currency.symbol),
        "position": _text(currency.position) or "before",
        "decimal_places": int(currency.decimal_places or 2),
    }


def _relation_value(record):
    if not record:
        return ""
    readable = _safe_record(record)
    return _text(readable.display_name) if readable else "无权查看"


def _metric_value(record, key):
    if key == "__settlement_reserved":
        return opm.settlement_reserved_amount_map(record.env, record.ids).get(record.id, 0.0)
    if key == "__settlement_actual_paid":
        return opm.settlement_actual_paid_amount_map(record.env, record.ids).get(record.id, 0.0)
    if key == "__settlement_remaining":
        reserved = opm.settlement_reserved_amount_map(record.env, record.ids).get(record.id, 0.0)
        return opm.settlement_remaining_reservable_amount(record, reserved)
    if key == "__request_reserved":
        return (record.amount or 0.0) if record.state in opm.get_reserved_states() else 0.0
    return None


def _fact(record, field_name, label, kind):
    currency = record.currency_id if "currency_id" in record._fields else None
    if field_name.startswith("__"):
        value = _metric_value(record, field_name)
    elif field_name not in record._fields:
        return None
    else:
        raw = record[field_name]
        value = _relation_value(raw) if kind == "relation" else raw
    if hasattr(value, "isoformat"):
        value = value.isoformat()
    return {
        "key": field_name.lstrip("_"),
        "label": label,
        "kind": kind,
        "value": value if value is not False else None,
        "currency": _currency_payload(currency) if kind == "money" else None,
    }


def _route_target(env, menu_xmlid, model_name, record_id):
    if not menu_xmlid:
        return None
    menu = env.ref(menu_xmlid, raise_if_not_found=False)
    menu = menu.sudo() if menu else menu
    action = menu.action if menu else None
    if not menu or not action or _text(getattr(action, "res_model", "")) != model_name:
        return None
    return {
        "name": "record",
        "params": {"model": model_name, "id": int(record_id)},
        "query": {"menu_id": int(menu.id), "action_id": int(action.id)},
    }


def _safe_related_records(record, declaration):
    try:
        if declaration.get("field"):
            raw = record[declaration["field"]] if declaration["field"] in record._fields else record.env[record._name]
            candidates = raw
        elif declaration.get("via_field"):
            via = record[declaration["via_field"]] if declaration["via_field"] in record._fields else None
            candidates = via[declaration["target_field"]] if via and declaration["target_field"] in via._fields else record.env[record._name]
        else:
            model_name = declaration.get("model")
            domain_field = declaration.get("domain_field")
            candidates = record.env[model_name].search([(domain_field, "=", record.id)], order="id desc", limit=80)
    except Exception:
        return []
    safe = []
    for candidate in candidates:
        readable = _safe_record(candidate)
        if readable:
            safe.append(readable)
    return safe


def _relationship(env, record, declaration):
    rows = []
    for related in _safe_related_records(record, declaration):
        inline_only = bool(declaration.get("inline_only"))
        currency = related.currency_id if "currency_id" in related._fields else None
        amount = related.amount if related._name == "payment.ledger" and "amount" in related._fields else None
        rows.append({
            "model": related._name,
            "id": int(related.id),
            "label": _identity(related, declaration.get("identity_fields")),
            "route": None if inline_only else _route_target(env, declaration.get("menu_xmlid"), related._name, related.id),
            "inline_only": inline_only,
            "amount": amount,
            "currency": _currency_payload(currency),
            "date": related.paid_at.isoformat() if related._name == "payment.ledger" and related.paid_at else None,
            "status": _text(related.state) if "state" in related._fields else "",
        })
    return {
        "key": declaration["key"],
        "label": declaration["label"],
        "empty_text": "暂无%s" % declaration["label"],
        "records": rows,
    }


def _detail_section(record, declaration):
    rows = []
    try:
        relation = record[declaration["field"]] if declaration["field"] in record._fields else record.env[record._name]
    except Exception:
        relation = record.env[record._name]
    for line in relation:
        if not _safe_record(line):
            continue
        cells = []
        for field_name, label, kind in declaration["columns"]:
            if field_name not in line._fields:
                continue
            raw = line[field_name]
            value = _relation_value(raw) if getattr(raw, "_name", "") else raw
            currency = line.currency_id if kind == "money" and "currency_id" in line._fields else (
                record.currency_id if kind == "money" and "currency_id" in record._fields else None
            )
            cells.append({
                "key": field_name,
                "label": label,
                "kind": kind,
                "value": value if value is not False else None,
                "currency": _currency_payload(currency),
            })
        rows.append({"key": str(line.id), "cells": cells})
    return {"key": declaration["key"], "label": declaration["label"], "rows": rows, "empty_text": "暂无%s" % declaration["label"]}


def build_financial_workspace_contract(env, model_name, record_id):
    declaration = WORKSPACE_DECLARATIONS.get(_text(model_name))
    if not declaration:
        return None
    try:
        record = _safe_record(env[model_name].browse(int(record_id or 0)))
    except Exception:
        record = None
    if not record:
        return None
    state_value = record.state if "state" in record._fields else ""
    state_label = state_value
    if "state" in record._fields and record._fields["state"].type == "selection":
        state_label = dict(record._fields["state"]._description_selection(env)).get(state_value, state_value)
    currency = record.currency_id if "currency_id" in record._fields else None
    facts = [
        item
        for field_name, label, kind in declaration["facts"]
        if (item := _fact(record, field_name, label, kind)) is not None
    ]
    relationships = [_relationship(env, record, item) for item in declaration["relations"]]
    primary_currency_id = int(currency.id) if currency else 0
    related_currency_names = sorted({
        _text(row.get("currency", {}).get("name"))
        for relationship in relationships
        for row in relationship["records"]
        if row.get("currency")
        and int(row["currency"].get("id") or 0) != primary_currency_id
        and _text(row["currency"].get("name"))
    })
    currency_mismatch = bool(primary_currency_id and related_currency_names)
    return {
        "version": "1.0",
        "kind": declaration["kind"],
        "model": record._name,
        "record_id": int(record.id),
        "record_label": _identity(record, ("name", "subject", "title")),
        "state": {"value": _text(state_value), "label": _text(state_label)},
        "currency": _currency_payload(currency),
        "facts": facts,
        "relationships": relationships,
        "details": [_detail_section(record, item) for item in declaration["details"]],
        "audit": [
            _fact(record, field_name, label, kind)
            for field_name, label, kind in (
                ("create_uid", "创建人", "relation"),
                ("create_date", "创建时间", "datetime"),
                ("write_uid", "更新人", "relation"),
                ("write_date", "更新时间", "datetime"),
            )
            if field_name in record._fields
        ],
        "currency_risk": {
            "mismatch": currency_mismatch,
            "message": (
                "当前记录为%s，关联记录包含%s；系统未执行隐式换算。"
                % (_text(currency.name), "、".join(related_currency_names))
            ) if currency_mismatch else "",
        },
        "source": {
            "kind": "financial_workspace_read_projection",
            "authorities": [record._name, "ir.model.access", "ir.rule", "operating_metrics"],
            "projection_only": True,
        },
    }


def build_financial_form_business_actions(env, model_name, record_id):
    """Combine authoritative payment actions with the read-only financial workspace."""
    model = str(model_name or "").strip()
    workspace = build_financial_workspace_contract(env, model, record_id)
    if model != "payment.request":
        return {"actions": [], "business_workspace": workspace} if workspace else None
    record = env[model].browse(int(record_id or 0)).exists()
    if not record:
        return None
    from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
        PaymentRequestAvailableActionsHandler,
    )
    result = PaymentRequestAvailableActionsHandler(env, payload={"id": int(record.id)}).run(
        payload={"id": int(record.id)}
    )
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
        for method in filter(None, methods):
            label = str(row.get("label") or action_key)
            actions.append({
                "key": f"payment_{action_key}", "action_key": action_key, "label": label,
                "kind": "mutation", "level": "header", "source_widget_id": "page.header",
                "selection": "none", "visible_profiles": ["edit", "readonly"], "method": method,
                "intent": str(row.get("execute_intent") or row.get("intent") or "payment.request.execute"),
                "allowed": bool(row.get("allowed")), "reason_code": str(row.get("reason_code") or ""),
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
                "required_params": list(row.get("required_params") or []), "primary": action_key == primary_key,
                "action_safety": {"classification": "danger", "requires_confirm": True,
                                  "confirm_message": f"确认{label}后，系统将重新读取付款申请及上下游金额状态。",
                                  "reason_code": "BUSINESS_STATE_TRANSITION"},
                "mutation": {"type": "record_action", "model": "payment.request", "operation": action_key,
                             "payload_schema": {"id": "record_id",
                                                "reason": "string" if bool(row.get("requires_reason")) else ""}},
                "refresh_policy": {"on_success": ["scene_projection"], "mode": "reload_record", "scope": "record"},
            })
    return {
        "actions": actions,
        "attachments": {
            "enabled": True, "label": "附件",
            "upload": {"intent": "file.upload", "max_bytes": 5 * 1024 * 1024, "accepted_types": []},
            "download": {"intent": "file.download"},
            "ui_labels": {"upload": "上传附件", "uploading": "上传中...", "download": "下载",
                          "upload_failed": "附件上传失败", "download_failed": "附件下载失败", "size_exceeded": "文件过大"},
        },
        "business_workspace": workspace,
    }
