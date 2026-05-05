#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
import urllib.request
from typing import Any


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1").rstrip("/")
DB_NAME = os.getenv("DB_NAME", "sc_prod_sim")
LOGIN = os.getenv("E2E_LOGIN") or os.getenv("ADMIN_LOGIN") or "admin"
PASSWORD = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

WEB_ACTIONS: list[tuple[str, int, dict[str, Any]]] = [
    ("项目立项", 663, {"render_profile": "create"}),
    ("快速创建项目", 664, {"render_profile": "create"}),
    ("我的项目", 554, {}),
    ("项目台账", 506, {}),
    ("项目驾驶舱", 570, {}),
    ("项目合同汇总", 559, {}),
    ("成本台账", 512, {}),
    ("项目资料", 562, {}),
    ("我的合同", 572, {}),
    ("收入合同", 573, {}),
    ("支出合同", 574, {}),
    ("一般合同", 643, {}),
    ("待我审批", 607, {}),
]

MOBILE_ACTIONS: list[tuple[str, int, dict[str, Any]]] = [
    ("项目立项", 663, {"render_profile": "create"}),
    ("快速创建项目", 664, {"render_profile": "create"}),
    ("我的项目", 554, {}),
    ("项目台账", 506, {}),
    ("收入合同", 573, {}),
    ("支出合同", 574, {}),
    ("待我审批", 607, {}),
]

PROJECT_RELATION_FIELDS = [
    "project_type_id",
    "project_category_id",
    "partner_id",
    "stage_id",
    "manager_id",
    "user_id",
    "tag_ids",
    "task_ids",
    "contract_ids",
    "payment_request_ids",
]


