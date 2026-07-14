# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from copy import deepcopy
from typing import Any, Optional

from ..core.intent_execution_result import IntentExecutionResult
from ..core.request_params import parse_positive_int
from ..utils.extension_hooks import call_extension_hook_first


def v2_policy_projection_source_authority(
    *,
    source_kind: str,
    no_business_fact_authority: bool,
    runtime_carrier: str,
    source_key: str,
) -> dict[str, Any]:
    return {
        "kind": source_kind,
        "runtime_carrier": runtime_carrier,
        "projection_only": True,
        "no_business_fact_authority": no_business_fact_authority,
        "formal_projection": True,
        "fact_authority": "source_contract_projection",
        "source_key": source_key,
    }


def v2_policy_projection(
    value: dict[str, Any],
    *,
    source_kind: str,
    no_business_fact_authority: bool,
    runtime_carrier: str,
    source_key: str,
) -> dict[str, Any]:
    projection = deepcopy(value or {})
    projection["sourceAuthority"] = v2_policy_projection_source_authority(
        source_kind=source_kind,
        no_business_fact_authority=no_business_fact_authority,
        runtime_carrier=runtime_carrier,
        source_key=source_key,
    )
    return projection


def params_from_payload(payload: Any, fallback_params: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        nested = payload.get("params")
        if isinstance(nested, dict):
            merged = dict(payload)
            merged.update(nested)
            return merged
        return dict(payload)
    if isinstance(fallback_params, dict):
        return dict(fallback_params)
    return {}


def headers_from_request(request: Any, logger: Any = None) -> dict[str, Any]:
    try:
        http_request = getattr(request, "httprequest", None)
        headers = getattr(http_request, "headers", None)
        if headers:
            return dict(headers)
    except Exception:
        if logger is not None:
            logger.debug("failed to read ui.contract.v2 request headers", exc_info=True)
    return {}


def trim_limit_params(params: dict[str, Any]) -> tuple[dict[str, Optional[int]], Optional[str]]:
    out: dict[str, Optional[int]] = {}
    for output_key, snake_key, camel_key in (
        ("max_widgets", "max_widgets", "maxWidgets"),
        ("max_actions", "max_actions", "maxActions"),
        ("max_containers", "max_containers", "maxContainers"),
    ):
        raw = params.get(snake_key) if snake_key in params else params.get(camel_key)
        value, error = parse_positive_int(raw, allow_empty=True)
        if error:
            return {}, snake_key
        out[output_key] = value
    return out, None


def ui_contract_params(params: dict[str, Any]) -> dict[str, Any]:
    ui_params = dict(params)
    ui_params.pop("source_type", None)
    ui_params.pop("sourceType", None)
    ui_params.pop("client_type", None)
    ui_params.pop("clientType", None)
    ui_params.setdefault("source_mode", "backend_internal")
    ui_params.setdefault("contract_surface", "user")
    if not ui_params.get("op") and not ui_params.get("subject"):
        if ui_params.get("menu_id") or ui_params.get("menuId") or ui_params.get("id"):
            ui_params["op"] = "menu"
        elif ui_params.get("action_id") or ui_params.get("actionId"):
            ui_params["op"] = "action_open"
        elif ui_params.get("model") or ui_params.get("model_code") or ui_params.get("modelCode"):
            ui_params["op"] = "model"
    op = str(ui_params.get("op") or ui_params.get("subject") or "").strip().lower()
    view_type = str(ui_params.get("view_type") or ui_params.get("viewType") or "").strip().lower()
    if view_type == "list":
        ui_params["view_type"] = "tree"
        if "viewType" in ui_params:
            ui_params["viewType"] = "tree"
        view_type = "tree"
    record_id = ui_params.get("record_id") or ui_params.get("recordId") or ui_params.get("res_id") or ui_params.get("resId")
    if op == "model" and view_type in {"form", ""} and record_id and "with_data" not in ui_params:
        ui_params["with_data"] = True
    return ui_params


def envelope(result: Any) -> dict[str, Any]:
    if isinstance(result, IntentExecutionResult):
        return result.to_legacy_dict()
    if isinstance(result, dict):
        return result
    return {"ok": True, "data": result or {}, "meta": {}}


def error_result(
    *,
    code: int,
    message: str,
    intent_type: str,
    version: str,
    contract_version: str,
    source_authority: dict[str, Any],
) -> IntentExecutionResult:
    return IntentExecutionResult(
        ok=False,
        error={"code": code, "message": message},
        meta={
            "intent": intent_type,
            "version": version,
            "contract_version": contract_version,
            "source_authority": source_authority,
        },
        code=code,
    )


def safe_eval_action_value(value: Any, default: Any) -> Any:
    if value in (None, False, ""):
        return default
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return default
    try:
        from odoo.tools.safe_eval import safe_eval

        return safe_eval(text)
    except Exception:
        try:
            return ast.literal_eval(text)
        except Exception:
            return default


def allowed_models_from_hook(env: Any, hook_name: str) -> set[str]:
    try:
        payload = call_extension_hook_first(env, hook_name, env)
    except Exception:
        payload = None
    if not isinstance(payload, (list, tuple, set)):
        return set()
    return {str(item).strip() for item in payload if str(item).strip()}


def standard_chatter_actions(*, message_capable: bool, activity_capable: bool) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if message_capable:
        actions.extend([
            {
                "key": "chatter_send_message",
                "label": "记录沟通",
                "kind": "chatter",
                "level": "chatter",
                "selection": "none",
                "intent": "message",
                "payload": {"mode": "message"},
            },
            {
                "key": "chatter_log_note",
                "label": "记录备注",
                "kind": "chatter",
                "level": "chatter",
                "selection": "none",
                "intent": "note",
                "payload": {"mode": "note"},
            },
        ])
    if activity_capable:
        actions.append({
            "key": "chatter_schedule_activity",
            "label": "活动",
            "kind": "chatter",
            "level": "chatter",
            "selection": "none",
            "intent": "activity",
            "payload": {
                "mode": "activity",
                "execute_intent": "chatter.activity.schedule",
                "activity_type_xmlid": "mail.mail_activity_data_todo",
                "fields": [
                    {"name": "summary", "label": "摘要", "type": "char", "required": True},
                    {"name": "date_deadline", "label": "截止日期", "type": "date", "required": False},
                    {"name": "note", "label": "备注", "type": "text", "required": False},
                ],
            },
        })
    return actions
