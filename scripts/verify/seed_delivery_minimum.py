#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "delivery_minimum_seed_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "delivery_minimum_seed.json"


def _intent(intent_url: str, token: str | None, intent: str, params: dict | None = None, anonymous: bool = False):
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    return http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str]:
    status, payload = _intent(
        intent_url,
        None,
        "login",
        {"db": db_name, "login": login, "password": password},
        anonymous=True,
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, ""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    return bool(token), token


def _first_id(intent_url: str, token: str, model: str, fields: list[str], domain: list | None = None) -> int:
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {"op": "list", "model": model, "fields": fields, "domain": domain or [], "limit": 1, "order": "id desc"},
    )
    if status >= 400 or payload.get("ok") is not True:
        return 0
    rows = (((payload.get("data") or {}).get("records")) or [])
    if not rows or not isinstance(rows[0], dict):
        return 0
    try:
        return int(rows[0].get("id") or 0)
    except Exception:
        return 0


def _ensure_group_membership(intent_url: str, token: str, login: str, group_xmlid: str) -> bool:
    module, _, name = str(group_xmlid or "").partition(".")
    if not module or not name:
        return False
    user_id = _first_id(intent_url, token, "res.users", ["id", "login"], [["login", "=", login]])
    if user_id <= 0:
        return False
    group_id = _first_id(
        intent_url,
        token,
        "ir.model.data",
        ["id", "res_id", "module", "name", "model"],
        [["module", "=", module], ["name", "=", name], ["model", "=", "res.groups"]],
    )
    if group_id <= 0:
        return False
    # ir.model.data.res_id is target group id; read it
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {"op": "read", "model": "ir.model.data", "ids": [group_id], "fields": ["id", "res_id"]},
    )
    if status >= 400 or payload.get("ok") is not True:
        return False
    rows = (((payload.get("data") or {}).get("records")) or [])
    if not rows or not isinstance(rows[0], dict):
        return False
    try:
        target_group_id = int(rows[0].get("res_id") or 0)
    except Exception:
        target_group_id = 0
    if target_group_id <= 0:
        return False
    # 已有组关系时不重复写，避免无谓触发“修改自身权限”限制。
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {"op": "read", "model": "res.users", "ids": [user_id], "fields": ["id", "groups_id"]},
    )
    if status < 400 and payload.get("ok") is True:
        rows = (((payload.get("data") or {}).get("records")) or [])
        if rows and isinstance(rows[0], dict):
            raw_groups = rows[0].get("groups_id") or []
            group_ids: set[int] = set()
            if isinstance(raw_groups, list):
                for item in raw_groups:
                    if isinstance(item, int):
                        group_ids.add(item)
                    elif isinstance(item, (list, tuple)) and item:
                        try:
                            group_ids.add(int(item[0]))
                        except Exception:
                            continue
            if target_group_id in group_ids:
                return True
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {
            "op": "write",
            "model": "res.users",
            "ids": [user_id],
            "vals": {"groups_id": [[4, target_group_id]]},
        },
    )
    return status < 400 and payload.get("ok") is True


def _create_payment_request(intent_url: str, token: str, project_id: int, partner_id: int, contract_id: int) -> int:
    trial_types = ("pay", "receive")
    last_error = ""
    for req_type in trial_types:
        vals = {
            "type": req_type,
            "project_id": int(project_id),
            "partner_id": int(partner_id),
            "amount": 100.0,
            "state": "draft",
        }
        if contract_id > 0:
            vals["contract_id"] = int(contract_id)
        status, payload = _intent(
            intent_url,
            token,
            "api.data",
            {"op": "create", "model": "payment.request", "vals": vals},
        )
        if status >= 400 or payload.get("ok") is not True:
            last_error = f"create type={req_type} status={status} payload={payload}"
            continue
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        try:
            rec_id = int(data.get("id") or 0)
        except Exception:
            rec_id = 0
        if rec_id > 0:
            return rec_id
    _create_payment_request.last_error = last_error  # type: ignore[attr-defined]
    return 0


