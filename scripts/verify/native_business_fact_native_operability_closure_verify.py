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
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
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

    def call_kw(self, model: str, method: str, args: list | None = None, kwargs: dict | None = None):
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


def _safe_count(session: OdooSession, model: str, domain: list) -> int:
    try:
        return int(session.call_kw(model, "search_count", [domain], {}) or 0)
    except Exception as error:
        message = str(error)
        if "AccessError" in message or "not allowed to access" in message:
            return 0
        raise


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_prod_sim")
    owner_login = _env("ROLE_OWNER_LOGIN", "wutao")
    owner_password = _env("ROLE_OWNER_PASSWORD", "demo")
    pm_login = _env("ROLE_PM_LOGIN", "xiaohuijiu")
    pm_password = _env("ROLE_PM_PASSWORD", "demo")
    outsider_password = _env("ROLE_OUTSIDER_PASSWORD", "demo")
    admin_login = _env("ADMIN_LOGIN", "admin")
    admin_password = _env("ADMIN_PASSWORD", "admin")

    failures: list[str] = []
    details: list[str] = []

    owner = OdooSession(base_url)
    owner_uid = owner.authenticate(db_name, owner_login, owner_password)

    pm = OdooSession(base_url)
    pm_uid = pm.authenticate(db_name, pm_login, pm_password)

    admin = OdooSession(base_url)
    admin.authenticate(db_name, admin_login, admin_password)

    cost_manager_group = admin.call_kw(
        "ir.model.data",
        "search_read",
        [[("module", "=", "smart_construction_core"), ("name", "=", "group_sc_cap_cost_manager")]],
        {"fields": ["res_id"], "limit": 1},
    )
    if cost_manager_group:
        admin.call_kw(
            "res.users",
            "write",
            [[pm_uid], {"groups_id": [(4, int(cost_manager_group[0]["res_id"]))]}],
            {"context": {"tracking_disable": True}},
        )
        pm = OdooSession(base_url)
        pm_uid = pm.authenticate(db_name, pm_login, pm_password)
        details.append("pm_cost_authorized=1")

    owner_row = owner.call_kw("res.users", "read", [[owner_uid], ["company_id"]], {})[0]
    company_id = _m2o_id(owner_row.get("company_id"))
    if company_id <= 0:
        raise SystemExit("[native_business_fact_native_operability_closure_verify] FAIL owner company missing")

    silent_context = {
        "tracking_disable": True,
        "mail_create_nosubscribe": True,
        "mail_auto_subscribe_no_notify": True,
    }
    suffix = f"{date.today().strftime('%Y%m%d')}-{int(time.time())}"

    project_id = _to_id(
        owner.call_kw(
            "project.project",
            "create",
            [[{
                "name": f"NATIVE-CLOSURE-{suffix}",
                "company_id": company_id,
            }]],
            {"context": silent_context},
        )
    )
    details.append(f"project_id={project_id}")

    owner.call_kw(
        "project.project",
        "write",
        [[project_id], {
            "project_manager_user_id": pm_uid,
            "technical_lead_user_id": pm_uid,
            "business_lead_user_id": pm_uid,
            "cost_lead_user_id": pm_uid,
            "finance_contact_user_id": owner_uid,
        }],
        {"context": silent_context},
    )

    member_id = _to_id(
        owner.call_kw(
            "project.responsibility",
            "create",
            [[{
                "project_id": project_id,
                "role_key": "manager",
                "user_id": pm_uid,
                "is_primary": True,
                "active": True,
            }]],
            {"context": silent_context},
        )
    )
    details.append(f"member_id={member_id}")

    task_id = _to_id(
        pm.call_kw(
            "project.task",
            "create",
            [[{"name": f"Task-{suffix}", "project_id": project_id, "user_ids": [(6, 0, [pm_uid])]}]],
            {"context": silent_context},
        )
    )
    details.append(f"task_id={task_id}")

    pm.call_kw(
        "project.task",
        "write",
        [[task_id], {"name": f"Task-{suffix}-edited"}],
        {"context": silent_context},
    )

    stage_ids = pm.call_kw(
        "project.task.type",
        "search",
        [[("id", "!=", 0)]],
        {"limit": 1},
    )
    if stage_ids:
        pm.call_kw(
            "project.task",
            "write",
            [[task_id], {"stage_id": int(stage_ids[0])}],
            {"context": silent_context},
        )

    budget_id = _to_id(
        pm.call_kw(
            "project.budget",
            "create",
            [[{
                "name": f"Budget-{suffix}",
                "project_id": project_id,
                "amount_revenue_target": 1000.0,
                "amount_cost_target": 700.0,
            }]],
            {"context": silent_context},
        )
    )
    details.append(f"budget_id={budget_id}")

    cost_code_ids = pm.call_kw("project.cost.code", "search", [[("id", "!=", 0)]], {"limit": 1})
    if not cost_code_ids:
        failures.append("missing project.cost.code seed")
        raise SystemExit("[native_business_fact_native_operability_closure_verify] FAIL " + "; ".join(failures))

    cost_id = _to_id(
        pm.call_kw(
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
    details.append(f"cost_id={cost_id}")

    budget_row = owner.call_kw("project.budget", "read", [[budget_id], ["project_id", "company_id"]], {})[0]
    cost_row = owner.call_kw("project.cost.ledger", "read", [[cost_id], ["project_id", "company_id"]], {})[0]
    if _m2o_id(budget_row.get("project_id")) != project_id or _m2o_id(budget_row.get("company_id")) != company_id:
        failures.append("budget anchor mismatch")
    if _m2o_id(cost_row.get("project_id")) != project_id or _m2o_id(cost_row.get("company_id")) != company_id:
        failures.append("cost anchor mismatch")

    group_user = admin.call_kw(
        "ir.model.data",
        "search_read",
        [[("module", "=", "base"), ("name", "=", "group_user")]],
        {"fields": ["res_id"], "limit": 1},
    )
    outsider_login = f"iter1296_outsider_{int(time.time())}"
    outsider_uid = _to_id(
        admin.call_kw(
            "res.users",
            "create",
            [[{
                "name": f"ITER1296 Outsider {suffix}",
                "login": outsider_login,
                "password": outsider_password,
                "company_id": company_id,
                "company_ids": [(6, 0, [company_id])],
                "groups_id": [(6, 0, [int(group_user[0]["res_id"])])],
            }]],
            {"context": {"tracking_disable": True}},
        )
    )

    outsider = OdooSession(base_url)
    outsider.authenticate(db_name, outsider_login, outsider_password)

    outsider_project = _safe_count(outsider, "project.project", [("id", "=", project_id)])
    outsider_task = _safe_count(outsider, "project.task", [("id", "=", task_id)])
    outsider_budget = _safe_count(outsider, "project.budget", [("id", "=", budget_id)])
    outsider_cost = _safe_count(outsider, "project.cost.ledger", [("id", "=", cost_id)])
    details.extend([
        f"outsider_project_count={outsider_project}",
        f"outsider_task_count={outsider_task}",
        f"outsider_budget_count={outsider_budget}",
        f"outsider_cost_count={outsider_cost}",
    ])
    if outsider_project > 0 or outsider_task > 0 or outsider_budget > 0 or outsider_cost > 0:
        failures.append("outsider visibility not denied")

    try:
        outsider.call_kw("project.task", "write", [[task_id], {"name": "OUTSIDER-MUTATION"}], {"context": silent_context})
        failures.append("outsider write task unexpectedly allowed")
    except Exception:
        pass
    try:
        outsider.call_kw("project.budget", "write", [[budget_id], {"amount_cost_target": 1.0}], {"context": silent_context})
        failures.append("outsider write budget unexpectedly allowed")
    except Exception:
        pass

    try:
        admin.call_kw("res.users", "unlink", [[outsider_uid]], {"context": {"tracking_disable": True}})
    except Exception:
        pass

    if failures:
        raise SystemExit("[native_business_fact_native_operability_closure_verify] FAIL " + "; ".join(failures))

    print("[native_business_fact_native_operability_closure_verify] PASS " + " ".join(details))


if __name__ == "__main__":
    main()
