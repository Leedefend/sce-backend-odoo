#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.request
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


def _to_id(value) -> int:
    if isinstance(value, list):
        if not value:
            return 0
        return int(value[0] or 0)
    return int(value or 0)


def _m2o_id(value) -> int:
    if isinstance(value, list) and value:
        return int(value[0] or 0)
    if isinstance(value, int):
        return value
    return 0


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
    finance_login = _env("ROLE_FINANCE_LOGIN", "shuiwujingbanren")
    finance_password = _env("ROLE_FINANCE_PASSWORD", "demo")
    outsider_password = _env("ROLE_OUTSIDER_PASSWORD", "demo")
    admin_login = _env("ADMIN_LOGIN", "admin")
    admin_password = _env("ADMIN_PASSWORD", "admin")

    failures: list[str] = []
    details: list[str] = []

    owner = OdooSession(base_url)
    owner_uid = owner.authenticate(db_name, owner_login, owner_password)

    finance = OdooSession(base_url)
    try:
        finance_uid = finance.authenticate(db_name, finance_login, finance_password)
    except Exception:
        finance = owner
        finance_uid = owner_uid
        details.append("finance_fallback_owner=1")

    admin = OdooSession(base_url)
    admin.authenticate(db_name, admin_login, admin_password)

    group_names = [
        "group_sc_cap_finance_manager",
        "group_sc_cap_settlement_manager",
    ]
    rows = admin.call_kw(
        "ir.model.data",
        "search_read",
        [[("module", "=", "smart_construction_core"), ("name", "in", group_names)]],
        {"fields": ["res_id"]},
    )
    group_ids = [int(item.get("res_id") or 0) for item in rows if int(item.get("res_id") or 0) > 0]
    if group_ids:
        admin.call_kw(
            "res.users",
            "write",
            [[finance_uid], {"groups_id": [(4, gid) for gid in group_ids]}],
            {"context": {"tracking_disable": True}},
        )
        finance = OdooSession(base_url)
        finance_uid = finance.authenticate(db_name, finance_login if "finance_fallback_owner=1" not in details else owner_login, finance_password if "finance_fallback_owner=1" not in details else owner_password)
        details.append("finance_settlement_authorized=1")

    owner_row = owner.call_kw("res.users", "read", [[owner_uid], ["company_id"]], {})[0]
    company_id = _m2o_id(owner_row.get("company_id"))
    if company_id <= 0:
        raise SystemExit("[native_business_fact_payment_settlement_operability_verify] FAIL owner company missing")

    suffix = str(int(time.time()))
    context = {"tracking_disable": True, "mail_create_nosubscribe": True, "mail_auto_subscribe_no_notify": True}

    project_id = _to_id(
        owner.call_kw(
            "project.project",
            "create",
            [[{"name": f"PAYSET-{suffix}", "company_id": company_id, "project_manager_user_id": finance_uid}]],
            {"context": context},
        )
    )
    partner_ids = owner.call_kw("res.partner", "search", [[("id", "!=", 0)]], {"limit": 1})
    if not partner_ids:
        failures.append("missing res.partner seed for payment/settlement operability")
        raise SystemExit("[native_business_fact_payment_settlement_operability_verify] FAIL " + "; ".join(failures))
    partner_id = int(partner_ids[0])

    payment_id = _to_id(
        finance.call_kw(
            "payment.request",
            "create",
            [[{"name": f"PAY-{suffix}", "project_id": project_id, "partner_id": partner_id, "amount": 123.0}]],
            {"context": context},
        )
    )
    finance.call_kw(
        "payment.request",
        "write",
        [[payment_id], {"amount": 456.0}],
        {"context": context},
    )

    settlement_id = _to_id(
        finance.call_kw(
            "sc.settlement.order",
            "create",
            [[{"name": f"SET-{suffix}", "project_id": project_id, "partner_id": partner_id, "company_id": company_id}]],
            {"context": context},
        )
    )
    finance.call_kw(
        "sc.settlement.order",
        "write",
        [[settlement_id], {"name": f"SET-{suffix}-EDIT"}],
        {"context": context},
    )

    payment_row = owner.call_kw("payment.request", "read", [[payment_id], ["project_id", "company_id"]], {})[0]
    settlement_row = owner.call_kw("sc.settlement.order", "read", [[settlement_id], ["project_id", "company_id"]], {})[0]
    if _m2o_id(payment_row.get("project_id")) != project_id or _m2o_id(payment_row.get("company_id")) != company_id:
        failures.append("payment anchor mismatch")
    if _m2o_id(settlement_row.get("project_id")) != project_id or _m2o_id(settlement_row.get("company_id")) != company_id:
        failures.append("settlement anchor mismatch")

    group_user = admin.call_kw(
        "ir.model.data",
        "search_read",
        [[("module", "=", "base"), ("name", "=", "group_user")]],
        {"fields": ["res_id"], "limit": 1},
    )
    outsider_login = f"iter1297_outsider_{suffix}"
    outsider_uid = _to_id(
        admin.call_kw(
            "res.users",
            "create",
            [[{
                "name": f"ITER1297 Outsider {suffix}",
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

    outsider_payment = _safe_count(outsider, "payment.request", [("id", "=", payment_id)])
    outsider_settlement = _safe_count(outsider, "sc.settlement.order", [("id", "=", settlement_id)])
    details.extend([
        f"project_id={project_id}",
        f"payment_id={payment_id}",
        f"settlement_id={settlement_id}",
        f"outsider_payment_count={outsider_payment}",
        f"outsider_settlement_count={outsider_settlement}",
    ])
    if outsider_payment > 0 or outsider_settlement > 0:
        failures.append("outsider visibility not denied for payment/settlement")

    try:
        outsider.call_kw("payment.request", "write", [[payment_id], {"amount": 1.0}], {"context": context})
        failures.append("outsider write payment unexpectedly allowed")
    except Exception:
        pass
    try:
        outsider.call_kw("sc.settlement.order", "write", [[settlement_id], {"name": "OUTSIDER"}], {"context": context})
        failures.append("outsider write settlement unexpectedly allowed")
    except Exception:
        pass

    try:
        admin.call_kw("res.users", "unlink", [[outsider_uid]], {"context": {"tracking_disable": True}})
    except Exception:
        pass

    if failures:
        raise SystemExit("[native_business_fact_payment_settlement_operability_verify] FAIL " + "; ".join(failures))

    print("[native_business_fact_payment_settlement_operability_verify] PASS " + " ".join(details))


if __name__ == "__main__":
    main()