def _attach_minimum_file(intent_url: str, token: str, payment_request_id: int) -> bool:
    if payment_request_id <= 0:
        return False
    content = base64.b64encode(b"r8 delivery seed").decode("ascii")
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {
            "op": "create",
            "model": "ir.attachment",
            "vals": {
                "name": f"r8_seed_{payment_request_id}.txt",
                "type": "binary",
                "datas": content,
                "mimetype": "text/plain",
                "res_model": "payment.request",
                "res_id": int(payment_request_id),
            },
        },
    )
    return status < 400 and payload.get("ok") is True


def _available_action_keys(intent_url: str, token: str, payment_request_id: int) -> list[str]:
    status, payload = _intent(
        intent_url,
        token,
        "payment.request.available_actions",
        {"id": int(payment_request_id)},
    )
    if status >= 400 or payload.get("ok") is not True:
        return []
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    actions = data.get("actions") if isinstance(data.get("actions"), list) else []
    out: list[str] = []
    for item in actions:
        if not isinstance(item, dict) or not item.get("allowed"):
            continue
        key = str(item.get("key") or "").strip().lower()
        if key:
            out.append(key)
    return out


def _find_submit_candidate(intent_url: str, token: str, limit: int = 30) -> tuple[int, str]:
    status, payload = _intent(
        intent_url,
        token,
        "api.data",
        {
            "op": "list",
            "model": "payment.request",
            "fields": ["id", "state"],
            "limit": int(limit),
            "order": "id desc",
        },
    )
    if status >= 400 or payload.get("ok") is not True:
        # fallback: probe known ID range when list access is blocked
        for rec_id in range(1, 201):
            actions = _available_action_keys(intent_url, token, rec_id)
            if "submit" in actions:
                return rec_id, f"submit_candidate_probe={rec_id}"
        return 0, f"list_failed status={status}"
    rows = (((payload.get("data") or {}).get("records")) or [])
    for row in rows:
        if not isinstance(row, dict):
            continue
        rec_id = int(row.get("id") or 0)
        if rec_id <= 0:
            continue
        st, body = _intent(intent_url, token, "payment.request.available_actions", {"id": rec_id})
        if st >= 400 or body.get("ok") is not True:
            continue
        actions = (((body.get("data") or {}).get("actions")) or [])
        for item in actions:
            if not isinstance(item, dict):
                continue
            if str(item.get("key") or "").strip().lower() == "submit" and bool(item.get("allowed")):
                return rec_id, f"submit_candidate={rec_id}"
    return 0, "no_submit_candidate"


