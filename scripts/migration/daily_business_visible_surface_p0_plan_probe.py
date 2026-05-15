#!/usr/bin/env python3
"""Read-only probe for P0 daily business visible-surface alignment facts."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/老系统列表，填单页面截图.docx"
EXPECTED_ROWS = 18


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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# Daily Business Visible Surface P0 Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        "",
        "## Coverage",
        "",
        "```json",
        json.dumps(payload["coverage"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Entries",
        "",
        "| priority | group | legacy entry | domain | screenshots | field count |",
        "| ---: | --- | --- | --- | --- | ---: |",
    ]
    for row in payload["entries"]:
        lines.append(
            "| {priority_sequence} | {legacy_menu_group} | {legacy_menu_name} | {business_domain} | "
            "{screenshot_ref} | {field_count} |".format(**row)
        )
    lines.extend(["", f"Decision: `{payload['decision']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


artifact_root = resolve_artifact_root()
output_json = artifact_root / "daily_business_visible_surface_p0_plan_probe_result_v1.json"
output_report = artifact_root / "daily_business_visible_surface_p0_plan_probe_report_v1.md"

Model = env["sc.legacy.user.priority.menu.plan"].sudo()  # noqa: F821
domain = [("source_document", "=", SOURCE_DOCUMENT)]
records = Model.with_context(active_test=False).search(domain, order="priority_sequence, legacy_menu_group, legacy_menu_name")
row_count = len(records)
verified_count = len(records.filtered(lambda rec: rec.replay_status == "verified"))
p0_count = len(records.filtered(lambda rec: rec.target_iteration == "p0_daily_business_visible_surface"))
missing_field_list = records.filtered(lambda rec: not (rec.legacy_field_list or "").strip()).mapped("legacy_menu_name")
missing_scope = records.filtered(lambda rec: not (rec.next_scope or "").strip()).mapped("legacy_menu_name")
group_counts = {
    row.get("legacy_menu_group") or "": row.get("legacy_menu_group_count") or row.get("__count") or 0
    for row in Model.read_group(domain, ["legacy_menu_group"], ["legacy_menu_group"], lazy=False)
}
entries = []
for record in records:
    field_items = [item for item in (record.legacy_field_list or "").split(";") if item.strip()]
    entries.append(
        {
            "priority_sequence": record.priority_sequence,
            "legacy_menu_group": record.legacy_menu_group,
            "legacy_menu_name": record.legacy_menu_name,
            "business_domain": record.business_domain,
            "screenshot_ref": record.screenshot_ref,
            "field_count": len(field_items),
        }
    )
status = (
    "PASS"
    if row_count == EXPECTED_ROWS
    and verified_count == EXPECTED_ROWS
    and p0_count == EXPECTED_ROWS
    and not missing_field_list
    and not missing_scope
    else "FAIL"
)
payload = {
    "status": status,
    "mode": "daily_business_visible_surface_p0_plan_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "expected_rows": EXPECTED_ROWS,
    "row_count": row_count,
    "verified_count": verified_count,
    "p0_count": p0_count,
    "coverage": {
        "group_counts": group_counts,
        "missing_field_list": missing_field_list,
        "missing_scope": missing_scope,
    },
    "entries": entries,
    "db_writes": 0,
    "decision": "daily_business_visible_surface_p0_plan_verified" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(output_json, payload)
write_report(output_report, payload)
print("DAILY_BUSINESS_VISIBLE_SURFACE_P0_PLAN_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
