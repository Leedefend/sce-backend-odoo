#!/usr/bin/env python3
"""Persist P0 daily business visible-surface runtime gap summaries."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/老系统列表，填单页面截图.docx"
EXPECTED_ROWS = 18
GAP_RESULT_NAME = "daily_business_visible_surface_p0_runtime_gap_probe_result_v1.json"


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/daily_business_visible_surface_p0/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/daily_business_visible_surface_p0/{env.cr.dbname}")  # noqa: F821


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", env.cr.dbname).split(",")  # noqa: F821
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_runtime_gap_write": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def entry_status(row: dict[str, object]) -> str:
    list_count = int(row.get("list_field_count") or 0)
    if (
        int(row.get("model_matched_count") or 0) == list_count
        and int(row.get("tree_matched_count") or 0) == list_count
        and int(row.get("form_matched_count") or 0) == list_count
    ):
        return "view_aligned"
    return "view_gap_audit_required"


def summary_text(row: dict[str, object]) -> str:
    payload = {
        "list_field_count": row.get("list_field_count") or 0,
        "model_matched_count": row.get("model_matched_count") or 0,
        "tree_matched_count": row.get("tree_matched_count") or 0,
        "form_matched_count": row.get("form_matched_count") or 0,
        "missing_model_labels": row.get("missing_model_labels") or [],
        "missing_tree_labels": row.get("missing_tree_labels") or [],
        "missing_form_labels": row.get("missing_form_labels") or [],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


ensure_allowed_db()
artifact_root = resolve_artifact_root()
gap_path = artifact_root / GAP_RESULT_NAME
if not gap_path.exists():
    raise RuntimeError({"missing_runtime_gap_probe_result": str(gap_path)})

gap_payload = json.loads(gap_path.read_text(encoding="utf-8"))
entries = gap_payload.get("entries") if isinstance(gap_payload, dict) else []
if not isinstance(entries, list) or len(entries) != EXPECTED_ROWS:
    raise RuntimeError({"invalid_runtime_gap_entries": len(entries) if isinstance(entries, list) else None})

Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
updated = 0
status_counts: dict[str, int] = {}
for row in entries:
    group = str(row.get("legacy_menu_group") or "").strip()
    name = str(row.get("legacy_menu_name") or "").strip()
    record = Plan.search(
        [
            ("source_document", "=", SOURCE_DOCUMENT),
            ("legacy_menu_group", "=", group),
            ("legacy_menu_name", "=", name),
        ],
        limit=1,
    )
    if not record:
        raise RuntimeError({"missing_plan_record": {"legacy_menu_group": group, "legacy_menu_name": name}})
    status = entry_status(row)
    record.write(
        {
            "surface_contract_status": status,
            "runtime_gap_summary": summary_text(row),
        }
    )
    status_counts[status] = status_counts.get(status, 0) + 1
    updated += 1
env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if updated == EXPECTED_ROWS else "FAIL",
    "mode": "daily_business_visible_surface_p0_runtime_gap_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "input_rows": len(entries),
    "updated": updated,
    "status_counts": status_counts,
    "gap_summary": gap_payload.get("summary") if isinstance(gap_payload, dict) else {},
    "decision": "daily_business_visible_surface_p0_runtime_gap_persisted"
    if updated == EXPECTED_ROWS
    else "STOP_REVIEW_REQUIRED",
}
write_json(artifact_root / "daily_business_visible_surface_p0_runtime_gap_write_result_v1.json", payload)
print("DAILY_BUSINESS_VISIBLE_SURFACE_P0_RUNTIME_GAP_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
