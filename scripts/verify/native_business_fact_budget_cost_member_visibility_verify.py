#!/usr/bin/env python3
import json
import os
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path


RULES_FILE = Path("addons/smart_construction_core/security/sc_record_rules.xml")


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._id = 0
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar())
        )
        self.uid = None

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

    def authenticate(self, db_name: str, login: str, password: str):
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
        uid = result.get("uid")
        if not uid:
            raise RuntimeError(f"authentication failed for login={login}")
        self.uid = uid
        return uid

    def search_count(self, model: str, domain: list):
        self._id += 1
        return self._post(
            f"/web/dataset/call_kw/{model}/search_count",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": "search_count",
                    "args": [domain],
                    "kwargs": {},
                },
                "id": self._id,
            },
        )

    def search(self, model: str, domain: list, limit: int = 5):
        self._id += 1
        return self._post(
            f"/web/dataset/call_kw/{model}/search",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": "search",
                    "args": [domain],
                    "kwargs": {"limit": limit},
                },
                "id": self._id,
            },
        )


def _rule_block(text: str, rule_id: str) -> str:
    start_tag = f'<record id="{rule_id}" model="ir.rule">'
    start = text.find(start_tag)
    if start < 0:
        return ""
    end = text.find("</record>", start)
    if end < 0:
        return ""
    return text[start:end]


def _verify_rule_tokens() -> list[str]:
    text = RULES_FILE.read_text(encoding="utf-8")
    checks = {
        "rule_sc_cost_read_project_budget": ["project_member_ids.user_id", "project_id.user_id", "create_uid"],
        "rule_sc_cost_read_project_cost_ledger": ["project_member_ids.user_id", "project_id.user_id", "create_uid"],
        "rule_sc_cost_user_project_cost_ledger": ["project_member_ids.user_id", "project_id.user_id", "create_uid"],
    }
    failures = []
    for rule_id, tokens in checks.items():
        block = _rule_block(text, rule_id)
        if not block:
            failures.append(f"missing rule block: {rule_id}")
            continue
        for token in tokens:
            if token not in block:
                failures.append(f"missing token {token} in {rule_id}")
    return failures


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_prod_sim")
    owner_login = _env("ROLE_OWNER_LOGIN", "wutao")
    owner_password = _env("ROLE_OWNER_PASSWORD", "demo")
    pm_login = _env("ROLE_PM_LOGIN", "xiaohuijiu")
    pm_password = _env("ROLE_PM_PASSWORD", "demo")
    outsider_login = _env("ROLE_OUTSIDER_LOGIN", "outsider_seed")
    outsider_password = _env("ROLE_OUTSIDER_PASSWORD", "demo")
    require_pm_visible = _env_bool("BUDGET_COST_VERIFY_REQUIRE_PM_VISIBLE", True)

    failures = _verify_rule_tokens()
    details = []

    owner = OdooSession(base_url)
    owner.authenticate(db_name, owner_login, owner_password)

    anchor_checks = {
        "budget.project_null": ("project.budget", [("project_id", "=", False)]),
        "budget.company_null_when_project_company_set": (
            "project.budget",
            [("project_id.company_id", "!=", False), ("company_id", "=", False)],
        ),
        "budget.project_without_company": (
            "project.budget",
            [("project_id", "!=", False), ("project_id.company_id", "=", False)],
        ),
        "cost.project_null": ("project.cost.ledger", [("project_id", "=", False)]),
        "cost.company_null_when_project_company_set": (
            "project.cost.ledger",
            [("project_id.company_id", "!=", False), ("company_id", "=", False)],
        ),
        "cost.project_without_company": (
            "project.cost.ledger",
            [("project_id", "!=", False), ("project_id.company_id", "=", False)],
        ),
    }
    for key, (model, domain) in anchor_checks.items():
        count = owner.search_count(model, domain)
        details.append(f"{key}={count}")
        if count:
            failures.append(f"{key}:{count}")

    owner_budget_ids = owner.search(
        "project.budget", [("project_id.company_id", "!=", False)], limit=5
    )
    owner_cost_ids = owner.search(
        "project.cost.ledger", [("project_id.company_id", "!=", False)], limit=5
    )
    details.append(f"owner_sample_budget={len(owner_budget_ids)}")
    details.append(f"owner_sample_cost={len(owner_cost_ids)}")

    pm = OdooSession(base_url)
    pm_uid = pm.authenticate(db_name, pm_login, pm_password)
    pm_budget_visible = pm.search_count("project.budget", [("id", "!=", 0)])
    pm_cost_visible = pm.search_count("project.cost.ledger", [("id", "!=", 0)])
    details.append(f"pm_budget_visible={pm_budget_visible}")
    details.append(f"pm_cost_visible={pm_cost_visible}")
    if require_pm_visible:
        if pm_budget_visible <= 0:
            failures.append(f"pm has no visible budget records: uid={pm_uid}")
        if pm_cost_visible <= 0:
            failures.append(f"pm has no visible cost records: uid={pm_uid}")
    else:
        details.append("pm_visibility_check=disabled")

    outsider = OdooSession(base_url)
    outsider.authenticate(db_name, outsider_login, outsider_password)
    if owner_budget_ids:
        outsider_budget = outsider.search_count("project.budget", [("id", "in", owner_budget_ids)])
        details.append(f"outsider_budget_on_owner_sample={outsider_budget}")
        if outsider_budget:
            failures.append(f"outsider should not see owner budget sample: {outsider_budget}")
    if owner_cost_ids:
        outsider_cost = outsider.search_count("project.cost.ledger", [("id", "in", owner_cost_ids)])
        details.append(f"outsider_cost_on_owner_sample={outsider_cost}")
        if outsider_cost:
            failures.append(f"outsider should not see owner cost sample: {outsider_cost}")

    if failures:
        raise SystemExit(
            "[native_business_fact_budget_cost_member_visibility_verify] FAIL "
            + "; ".join(failures)
        )

    print(
        "[native_business_fact_budget_cost_member_visibility_verify] PASS "
        + " ".join(details)
    )


if __name__ == "__main__":
    main()
