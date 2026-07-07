# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from odoo import fields


ROOT = Path("/mnt") if Path("/mnt/scripts").exists() else Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "backend" / "project_task_action_seed.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _set_if_field(model, vals: dict, field_name: str, value) -> None:
    if field_name in getattr(model, "_fields", {}):
        vals[field_name] = value


def _write_report(payload: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


login = os.getenv("ROLE_PM_LOGIN", "demo_role_pm")
User = env["res.users"].sudo()  # noqa: F821
pm_user = User.search([("login", "=", login)], limit=1)
if not pm_user:
    payload = {"generated_at_utc": _utc_now(), "ok": False, "error": f"missing PM user login={login}"}
    _write_report(payload)
    raise SystemExit(1)

Project = env["project.project"].sudo()  # noqa: F821
Task = env["project.task"].sudo()  # noqa: F821
stamp = fields.Datetime.now().strftime("%Y%m%d%H%M%S")

project_vals = {
    "name": f"Delivery Action Smoke {stamp}",
    "manager_id": pm_user.id,
    "user_id": pm_user.id,
    "company_id": env.company.id,  # noqa: F821
    "operation_strategy": "direct",
    "funding_enabled": True,
}
_set_if_field(Project, project_vals, "date_start", fields.Date.today())
_set_if_field(Project, project_vals, "start_date", fields.Date.today())
_set_if_field(Project, project_vals, "sc_project_showcase", True)
_set_if_field(Project, project_vals, "sc_project_showcase_ready", True)
_set_if_field(Project, project_vals, "sc_execution_state", "ready")
if "user_ids" in getattr(Project, "_fields", {}):
    project_vals["user_ids"] = [(4, pm_user.id)]

project = Project.with_user(pm_user).create(project_vals)

task_vals = {
    "name": f"Delivery Action Smoke Task {stamp}",
    "project_id": project.id,
}
if "user_ids" in getattr(Task, "_fields", {}):
    task_vals["user_ids"] = [(4, pm_user.id)]
if "user_id" in getattr(Task, "_fields", {}):
    task_vals["user_id"] = pm_user.id
if "sc_state" in getattr(Task, "_fields", {}):
    task_vals["sc_state"] = "draft"

task = Task.with_context(allow_transition=True).with_user(pm_user).create(task_vals)
env.cr.commit()  # noqa: F821

payload = {
    "generated_at_utc": _utc_now(),
    "ok": True,
    "login": login,
    "project_id": int(project.id),
    "task_id": int(task.id),
    "project_name": project.display_name,
    "task_name": task.display_name,
}
_write_report(payload)
print(REPORT_PATH)
print("[project_task_action_seed] PASS")
