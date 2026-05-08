#!/usr/bin/env python3
"""Read-only probe for user-prioritized legacy menu plan replay."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
EXPECTED_ROWS = 55


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/business_user_priority_menu_plan/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/business_user_priority_menu_plan/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


artifact_root = resolve_artifact_root()
output_json = artifact_root / "business_user_priority_menu_plan_probe_result_v1.json"

Model = env["sc.legacy.user.priority.menu.plan"].sudo()  # noqa: F821
domain = [("source_document", "=", SOURCE_DOCUMENT)]
row_count = Model.with_context(active_test=False).search_count(domain)
verified_count = Model.with_context(active_test=False).search_count(domain + [("replay_status", "=", "verified")])
next_topic_count = Model.with_context(active_test=False).search_count(
    domain + [("current_round_action", "=", "next_topic_required")]
)
specialized_count = Model.with_context(active_test=False).search_count(
    domain + [("current_round_action", "=", "specialized_carrier_exists")]
)
sample_names = Model.with_context(active_test=False).search(domain, order="priority_sequence", limit=10).mapped(
    "legacy_menu_name"
)
group_counts = {
    row["legacy_menu_group"] or "": row.get("legacy_menu_group_count") or row.get("__count") or 0
    for row in Model.read_group(domain, ["legacy_menu_group"], ["legacy_menu_group"], lazy=False)
}
status = "PASS" if row_count == EXPECTED_ROWS and verified_count == EXPECTED_ROWS else "FAIL"
payload = {
    "status": status,
    "mode": "business_user_priority_menu_plan_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "expected_rows": EXPECTED_ROWS,
    "row_count": row_count,
    "verified_count": verified_count,
    "next_topic_count": next_topic_count,
    "specialized_count": specialized_count,
    "group_counts": group_counts,
    "sample_names": sample_names,
    "db_writes": 0,
    "decision": "business_user_priority_menu_plan_verified" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(output_json, payload)
print("BUSINESS_USER_PRIORITY_MENU_PLAN_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
