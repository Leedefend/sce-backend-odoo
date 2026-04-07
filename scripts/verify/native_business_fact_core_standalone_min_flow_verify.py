#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import date
from http.cookiejar import CookieJar


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._id = 0
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar())
        )

    def _post(self, path: str, payload: dict):
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener.open(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        if body.get("error"):
            raise RuntimeError(json.dumps(body["error"], ensure_ascii=False))
        return body.get("result")

    def authenticate(self, db_name: str, login: str, password: str) -> int:
        self._id += 1
        result = self._post(
            "/web/session/authenticate",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"db": db_name, "login": login, "password": password},
                "id": self._id,
            },
        )
        uid = int(result.get("uid") or 0)
        if uid <= 0:
            raise RuntimeError(f"auth failed: {login}")
        return uid

    def call_kw(self, model: str, method: str, args=None, kwargs=None):
        self._id += 1
        return self._post(
            f"/web/dataset/call_kw/{model}/{method}",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": args or [],
                    "kwargs": kwargs or {},
                },
                "id": self._id,
            },
        )


def _safe_search_count(session: OdooSession, model: str, domain: list) -> int:
    try:
        return int(session.call_kw(model, "search_count", [domain], {}))
    except Exception:
        return 0


def _m2o_id(value) -> int:
    if isinstance(value, list) and value:
        return int(value[0] or 0)
    if isinstance(value, int):
        return value
    return 0


