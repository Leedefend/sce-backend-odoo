#!/usr/bin/env python3
"""Resolve current Odoo views for the SCBS 55 user-visible surface plan."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_user_visible_surface_target_view_write_result_v1.json"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_visible_surface/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_visible_surface/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def action_primary_view(action):
    if action and action.view_id and action.view_id.model == action.res_model:
        return action.view_id
    for action_view in action.view_ids:
        view = action_view.view_id
        if view and view.model == action.res_model:
            return view
    return env["ir.ui.view"].browse()  # noqa: F821


def default_model_view(model: str):
    View = env["ir.ui.view"].sudo()  # noqa: F821
    for view_type in ("list", "tree", "form", "kanban", "pivot", "graph", "search"):
        view = View.search([("model", "=", model), ("type", "=", view_type)], order="priority,id", limit=1)
        if view:
            return view
    return View.browse()


ensure_allowed_db()
artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821

domain = [("source_document", "=", SOURCE_DOCUMENT)]
rows = Plan.search(domain, order="priority_sequence")
updated = 0
missing_target_model: list[str] = []
missing_view: list[dict[str, str]] = []
source_counts = {"action": 0, "model_default": 0}

for record in rows:
    if not record.target_model:
        missing_target_model.append(record.legacy_menu_name)
        continue

    view = action_primary_view(record.target_action_id)
    source = "action"
    if not view:
        view = default_model_view(record.target_model)
        source = "model_default"

    if not view:
        missing_view.append({"name": record.legacy_menu_name, "target_model": record.target_model})
        continue

    record.write({"target_view_id": view.id})
    source_counts[source] += 1
    updated += 1

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if updated == len(rows) and not missing_target_model and not missing_view else "FAIL",
    "mode": "scbs_55_user_visible_surface_target_view_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "expected_rows": 55,
    "row_count": len(rows),
    "updated": updated,
    "missing_target_model": missing_target_model,
    "missing_view": missing_view,
    "source_counts": source_counts,
    "db_writes": updated,
    "decision": "scbs_55_target_views_landed" if updated == len(rows) and not missing_view else "STOP_REVIEW_REQUIRED",
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
print("SCBS_55_USER_VISIBLE_SURFACE_TARGET_VIEW_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
