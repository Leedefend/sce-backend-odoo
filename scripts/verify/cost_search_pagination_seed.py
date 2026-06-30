# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/mnt") if Path("/mnt/scripts").exists() else Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "backend" / "cost_search_pagination_seed.json"

LOGIN = os.getenv("ROLE_COST_READONLY_LOGIN") or "cost_readonly_smoke"
PASSWORD = os.getenv("ROLE_COST_READONLY_PASSWORD") or "demo"

GROUP_XMLIDS = [
    "base.group_user",
    "smart_construction_core.group_sc_internal_user",
    "smart_construction_core.group_sc_cap_project_read",
    "smart_construction_core.group_sc_cap_cost_read",
    "smart_construction_core.group_sc_cap_finance_read",
    "smart_construction_custom.group_sc_role_finance",
]

SCENES = [
    ("cost.project_budget", "smart_construction_core.menu_project_budget", "smart_construction_core.action_project_budget", "project.budget"),
    ("cost.project_cost_ledger", "smart_construction_core.menu_sc_project_cost_ledger", "smart_construction_core.action_project_cost_ledger", "project.cost.ledger"),
    ("cost.profit_compare", "smart_construction_core.menu_sc_profit_reports", "smart_construction_core.action_project_profit_compare", "project.profit.compare"),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_report(payload: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ref(xmlid: str):
    return env.ref(xmlid, raise_if_not_found=False)  # noqa: F821


def _group_ids() -> tuple[list[int], list[str]]:
    ids: list[int] = []
    missing: list[str] = []
    for xmlid in GROUP_XMLIDS:
        rec = _ref(xmlid)
        if rec:
            ids.append(int(rec.id))
        else:
            missing.append(xmlid)
    return ids, missing


def _scene_row(scene_key: str, menu_xmlid: str, action_xmlid: str, model: str) -> dict:
    menu = _ref(menu_xmlid)
    action = _ref(action_xmlid)
    count = int(env[model].sudo().search_count([])) if model in env else 0  # noqa: F821
    return {
        "scene_key": scene_key,
        "menu_xmlid": menu_xmlid,
        "menu_id": int(menu.id) if menu else 0,
        "action_xmlid": action_xmlid,
        "action_id": int(action.id) if action else 0,
        "model": model,
        "action_model": str(getattr(action, "res_model", "") or "") if action else "",
        "row_count": count,
        "ok": bool(menu) and bool(action) and str(getattr(action, "res_model", "") or "") == model and count > 0,
    }


group_ids, missing_groups = _group_ids()
if missing_groups:
    payload = {"generated_at_utc": _utc_now(), "ok": False, "login": LOGIN, "missing_groups": missing_groups}
    _write_report(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)

User = env["res.users"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821
user = User.search([("login", "=", LOGIN)], limit=1)
if not user:
    partner = Partner.search([("name", "=", "Cost Readonly Smoke")], limit=1)
    if not partner:
        partner = Partner.create({"name": "Cost Readonly Smoke"})
    user = User.create(
        {
            "name": "Cost Readonly Smoke",
            "login": LOGIN,
            "password": PASSWORD,
            "partner_id": partner.id,
            "company_id": env.company.id,  # noqa: F821
            "company_ids": [(6, 0, [env.company.id])],  # noqa: F821
            "groups_id": [(6, 0, group_ids)],
        }
    )

user.write(
    {
        "name": "Cost Readonly Smoke",
        "password": PASSWORD,
        "active": True,
        "company_id": env.company.id,  # noqa: F821
        "company_ids": [(6, 0, [env.company.id])],  # noqa: F821
        "groups_id": [(6, 0, group_ids)],
    }
)

checks = [_scene_row(*spec) for spec in SCENES]
errors = [row for row in checks if not row["ok"]]
env.cr.commit()  # noqa: F821
payload = {
    "generated_at_utc": _utc_now(),
    "ok": not errors,
    "login": LOGIN,
    "user_id": int(user.id),
    "company_id": int(env.company.id),  # noqa: F821
    "group_xmlids": GROUP_XMLIDS,
    "group_ids": group_ids,
    "checks": checks,
    "errors": errors,
}
_write_report(payload)
print(REPORT_PATH)
print("[cost_search_pagination_seed] PASS" if payload["ok"] else "[cost_search_pagination_seed] FAIL")
if errors:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)