def _post(intent: str, params: dict[str, Any], token: str | None = None) -> dict[str, Any]:
    body = json.dumps({"intent": intent, "params": {"db": DB_NAME, **params}}, ensure_ascii=False).encode()
    headers = {"Content-Type": "application/json", "X-Odoo-DB": DB_NAME}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        headers["X-Anonymous-Intent"] = "1"
    req = urllib.request.Request(f"{BASE_URL}/api/v1/intent?db={DB_NAME}", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("ok") is not True:
        raise RuntimeError(f"{intent} failed: {json.dumps(payload, ensure_ascii=False)[:1200]}")
    return payload


def _login() -> str:
    payload = _post("login", {"login": LOGIN, "password": PASSWORD})
    token = (((payload.get("data") or {}).get("session") or {}).get("token") or (payload.get("data") or {}).get("token") or "")
    if not token:
        raise RuntimeError("login response missing token")
    return str(token)


def _norm_view(value: Any) -> str:
    text = str(value or "").strip()
    return "list" if text == "tree" else text


def _render_profile(row: dict[str, Any]) -> str:
    head = row.get("head") if isinstance(row.get("head"), dict) else {}
    return str(row.get("render_profile") or head.get("render_profile") or "").strip()


def _compat(v2: dict[str, Any]) -> dict[str, Any]:
    compat = (((v2.get("meta") or {}).get("compat") or {}).get("ui_contract") or {})
    nested = compat.get("ui_contract")
    return nested if isinstance(nested, dict) else {}


def _source_context(v2: dict[str, Any]) -> dict[str, Any]:
    data_meta = ((v2.get("dataContract") or {}).get("dataMeta") or {})
    runtime = v2.get("runtimeContract") or {}
    row = data_meta.get("sourceContext") or runtime.get("sourceContext") or {}
    return row if isinstance(row, dict) else {}


def _relation_signature(fields: dict[str, Any], name: str) -> dict[str, Any] | None:
    desc = fields.get(name) if isinstance(fields.get(name), dict) else {}
    entry = desc.get("relation_entry") if isinstance(desc.get("relation_entry"), dict) else {}
    if not entry:
        return None
    return {
        key: entry.get(key)
        for key in ("model", "action_id", "menu_id", "can_read", "can_create", "create_mode", "reason_code", "default_vals")
    }


def _web_contract_matrix(token: str) -> list[dict[str, Any]]:
    rows = []
    for label, action_id, extra in WEB_ACTIONS:
        old = _post("ui.contract", {"op": "action_open", "action_id": action_id, **extra}, token).get("data") or {}
        v2 = _post(
            "ui.contract.v2",
            {
                "op": "action_open",
                "action_id": action_id,
                "client_type": "web_pc",
                "delivery_profile": "full",
                **extra,
            },
            token,
        ).get("data") or {}
        compat = _compat(v2)
        source_context = _source_context(v2)
        page_info = v2.get("pageInfo") or {}
        old_sig = (old.get("model"), _norm_view(old.get("view_type")), _render_profile(old))
        v2_sig = (
            page_info.get("model"),
            _norm_view(page_info.get("viewType")),
            source_context.get("renderProfile") or _render_profile(compat),
        )
        old_context = (old.get("head") or {}).get("context") or old.get("context") or {}
        v2_context = source_context.get("context") or (compat.get("head") or {}).get("context") or compat.get("context") or {}
        old_domain = old.get("domain") or (old.get("head") or {}).get("domain") or []
        v2_domain = source_context.get("domain") or compat.get("domain") or (compat.get("head") or {}).get("domain") or []
        old_fields = old.get("fields") if isinstance(old.get("fields"), dict) else {}
        v2_fields = compat.get("fields") if isinstance(compat.get("fields"), dict) else {}
        relation_diffs = []
        if action_id in {663, 664}:
            for field in PROJECT_RELATION_FIELDS:
                old_relation = _relation_signature(old_fields, field)
                v2_relation = _relation_signature(v2_fields, field)
                if old_relation != v2_relation:
                    relation_diffs.append({"field": field, "old": old_relation, "v2": v2_relation})
        ok = (
            old_sig == v2_sig
            and old_context == v2_context
            and old_domain == v2_domain
            and len(old_fields) == len(v2_fields)
            and not relation_diffs
        )
        rows.append(
            {
                "label": label,
                "action_id": action_id,
                "ok": ok,
                "old_signature": old_sig,
                "v2_signature": v2_sig,
                "field_count": [len(old_fields), len(v2_fields)],
                "context_equal": old_context == v2_context,
                "domain_equal": old_domain == v2_domain,
                "relation_diffs": relation_diffs,
            }
        )
    return rows


def _mobile_compact_matrix(token: str) -> list[dict[str, Any]]:
    rows = []
    for label, action_id, extra in MOBILE_ACTIONS:
        full = _post(
            "ui.contract.v2",
            {
                "op": "action_open",
                "action_id": action_id,
                "client_type": "web_pc",
                "delivery_profile": "full",
                **extra,
            },
            token,
        ).get("data") or {}
        mobile = _post(
            "ui.contract.v2",
            {
                "op": "action_open",
                "action_id": action_id,
                "client_type": "harmony_h5",
                "delivery_profile": "mobile_compact",
                **extra,
            },
            token,
        ).get("data") or {}
        full_info = full.get("pageInfo") or {}
        mobile_info = mobile.get("pageInfo") or {}
        full_context = _source_context(full)
        mobile_context = _source_context(mobile)
        full_source = (((full.get("dataContract") or {}).get("dataSource") or {}).get("primary") or {})
        mobile_source = (((mobile.get("dataContract") or {}).get("dataSource") or {}).get("primary") or {})
        full_params = full_source.get("params") if isinstance(full_source.get("params"), dict) else {}
        mobile_params = mobile_source.get("params") if isinstance(mobile_source.get("params"), dict) else {}
        full_main = (full.get("dataContract") or {}).get("mainData") or {}
        mobile_main = (mobile.get("dataContract") or {}).get("mainData") or {}
        is_create = extra.get("render_profile") == "create"
        signature_ok = (full_info.get("model"), full_info.get("viewType")) == (mobile_info.get("model"), mobile_info.get("viewType"))
        context_ok = (full_context.get("context") or full_params.get("context") or {}) == (
            mobile_context.get("context") or mobile_params.get("context") or {}
        )
        domain_ok = (full_context.get("domain") or full_params.get("domain") or []) == (
            mobile_context.get("domain") or mobile_params.get("domain") or []
        )
        main_ok = True
        if is_create:
            main_ok = bool(mobile_main) and all(mobile_main.get(key) == value for key, value in full_main.items())
        compat_trimmed = (mobile.get("meta") or {}).get("sourceCompatTrimmed") is True
        page_auth = ((mobile.get("statusContract") or {}).get("globalStatus") or {}).get("pageAuth")
        auth_ok = page_auth == "edit" if is_create else page_auth in {"read", "edit"}
        ok = signature_ok and context_ok and domain_ok and main_ok and compat_trimmed and auth_ok
        rows.append(
            {
                "label": label,
                "action_id": action_id,
                "ok": ok,
                "signature_equal": signature_ok,
                "context_equal": context_ok,
                "domain_equal": domain_ok,
                "main_data_ok": main_ok,
                "compat_trimmed": compat_trimmed,
                "page_auth": page_auth,
            }
        )
    return rows


def main() -> int:
    token = _login()
    web_rows = _web_contract_matrix(token)
    mobile_rows = _mobile_compact_matrix(token)
    report = {
        "base_url": BASE_URL,
        "db": DB_NAME,
        "login": LOGIN,
        "web_matrix": web_rows,
        "mobile_compact_matrix": mobile_rows,
        "ok": all(row["ok"] for row in web_rows + mobile_rows),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
