# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/mnt") if Path("/mnt/scripts").exists() else Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "backend" / "executive_readonly_seed.json"

LOGIN = os.getenv("ROLE_EXECUTIVE_READONLY_LOGIN") or "executive_readonly_smoke"
PASSWORD = os.getenv("ROLE_EXECUTIVE_READONLY_PASSWORD") or "demo"

GROUP_XMLIDS = [
    "base.group_user",
    "smart_construction_core.group_sc_internal_user",
    "smart_construction_core.group_sc_cap_project_read",
    "smart_construction_core.group_sc_cap_finance_read",
    "smart_construction_core.group_sc_cap_material_read",
    "smart_construction_core.group_sc_cap_cost_read",
    "smart_construction_core.group_sc_cap_data_read",
    "smart_construction_core.group_sc_role_executive",
    "smart_construction_custom.group_sc_role_executive",
]

ACTION_XMLIDS = {
    "finance.operating_metrics": "smart_construction_core.action_sc_operating_metrics_project",
    "projects.dashboard_showcase": "smart_construction_core.action_project_dashboard",
}


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


def _action_row(scene_key: str, xmlid: str) -> dict:
    rec = _ref(xmlid)
    return {
        "scene_key": scene_key,
        "action_xmlid": xmlid,
        "action_id": int(rec.id) if rec else 0,
        "model": str(getattr(rec, "res_model", "") or "") if rec else "",
        "available": bool(rec),
    }


def _operating_metrics_count() -> int:
    try:
        return int(env["sc.operating.metrics.project"].sudo().search_count([]))  # noqa: F821
    except Exception:
        return 0


group_ids, missing_groups = _group_ids()
if missing_groups:
    payload = {
        "generated_at_utc": _utc_now(),
        "ok": False,
        "login": LOGIN,
        "missing_groups": missing_groups,
    }
    _write_report(payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)

User = env["res.users"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821
user = User.search([("login", "=", LOGIN)], limit=1)
partner = False
if user:
    partner = user.partner_id
else:
    partner = Partner.search([("name", "=", "Executive Readonly Smoke")], limit=1)
    if not partner:
        partner = Partner.create({"name": "Executive Readonly Smoke"})
    user = User.create(
        {
            "name": "Executive Readonly Smoke",
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
        "name": "Executive Readonly Smoke",
        "password": PASSWORD,
        "active": True,
        "company_id": env.company.id,  # noqa: F821
        "company_ids": [(6, 0, [env.company.id])],  # noqa: F821
        "groups_id": [(6, 0, group_ids)],
    }
)

actions = [_action_row(scene_key, xmlid) for scene_key, xmlid in ACTION_XMLIDS.items()]
finance_action = next((row for row in actions if row["scene_key"] == "finance.operating_metrics"), {})
errors: list[str] = []
if int(finance_action.get("action_id") or 0) <= 0:
    errors.append("finance_operating_metrics_action_missing")
if str(finance_action.get("model") or "") != "sc.operating.metrics.project":
    errors.append(f"finance_operating_metrics_model_mismatch:{finance_action.get('model')}")
if _operating_metrics_count() <= 0:
    errors.append("operating_metrics_empty")

env.cr.commit()  # noqa: F821
payload = {
    "generated_at_utc": _utc_now(),
    "ok": not errors,
    "login": LOGIN,
    "user_id": int(user.id),
    "group_xmlids": GROUP_XMLIDS,
    "group_ids": group_ids,
    "actions": actions,
    "operating_metrics_count": _operating_metrics_count(),
    "errors": errors,
}
_write_report(payload)
print(REPORT_PATH)
print("[executive_readonly_seed] PASS" if payload["ok"] else "[executive_readonly_seed] FAIL")
if errors:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)