def _ensure_payment_request(intent_url: str, token: str) -> tuple[int, str]:
    debug: list[str] = []
    candidate_id, candidate_debug = _find_submit_candidate(intent_url, token, limit=50)
    debug.append(candidate_debug)
    if candidate_id > 0:
        return candidate_id, ";".join(debug)

    # Existing draft is only acceptable when submit is actually allowed.
    payment_id = _first_id(intent_url, token, "payment.request", ["id", "state"], [["state", "=", "draft"]])
    if payment_id > 0 and "submit" in _available_action_keys(intent_url, token, payment_id):
        return payment_id, "existing_draft_submit_allowed"
    if payment_id > 0:
        _attach_minimum_file(intent_url, token, payment_id)
        if "submit" in _available_action_keys(intent_url, token, payment_id):
            return payment_id, "existing_draft_submit_allowed_after_attach"
        debug.append(f"existing_draft_not_submittable={payment_id}")
    else:
        debug.append("no_existing_draft")

    project_id = _first_id(intent_url, token, "project.project", ["id", "name"])
    partner_id = _first_id(intent_url, token, "res.partner", ["id", "name"])
    contract_id = _first_id(intent_url, token, "construction.contract", ["id", "state"], [["state", "!=", "cancel"]])
    debug.append(f"project_id={project_id}")
    debug.append(f"partner_id={partner_id}")
    debug.append(f"contract_id={contract_id}")
    if project_id <= 0 or partner_id <= 0:
        return 0, ";".join(debug)
    created_id = _create_payment_request(intent_url, token, project_id, partner_id, contract_id)
    if created_id <= 0:
        debug.append(str(getattr(_create_payment_request, "last_error", "")))
        return 0, ";".join([item for item in debug if item])
    _attach_minimum_file(intent_url, token, created_id)
    if "submit" not in _available_action_keys(intent_url, token, created_id):
        debug.append(f"created_not_submittable={created_id}")
        return 0, ";".join([item for item in debug if item])
    return created_id, ";".join(debug)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    candidate_accounts = [
        ("admin", str(os.getenv("ADMIN_PASSWD") or os.getenv("E2E_PASSWORD") or "admin").strip()),
        (
            str(os.getenv("ROLE_FINANCE_LOGIN") or "").strip(),
            str(os.getenv("ROLE_FINANCE_PASSWORD") or "").strip(),
        ),
        ("demo_role_finance", "demo"),
        ("sc_fx_finance", "prod_like"),
        (
            str(os.getenv("E2E_LOGIN") or "").strip(),
            str(os.getenv("E2E_PASSWORD") or "").strip(),
        ),
    ]

    tokens: list[dict] = []
    for cand_login, cand_password in candidate_accounts:
        if not cand_login or not cand_password:
            continue
        ok, cand_token = _login(intent_url, db_name, cand_login, cand_password)
        if ok and cand_token:
            tokens.append({"login": cand_login, "token": cand_token})
    token = str(tokens[0]["token"]) if tokens else ""
    login = str(tokens[0]["login"]) if tokens else ""
    if not tokens:
        errors.append("login failed for seed.delivery.minimum")
    else:
        admin_token = ""
        for row in tokens:
            if str(row.get("login")) == "admin":
                admin_token = str(row.get("token") or "")
                break
        for row in tokens:
            actor_login = str(row["login"])
            actor_token = str(row["token"])
            # admin 给自己改组在 Odoo 常被限制；且 admin 已可作为保底执行账户。
            if actor_login == "admin":
                continue
            grant_token = admin_token or actor_token
            for xmlid in (
                "smart_construction_core.group_sc_cap_finance_user",
            ):
                if _ensure_group_membership(intent_url, grant_token, actor_login, xmlid):
                    continue
                warnings.append(f"group ensure failed: {xmlid} for {actor_login}")

    project_id = _first_id(intent_url, token, "project.project", ["id", "name"]) if token else 0
    if project_id <= 0:
        errors.append("project.project seed unavailable")

    seed_debug = ""
    payment_request_id = 0
    seed_debug = ""
    # Cross-account scan: find submittable request first.
    for row in tokens:
        candidate_id, candidate_debug = _find_submit_candidate(intent_url, str(row["token"]), limit=50)
        if candidate_id > 0:
            payment_request_id = candidate_id
            seed_debug = candidate_debug
            token = str(row["token"])
            login = str(row["login"])
            break

    # If no submittable record found, try to materialize one per account.
    if payment_request_id <= 0:
        for row in tokens:
            candidate_id, candidate_debug = _ensure_payment_request(intent_url, str(row["token"]))
            if candidate_id > 0 and "submit" in _available_action_keys(intent_url, str(row["token"]), candidate_id):
                payment_request_id = candidate_id
                seed_debug = candidate_debug
                token = str(row["token"])
                login = str(row["login"])
                break
            if candidate_debug:
                seed_debug = candidate_debug

    if payment_request_id <= 0:
        warnings.append("payment.request seed unavailable; fallback to owner payment flow")
        if seed_debug:
            warnings.append(seed_debug)

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "seed": {
            "seed_actor_login": login,
            "project_id": project_id,
            "payment_request_id": payment_request_id,
            "seed_debug": seed_debug,
            "owner_payment_fallback": {
                "request_id": "R8-DELIVERY-FALLBACK",
                "record_id": project_id,
                "model": "owner.payment.request",
            },
            "execute_button": {
                "model": "project.project",
                "button": {"name": "action_view_tasks", "type": "object"},
                "res_id": project_id,
                "dry_run": True,
            },
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Delivery Minimum Seed Report",
        "",
        f"- project_id: {project_id}",
        f"- payment_request_id: {payment_request_id}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        lines.extend([f"- {item}" for item in errors])
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[seed_delivery_minimum] FAIL")
        return 2
    print("[seed_delivery_minimum] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
