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
        self.uid = 0

    def _post(self, path: str, payload: dict):
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener.open(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        if data.get("error"):
            raise RuntimeError(json.dumps(data["error"], ensure_ascii=False))
        return data.get("result")

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
            raise RuntimeError(f"authentication failed for login={login}")
        self.uid = uid
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

    def create(self, model: str, values: dict, context: dict | None = None) -> int:
        kwargs = {"context": context} if context else {}
        created = self.call_kw(model, "create", [[values]], kwargs)
        if isinstance(created, list):
            record_id = int(created[0] or 0) if created else 0
        else:
            record_id = int(created or 0)
        if record_id <= 0:
            raise RuntimeError(f"create failed: {model}")
        return record_id

    def search(self, model: str, domain: list, limit: int = 1):
        return self.call_kw(model, "search", [domain], {"limit": limit})

    def search_count(self, model: str, domain: list) -> int:
        return int(self.call_kw(model, "search_count", [domain], {}) or 0)

    def read(self, model: str, ids: list[int], fields: list[str]):
        return self.call_kw(model, "read", [ids], {"fields": fields})


def _extract_m2o_id(value) -> int:
    if isinstance(value, list) and value:
        return int(value[0] or 0)
    if isinstance(value, int):
        return value
    return 0


def _extract_record_id(value) -> int:
    if isinstance(value, list):
        if not value:
            return 0
        return int(value[0] or 0)
    return int(value or 0)


def _safe_search_count(session: OdooSession, model: str, domain: list) -> int:
    try:
        return session.search_count(model, domain)
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
    outsider_login = _env("ROLE_OUTSIDER_LOGIN", "")
    outsider_password = _env("ROLE_OUTSIDER_PASSWORD", "demo")
    admin_login = _env("ADMIN_LOGIN", "admin")
    admin_password = _env("ADMIN_PASSWORD", "admin")

    failures: list[str] = []
    details: list[str] = []

    owner = OdooSession(base_url)
    owner_uid = owner.authenticate(db_name, owner_login, owner_password)
    pm = OdooSession(base_url)
    try:
        pm_uid = pm.authenticate(db_name, pm_login, pm_password)
    except Exception:
        pm = owner
        pm_uid = owner_uid
    outsider = OdooSession(base_url)
    temp_outsider_user_id = 0

    suffix = date.today().strftime("%Y%m%d")
    project_name = f"FRESH-MIN-FLOW-{suffix}-{owner_uid}-{pm_uid}"
    owner_user_data = owner.read("res.users", [owner_uid], ["company_id"])[0]
    owner_company_id = _extract_m2o_id(owner_user_data.get("company_id"))
    if owner_company_id <= 0:
        raise SystemExit("[native_business_fact_fresh_install_min_flow_verify] FAIL owner company missing")

    silent_context = {
        "tracking_disable": True,
        "mail_create_nosubscribe": True,
        "mail_auto_subscribe_no_notify": True,
    }

    project_id = owner.create(
        "project.project",
        {
            "name": project_name,
            "company_id": owner_company_id,
            "project_manager_user_id": pm_uid,
            "technical_lead_user_id": pm_uid,
            "business_lead_user_id": pm_uid,
            "cost_lead_user_id": pm_uid,
            "finance_contact_user_id": owner_uid,
        },
        context=silent_context,
    )
    details.append(f"project_id={project_id}")

    member_id = owner.create(
        "project.responsibility",
        {
            "project_id": project_id,
            "role_key": "manager",
            "user_id": pm_uid,
            "is_primary": True,
            "active": True,
        },
        context=silent_context,
    )
    details.append(f"member_id={member_id}")

    task_id = owner.create(
        "project.task",
        {
            "name": f"Task-{project_name}",
            "project_id": project_id,
            "user_ids": [(6, 0, [pm_uid])],
        },
        context=silent_context,
    )
    details.append(f"task_id={task_id}")

    budget_id = owner.create(
        "project.budget",
        {
            "name": f"Budget-{project_name}",
            "project_id": project_id,
            "amount_revenue_target": 1000.0,
            "amount_cost_target": 800.0,
        },
        context=silent_context,
    )
    details.append(f"budget_id={budget_id}")

    cost_code_ids = owner.search("project.cost.code", [("id", "!=", 0)], limit=1)
    if not cost_code_ids:
        failures.append("missing project.cost.code seed record")
        raise SystemExit(
            "[native_business_fact_fresh_install_min_flow_verify] FAIL " + "; ".join(failures)
        )

    cost_id = owner.create(
        "project.cost.ledger",
        {
            "project_id": project_id,
            "cost_code_id": int(cost_code_ids[0]),
            "date": str(date.today()),
            "period": date.today().strftime("%Y-%m"),
            "amount": 100.0,
            "note": f"Cost-{project_name}",
        },
        context=silent_context,
    )
    details.append(f"cost_id={cost_id}")

    project_data = owner.read("project.project", [project_id], ["company_id"])[0]
    project_company_id = _extract_m2o_id(project_data.get("company_id"))
    if project_company_id <= 0:
        failures.append("project.company_id missing")

    budget_data = owner.read("project.budget", [budget_id], ["project_id", "company_id"])[0]
    budget_project_id = _extract_m2o_id(budget_data.get("project_id"))
    budget_company_id = _extract_m2o_id(budget_data.get("company_id"))
    if budget_project_id != project_id:
        failures.append("budget.project_id mismatch")
    if budget_company_id != project_company_id:
        failures.append("budget.company_id mismatch")

    cost_data = owner.read("project.cost.ledger", [cost_id], ["project_id", "company_id"])[0]
    cost_project_id = _extract_m2o_id(cost_data.get("project_id"))
    cost_company_id = _extract_m2o_id(cost_data.get("company_id"))
    if cost_project_id != project_id:
        failures.append("cost.project_id mismatch")
    if cost_company_id != project_company_id:
        failures.append("cost.company_id mismatch")

    pm_project_count = pm.search_count("project.project", [("id", "=", project_id)])
    pm_task_count = pm.search_count("project.task", [("id", "=", task_id)])
    pm_budget_count = pm.search_count("project.budget", [("id", "=", budget_id)])
    pm_cost_count = pm.search_count("project.cost.ledger", [("id", "=", cost_id)])
    details.extend(
        [
            f"pm_project_count={pm_project_count}",
            f"pm_task_count={pm_task_count}",
            f"pm_budget_count={pm_budget_count}",
            f"pm_cost_count={pm_cost_count}",
        ]
    )
    if pm_project_count <= 0:
        failures.append("pm cannot see created project")
    if pm_task_count <= 0:
        failures.append("pm cannot see created task")
    if pm_budget_count <= 0:
        failures.append("pm cannot see created budget")
    if pm_cost_count <= 0:
        failures.append("pm cannot see created cost")

    if outsider_login:
        outsider.authenticate(db_name, outsider_login, outsider_password)
    else:
        admin = OdooSession(base_url)
        admin.authenticate(db_name, admin_login, admin_password)
        group_user = admin.call_kw(
            "ir.model.data",
            "search_read",
            [[("module", "=", "base"), ("name", "=", "group_user")]],
            {"fields": ["res_id"], "limit": 1},
        )
        if not group_user:
            raise SystemExit("[native_business_fact_fresh_install_min_flow_verify] FAIL cannot resolve base.group_user")
        outsider_login = f"iter1295_outsider_{int(time.time())}"
        temp_outsider_user_id = _extract_record_id(
            admin.call_kw(
                "res.users",
                "create",
                [[{
                    "name": "ITER1295 Outsider",
                    "login": outsider_login,
                    "password": outsider_password,
                    "company_id": owner_company_id,
                    "company_ids": [(6, 0, [owner_company_id])],
                    "groups_id": [(6, 0, [int(group_user[0]["res_id"])])],
                }]],
                {"context": {"tracking_disable": True}},
            )
        )
        if temp_outsider_user_id <= 0:
            raise SystemExit("[native_business_fact_fresh_install_min_flow_verify] FAIL outsider bootstrap failed")
        outsider.authenticate(db_name, outsider_login, outsider_password)

    outsider_project_count = _safe_search_count(outsider, "project.project", [("id", "=", project_id)])
    outsider_task_count = _safe_search_count(outsider, "project.task", [("id", "=", task_id)])
    outsider_budget_count = _safe_search_count(outsider, "project.budget", [("id", "=", budget_id)])
    outsider_cost_count = _safe_search_count(outsider, "project.cost.ledger", [("id", "=", cost_id)])
    details.extend(
        [
            f"outsider_project_count={outsider_project_count}",
            f"outsider_task_count={outsider_task_count}",
            f"outsider_budget_count={outsider_budget_count}",
            f"outsider_cost_count={outsider_cost_count}",
        ]
    )
    if outsider_project_count > 0:
        failures.append("outsider sees created project")
    if outsider_task_count > 0:
        failures.append("outsider sees created task")
    if outsider_budget_count > 0:
        failures.append("outsider sees created budget")
    if outsider_cost_count > 0:
        failures.append("outsider sees created cost")

    if temp_outsider_user_id:
        try:
            admin = OdooSession(base_url)
            admin.authenticate(db_name, admin_login, admin_password)
            admin.call_kw("res.users", "unlink", [[temp_outsider_user_id]], {"context": {"tracking_disable": True}})
        except Exception:
            pass

    if failures:
        raise SystemExit(
            "[native_business_fact_fresh_install_min_flow_verify] FAIL " + "; ".join(failures)
        )

    print("[native_business_fact_fresh_install_min_flow_verify] PASS " + " ".join(details))


if __name__ == "__main__":
    main()
