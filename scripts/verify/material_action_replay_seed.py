# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from odoo import fields


ROOT = Path("/mnt") if Path("/mnt/scripts").exists() else Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "backend" / "material_action_replay_seed.json"

SCENES = [
    ("material.center", "smart_construction_core.menu_sc_material_center", "", ""),
    (
        "material.procurement",
        "smart_construction_core.menu_sc_material_purchase_request",
        "smart_construction_core.action_sc_material_purchase_request",
        "sc.material.purchase.request",
    ),
    (
        "material.inbound",
        "smart_construction_core.menu_sc_material_inbound",
        "smart_construction_core.action_sc_material_inbound",
        "sc.material.inbound",
    ),
    (
        "labor.request",
        "smart_construction_core.menu_sc_labor_request",
        "smart_construction_core.action_sc_labor_request",
        "sc.labor.request",
    ),
    (
        "equipment.request",
        "smart_construction_core.menu_sc_equipment_request",
        "smart_construction_core.action_sc_equipment_request",
        "sc.equipment.request",
    ),
    (
        "subcontract.request",
        "smart_construction_core.menu_sc_subcontract_request",
        "smart_construction_core.action_sc_subcontract_request",
        "sc.subcontract.request",
    ),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_report(payload: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ref_id(xmlid: str) -> int:
    if not xmlid:
        return 0
    rec = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
    return int(rec.id) if rec else 0


def _create_project(user):
    Project = env["project.project"].sudo()  # noqa: F821
    stamp = fields.Datetime.now().strftime("%Y%m%d%H%M%S")
    vals = {
        "name": f"Material Action Replay {stamp}",
        "manager_id": user.id,
        "user_id": user.id,
        "company_id": env.company.id,  # noqa: F821
        "operation_strategy": "direct",
        "funding_enabled": True,
    }
    if "user_ids" in Project._fields:
        vals["user_ids"] = [(4, user.id)]
    if "sc_project_showcase" in Project._fields:
        vals["sc_project_showcase"] = True
    if "sc_project_showcase_ready" in Project._fields:
        vals["sc_project_showcase_ready"] = True
    return Project.create(vals)


def _partner():
    Partner = env["res.partner"].sudo()  # noqa: F821
    partner = Partner.search([("name", "=", "Material Action Replay Supplier")], limit=1)
    if not partner:
        partner = Partner.create({"name": "Material Action Replay Supplier", "supplier_rank": 1})
    return partner


def _warehouse_location():
    Warehouse = env["stock.warehouse"].sudo()  # noqa: F821
    warehouse = Warehouse.search([("company_id", "in", [env.company.id, False])], limit=1)  # noqa: F821
    return warehouse, warehouse.lot_stock_id if warehouse else (False, False)


def _create_record(model: str, project, user, partner):
    Model = env[model].sudo()  # noqa: F821
    vals = {
        "project_id": project.id,
    }
    if "requester_id" in Model._fields:
        vals["requester_id"] = user.id
    if "applicant_id" in Model._fields:
        vals["applicant_id"] = user.id
    if "keeper_id" in Model._fields:
        vals["keeper_id"] = user.id
    if "supplier_id" in Model._fields:
        vals["supplier_id"] = partner.id
    if "contractor_id" in Model._fields:
        vals["contractor_id"] = partner.id
    if "suggested_subcontractor_id" in Model._fields:
        vals["suggested_subcontractor_id"] = partner.id
    if "subcontract_scope" in Model._fields:
        vals["subcontract_scope"] = "Action replay subcontract scope"
    if "usage_location" in Model._fields:
        vals["usage_location"] = "Action replay site"
    if "purpose" in Model._fields:
        vals["purpose"] = "Action replay procurement"
    if model == "sc.material.inbound":
        warehouse, location = _warehouse_location()
        if warehouse:
            vals["warehouse_id"] = warehouse.id
        if location:
            vals["dest_location_id"] = location.id
    return Model.create(vals)


login = os.getenv("ROLE_MATERIAL_LOGIN") or os.getenv("ROLE_PM_LOGIN") or "demo_business_full"
User = env["res.users"].sudo()  # noqa: F821
user = User.search([("login", "=", login)], limit=1)
if not user:
    payload = {"generated_at_utc": _utc_now(), "ok": False, "error": f"missing replay user login={login}"}
    _write_report(payload)
    raise SystemExit(1)

project = _create_project(user)
partner = _partner()

checks = []
for scene_key, menu_xmlid, action_xmlid, model in SCENES:
    row = {
        "scene_key": scene_key,
        "menu_xmlid": menu_xmlid,
        "menu_id": _ref_id(menu_xmlid),
        "action_xmlid": action_xmlid,
        "action_id": _ref_id(action_xmlid),
        "model": model,
        "record_id": 0,
        "ok": True,
        "errors": [],
    }
    if row["menu_id"] <= 0:
        row["ok"] = False
        row["errors"].append("menu_xmlid_unresolved")
    if action_xmlid and row["action_id"] <= 0:
        row["ok"] = False
        row["errors"].append("action_xmlid_unresolved")
    if model:
        try:
            rec = _create_record(model, project, user, partner)
            row["record_id"] = int(rec.id)
        except Exception as exc:
            row["ok"] = False
            row["errors"].append(f"record_create_failed:{type(exc).__name__}:{exc}")
    checks.append(row)

env.cr.commit()  # noqa: F821
payload = {
    "generated_at_utc": _utc_now(),
    "ok": all(row["ok"] for row in checks),
    "login": login,
    "project_id": int(project.id),
    "checks": checks,
}
_write_report(payload)
print(REPORT_PATH)
print("[material_action_replay_seed] PASS" if payload["ok"] else "[material_action_replay_seed] FAIL")
if not payload["ok"]:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(1)