def _to_id(value) -> int:
    if isinstance(value, list):
        if not value:
            return 0
        return int(value[0] or 0)
    return int(value or 0)


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_prod_sim")
    owner_login = _env("ROLE_OWNER_LOGIN", "admin")
    owner_password = _env("ROLE_OWNER_PASSWORD", "admin")
    outsider_password = _env("ROLE_OUTSIDER_PASSWORD", "demo")

    owner = OdooSession(base_url)
    owner_uid = owner.authenticate(db_name, owner_login, owner_password)

    owner_user = owner.call_kw("res.users", "read", [[owner_uid], ["company_id"]], {})[0]
    owner_company_id = _m2o_id(owner_user.get("company_id"))
    if owner_company_id <= 0:
        raise SystemExit("[native_business_fact_core_standalone_min_flow_verify] FAIL owner company missing")

    cap_group_names = [
        "group_sc_cap_project_read",
        "group_sc_cap_project_user",
        "group_sc_cap_project_manager",
        "group_sc_cap_cost_read",
        "group_sc_cap_cost_user",
        "group_sc_cap_cost_manager",
        "group_sc_cap_finance_read",
        "group_sc_cap_finance_user",
        "group_sc_cap_finance_manager",
        "group_sc_cap_settlement_read",
        "group_sc_cap_settlement_user",
        "group_sc_cap_settlement_manager",
        "group_sc_cap_config_admin",
    ]
    group_rows = owner.call_kw(
        "ir.model.data",
        "search_read",
        [[("module", "=", "smart_construction_core"), ("name", "in", cap_group_names)]],
        {"fields": ["res_id"]},
    )
    group_ids = [int(row.get("res_id") or 0) for row in group_rows if int(row.get("res_id") or 0) > 0]
    if group_ids:
        owner.call_kw(
            "res.users",
            "write",
            [[owner_uid], {"groups_id": [(4, group_id) for group_id in group_ids]}],
            {"context": {"tracking_disable": True}},
        )
        owner = OdooSession(base_url)
        owner_uid = owner.authenticate(db_name, owner_login, owner_password)

    suffix = f"{date.today().strftime('%Y%m%d')}-{int(time.time())}"
    silent_context = {
        "tracking_disable": True,
        "mail_create_nosubscribe": True,
        "mail_auto_subscribe_no_notify": True,
    }

    project_id = _to_id(
        owner.call_kw(
            "project.project",
            "create",
            [[{
                "name": f"CORE-STANDALONE-{suffix}",
                "company_id": owner_company_id,
                "project_manager_user_id": owner_uid,
            }]],
            {"context": silent_context},
        )
    )

    task_id = _to_id(
        owner.call_kw(
            "project.task",
            "create",
            [[{"name": f"Task-{suffix}", "project_id": project_id}]],
            {"context": silent_context},
        )
    )

    budget_id = _to_id(
        owner.call_kw(
            "project.budget",
            "create",
            [[{
                "name": f"Budget-{suffix}",
                "project_id": project_id,
                "amount_revenue_target": 1000.0,
                "amount_cost_target": 800.0,
            }]],
            {"context": silent_context},
        )
    )

    cost_code_ids = owner.call_kw("project.cost.code", "search", [[("id", "!=", 0)]], {"limit": 1})
    if not cost_code_ids:
        created_cost_code = _to_id(
            owner.call_kw(
                "project.cost.code",
                "create",
                [[{"name": "默认人工", "code": f"CC-{suffix}", "type": "labor"}]],
                {"context": silent_context},
            )
        )
        if created_cost_code <= 0:
            raise SystemExit("[native_business_fact_core_standalone_min_flow_verify] FAIL missing project.cost.code")
        cost_code_ids = [created_cost_code]
    cost_id = _to_id(
        owner.call_kw(
            "project.cost.ledger",
            "create",
            [[{
                "project_id": project_id,
                "cost_code_id": int(cost_code_ids[0]),
                "date": str(date.today()),
                "period": date.today().strftime("%Y-%m"),
                "amount": 120.0,
                "note": f"Cost-{suffix}",
            }]],
            {"context": silent_context},
        )
    )

    partner_id = _to_id(
        owner.call_kw(
            "res.partner",
            "create",
            [[{"name": f"CorePartner-{suffix}", "company_id": owner_company_id}]],
            {},
        )
    )

    settlement_id = _to_id(
        owner.call_kw(
            "sc.settlement.order",
            "create",
            [[{
                "name": f"SET-{suffix}",
                "project_id": project_id,
                "partner_id": partner_id,
                "company_id": owner_company_id,
            }]],
            {"context": silent_context},
        )
    )

    payment_id = _to_id(
        owner.call_kw(
            "payment.request",
            "create",
            [[{
                "name": f"PAY-{suffix}",
                "project_id": project_id,
                "partner_id": partner_id,
                "amount": 100.0,
            }]],
            {"context": silent_context},
        )
    )

    failures: list[str] = []
    details: list[str] = [
        f"project_id={project_id}",
        f"task_id={task_id}",
        f"budget_id={budget_id}",
        f"cost_id={cost_id}",
        f"payment_id={payment_id}",
        f"settlement_id={settlement_id}",
    ]

    checks = [
        ("project.budget", budget_id),
        ("project.cost.ledger", cost_id),
        ("payment.request", payment_id),
        ("sc.settlement.order", settlement_id),
    ]
    for model, rec_id in checks:
        row = owner.call_kw(model, "read", [[rec_id], ["project_id", "company_id"]], {})[0]
        if _m2o_id(row.get("project_id")) != project_id:
            failures.append(f"{model}.project_id mismatch")
        if _m2o_id(row.get("company_id")) != owner_company_id:
            failures.append(f"{model}.company_id mismatch")

    outsider_login = f"core_outsider_{suffix}"
    group_user = owner.call_kw(
        "ir.model.data",
        "search_read",
        [[("module", "=", "base"), ("name", "=", "group_user")]],
        {"fields": ["res_id"], "limit": 1},
    )
    outsider_uid = _to_id(
        owner.call_kw(
            "res.users",
            "create",
            [[{
                "name": f"Core Outsider {suffix}",
                "login": outsider_login,
                "password": outsider_password,
                "company_id": owner_company_id,
                "company_ids": [(6, 0, [owner_company_id])],
                "groups_id": [(6, 0, [int(group_user[0]["res_id"])])],
            }]],
            {"context": silent_context},
        )
    )

    outsider = OdooSession(base_url)
    outsider.authenticate(db_name, outsider_login, outsider_password)
    outsider_project = _safe_search_count(outsider, "project.project", [("id", "=", project_id)])
    outsider_task = _safe_search_count(outsider, "project.task", [("id", "=", task_id)])
    outsider_budget = _safe_search_count(outsider, "project.budget", [("id", "=", budget_id)])
    outsider_cost = _safe_search_count(outsider, "project.cost.ledger", [("id", "=", cost_id)])
    outsider_payment = _safe_search_count(outsider, "payment.request", [("id", "=", payment_id)])
    outsider_settlement = _safe_search_count(outsider, "sc.settlement.order", [("id", "=", settlement_id)])
    details.extend(
        [
            f"outsider_project={outsider_project}",
            f"outsider_task={outsider_task}",
            f"outsider_budget={outsider_budget}",
            f"outsider_cost={outsider_cost}",
            f"outsider_payment={outsider_payment}",
            f"outsider_settlement={outsider_settlement}",
        ]
    )

    try:
        owner.call_kw("res.users", "unlink", [[outsider_uid]], {"context": {"tracking_disable": True}})
    except Exception:
        pass

    if failures:
        raise SystemExit(
            "[native_business_fact_core_standalone_min_flow_verify] FAIL " + "; ".join(failures)
        )

    print("[native_business_fact_core_standalone_min_flow_verify] PASS " + " ".join(details))


if __name__ == "__main__":
    main()
