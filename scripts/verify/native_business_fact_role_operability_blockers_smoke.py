#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import time

from python_http_smoke_utils import get_base_url, http_post_json


def _intent(
    intent_url: str,
    token: str | None,
    intent: str,
    params: dict | None = None,
    anonymous: bool = False,
    context: dict | None = None,
):
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    payload = {"intent": intent, "params": params or {}}
    if isinstance(context, dict) and context:
        payload["context"] = context
    return http_post_json(intent_url, payload, headers=headers)


def _expect_ok(label: str, status: int, payload: dict) -> None:
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, payload = _intent(
        intent_url,
        None,
        "login",
        {"db": db_name, "login": login, "password": password},
        anonymous=True,
    )
    _expect_ok(f"login:{login}", status, payload)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if not token:
        session = data.get("session") if isinstance(data.get("session"), dict) else {}
        token = str(session.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login:{login} token missing")
    return token


def _api_data(intent_url: str, token: str, op: str, model: str, context: dict | None = None, **kwargs):
    params = {"op": op, "model": model}
    params.update(kwargs)
    return _intent(intent_url, token, "api.data", params, context=context)


def _first_id(intent_url: str, token: str, model: str, fields: list[str], domain: list | None = None) -> int:
    st, body = _api_data(intent_url, token, "list", model, fields=fields, domain=domain or [], limit=1, order="id desc")
    if st >= 400 or body.get("ok") is not True:
        return 0
    rows = (((body.get("data") or {}).get("records")) or [])
    if not rows or not isinstance(rows[0], dict):
        return 0
    try:
        return int(rows[0].get("id") or 0)
    except Exception:
        return 0


def _ensure_refs(intent_url: str, admin_token: str) -> dict[str, int]:
    refs: dict[str, int] = {}
    project_id = _first_id(intent_url, admin_token, "project.project", ["id", "name"])
    if project_id <= 0:
        st, body = _api_data(intent_url, admin_token, "create", "project.project", vals={"name": f"NBF-REF-{int(time.time())}"})
        _expect_ok("create ref project.project", st, body)
        project_id = int((((body.get("data") or {}).get("id")) or 0))
    partner_id = _first_id(intent_url, admin_token, "res.partner", ["id", "name"], [["active", "=", True]])
    currency_id = _first_id(intent_url, admin_token, "res.currency", ["id", "name"], [["active", "=", True]])
    cost_code_id = _first_id(intent_url, admin_token, "project.cost.code", ["id", "name"])
    if cost_code_id <= 0:
        st_imd, body_imd = _api_data(
            intent_url,
            admin_token,
            "list",
            "ir.model.data",
            fields=["id", "res_id", "module", "name", "model"],
            domain=[
                ["module", "=", "smart_construction_custom"],
                ["name", "=", "project_cost_code_sc_seed_root"],
                ["model", "=", "project.cost.code"],
            ],
            limit=1,
        )
        if st_imd < 400 and isinstance(body_imd, dict) and body_imd.get("ok") is True:
            rows = (((body_imd.get("data") or {}).get("records")) or [])
            if rows and isinstance(rows[0], dict):
                try:
                    cost_code_id = int(rows[0].get("res_id") or 0)
                except Exception:
                    cost_code_id = 0
    if cost_code_id <= 0:
        raise RuntimeError("reference ids missing: cost_code_id (seed/xmlid required)")

    refs.update(
        {
            "project_id": int(project_id),
            "partner_id": int(partner_id),
            "currency_id": int(currency_id),
            "cost_code_id": int(cost_code_id),
        }
    )
    missing = [k for k, v in refs.items() if int(v or 0) <= 0]
    if missing:
        raise RuntimeError(f"reference ids missing: {','.join(missing)}")
    return refs


def _role_project_id(intent_url: str, token: str) -> int:
    return _first_id(intent_url, token, "project.project", ["id", "name"])


def _ui_contract(intent_url: str, token: str, model: str, view_type: str):
    return _intent(intent_url, token, "ui.contract", {"op": "model", "model": model, "view_type": view_type})


def _pick_button(contract_payload: dict) -> dict | None:
    data = contract_payload.get("data") if isinstance(contract_payload.get("data"), dict) else {}
    buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    primary: dict | None = None
    fallback: dict | None = None
    for button in buttons:
        if not isinstance(button, dict):
            continue
        intent_name = str(button.get("intent") or "").strip()
        params = button.get("params") if isinstance(button.get("params"), dict) else None
        if intent_name and isinstance(params, dict):
            picked = dict(button)
            picked["params"] = dict(params)
            if intent_name.lower() in {"open", "navigate"}:
                fallback = picked
                continue
            primary = picked
            break
    return primary or fallback


def _create_vals(model: str, refs: dict[str, int], suffix: str, role_project_id: int) -> tuple[dict, str]:
    selected_project_id = int(role_project_id or refs.get("project_id") or 0)
    if selected_project_id <= 0:
        raise RuntimeError("project reference missing for role")
    if model == "project.project":
        return {"name": f"NBF-P-{suffix}"}, "name"
    if model == "project.task":
        return {"name": f"NBF-T-{suffix}", "project_id": selected_project_id}, "name"
    if model == "project.budget":
        return {"name": f"NBF-B-{suffix}", "project_id": selected_project_id}, "name"
    if model == "project.cost.ledger":
        return {
            "project_id": selected_project_id,
            "cost_code_id": refs["cost_code_id"],
            "period": time.strftime("%Y-%m"),
            "date": time.strftime("%Y-%m-%d"),
            "amount": 1.0,
            "note": f"NBF-C-{suffix}",
        }, "note"
    if model == "payment.request":
        return {
            "type": "pay",
            "project_id": selected_project_id,
            "partner_id": refs["partner_id"],
            "currency_id": refs["currency_id"],
            "amount": 1.0,
            "date_request": time.strftime("%Y-%m-%d"),
            "note": f"NBF-PR-{suffix}",
        }, "note"
    if model == "sc.settlement.order":
        return {
            "name": f"NBF-SO-{suffix}",
            "project_id": selected_project_id,
            "partner_id": refs["partner_id"],
            "currency_id": refs["currency_id"],
            "note": "native-business-fact-operability",
        }, "note"
    raise RuntimeError(f"unsupported model: {model}")


def _verify_model_operability(intent_url: str, token: str, model: str, refs: dict[str, int], detail: list[str], role_project_id: int) -> None:
    st_list, p_list = _ui_contract(intent_url, token, model, "list")
    _expect_ok(f"{model} ui.contract list", st_list, p_list)
    st_form, p_form = _ui_contract(intent_url, token, model, "form")
    _expect_ok(f"{model} ui.contract form", st_form, p_form)

    st_l, p_l = _api_data(intent_url, token, "list", model, fields=["id"], limit=1, order="id desc")
    _expect_ok(f"{model} api.data list", st_l, p_l)

    suffix = str(int(time.time() * 1000))[-8:]
    vals, write_key = _create_vals(model, refs, suffix, role_project_id)
    model_context = {"allow_transition": True} if model == "project.task" else None
    st_c, p_c = _api_data(intent_url, token, "create", model, vals=vals, context=model_context)
    _expect_ok(f"{model} api.data create", st_c, p_c)
    rec_id = int((((p_c.get("data") or {}).get("id")) or 0))
    if rec_id <= 0:
        raise RuntimeError(f"{model} create id missing")

    write_value = f"NBF-W-{suffix}"
    st_w, p_w = _api_data(intent_url, token, "write", model, ids=[rec_id], vals={write_key: write_value}, context=model_context)
    _expect_ok(f"{model} api.data write", st_w, p_w)

    button = _pick_button(p_form)
    if button:
        intent_name = str(button.get("intent") or "").strip()
        params = button.get("params") if isinstance(button.get("params"), dict) else {}
        if intent_name == "execute":
            button_name = str(button.get("name") or params.get("button_name") or params.get("method_name") or "").strip()
            if not button_name:
                detail.append(f"{model}:button=execute(no_name_skip)")
                return
            exec_params = {
                "model": str(params.get("model") or params.get("res_model") or model),
                "res_id": int(params.get("res_id") or params.get("id") or rec_id),
                "button": {
                    "name": button_name,
                    "type": str(button.get("type") or params.get("button_type") or "object"),
                },
            }
            st_b, p_b = _intent(intent_url, token, "execute_button", exec_params)
            _expect_ok(f"{model} button execute_button", st_b, p_b)
            detail.append(f"{model}:button=execute_button")
            return
        if intent_name.lower() in {"open", "navigate"}:
            detail.append(f"{model}:button={intent_name}(navigation_skip)")
            return
        call_params = dict(params)
        if "id" not in call_params and "res_id" not in call_params:
            call_params["id"] = rec_id
        st_b, p_b = _intent(intent_url, token, intent_name, call_params)
        _expect_ok(f"{model} button {intent_name}", st_b, p_b)
        detail.append(f"{model}:button={intent_name}")
    else:
        detail.append(f"{model}:button=none")


def main() -> None:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo").strip()

    admin_login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    admin_password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    admin_token = _login(intent_url, db_name, admin_login, admin_password)
    refs = _ensure_refs(intent_url, admin_token)

    role_matrix = [
        (
            "owner",
            str(os.getenv("ROLE_OWNER_LOGIN") or "demo_role_owner").strip(),
            str(os.getenv("ROLE_OWNER_PASSWORD") or "demo").strip(),
            ["project.project", "project.task", "project.budget", "project.cost.ledger"],
        ),
        (
            "pm",
            str(os.getenv("ROLE_PM_LOGIN") or "demo_role_pm").strip(),
            str(os.getenv("ROLE_PM_PASSWORD") or "demo").strip(),
            ["project.project", "project.task"],
        ),
        (
            "finance",
            str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(),
            str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip(),
            ["project.cost.ledger", "payment.request", "sc.settlement.order"],
        ),
    ]

    details: list[str] = []
    for role_key, login, password, models in role_matrix:
        role_token = _login(intent_url, db_name, login, password)
        role_project_id = _role_project_id(intent_url, role_token)
        for model in models:
            _verify_model_operability(intent_url, role_token, model, refs, details, role_project_id)
        details.append(f"{role_key}:{login}:{len(models)}")

    print(
        "[native_business_fact_role_operability_blockers_smoke] "
        f"PASS roles={len(role_matrix)} refs={refs} details={'|'.join(details)}"
    )


if __name__ == "__main__":
    main()
