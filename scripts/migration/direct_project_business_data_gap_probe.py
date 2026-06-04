#!/usr/bin/env python3
"""Read-only data gap probe for the direct-project business menu supplement."""

from __future__ import annotations

import ast
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_DOCUMENT = "user:direct_project_business_menu:2026-05-30"
OUTPUT_JSON_NAME = "direct_project_business_data_gap_probe_result_v1.json"
OUTPUT_REPORT_NAME = "direct_project_business_data_gap_probe_report_v1.md"

SCBS55_ONLINE_COUNTS = {
    "施工合同": {"old_entry": "施工合同", "old_count": 182},
    "报价单": {"old_entry": "报价单", "old_count": 126},
    "材料结算单": {"old_entry": "材料结算单", "old_count": 1214},
    "方单": {"old_entry": "方单", "old_count": 252},
    "零星用工": {"old_entry": "零星用工", "old_count": 8769},
    "分包方单": {"old_entry": "分包方单", "old_count": 721},
    "机械台班记录": {"old_entry": "机械台班记录", "old_count": 17495},
    "租入": {"old_entry": "租入", "old_count": 166},
    "还租": {"old_entry": "还租", "old_count": 37},
    "租赁结算单": {"old_entry": "租赁结算单", "old_count": 699},
    "项目费用报销单": {"old_entry": "报销申请", "old_count": 9},
    "管理人员工资表": {"old_entry": "管理人员工资表", "old_count": 233},
    "油卡登记": {"old_entry": "油卡登记", "old_count": 8},
    "充值登记": {"old_entry": "充值登记", "old_count": 32},
    "加油登记": {"old_entry": "加油登记", "old_count": 500},
    "支付申请": {"old_entry": "支付申请", "old_count": 2595},
    "工程进度收款": {"old_entry": "到款确认表", "old_count": 220},
    "往来单位付款": {"old_entry": "往来单位付款", "old_count": 10342},
    "工程结算单": {"old_entry": "工程结算单", "old_count": 37},
    "进项上报": {"old_entry": "进项上报", "old_count": 6389},
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/direct_project_business_menu/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/direct_project_business_menu/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_domain(action) -> list[Any]:
    if not action or not action.domain:
        return []
    try:
        parsed = ast.literal_eval(action.domain)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def search_count(model_name: str, domain: list[Any]) -> tuple[int, str]:
    if not model_name or model_name not in env:  # noqa: F821
        return 0, "missing_model"
    try:
        return env[model_name].sudo().with_context(active_test=False).search_count(domain), ""  # noqa: F821
    except Exception as exc:  # noqa: BLE001
        return 0, repr(exc)


def status_for(row: dict[str, Any]) -> str:
    if row["model_missing"]:
        return "FAIL_MODEL_MISSING"
    if not row["action_id"]:
        return "FAIL_ACTION_MISSING"
    if row["count_error"]:
        return "FAIL_COUNT_ERROR"
    if row["old_count"] is not None and row["delivered_count"] < row["old_count"]:
        return "REVIEW_OLD_ONLINE_GAP"
    if row["delivered_count"] == 0:
        return "REVIEW_ZERO_DATA"
    return "PASS"


def report(payload: dict[str, Any]) -> str:
    lines = [
        "# Direct Project Business Data Gap Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        f"Source Document: {payload['source_document']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| group | menu | model | action | delivered | old online | status |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        old_count = "" if row["old_count"] is None else str(row["old_count"])
        lines.append(
            f"| {row['group']} | {row['name']} | {row['target_model']} | {row['action_id'] or ''} | "
            f"{row['delivered_count']} | {old_count} | {row['status']} |"
        )
    lines.extend(["", "## Review Rows", "", "```json", json.dumps(payload["review_rows"], ensure_ascii=False, indent=2, sort_keys=True), "```", ""])
    return "\n".join(lines)


artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
rows = []

for record in Plan.search([("source_document", "=", SOURCE_DOCUMENT)], order="priority_sequence"):
    domain = parse_domain(record.target_action_id)
    count, error = search_count(record.target_model, domain)
    old = SCBS55_ONLINE_COUNTS.get(record.legacy_menu_name, {})
    row = {
        "group": record.legacy_menu_group,
        "name": record.legacy_menu_name,
        "business_domain": record.business_domain,
        "target_model": record.target_model,
        "model_missing": bool(record.target_model and record.target_model not in env),  # noqa: F821
        "action_id": record.target_action_id.id if record.target_action_id else 0,
        "action_name": record.target_action_id.name if record.target_action_id else "",
        "action_domain": domain,
        "delivered_count": count,
        "count_error": error,
        "old_reference_entry": old.get("old_entry", ""),
        "old_count": old.get("old_count"),
        "overlay_source": SOURCE_DOCUMENT,
        "scbs55_baseline_preserved": True,
    }
    row["status"] = status_for(row)
    rows.append(row)

review_rows = [row for row in rows if row["status"] != "PASS"]
payload = {
    "status": "PASS" if not review_rows else "REVIEW",
    "mode": "direct_project_business_data_gap_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "row_count": len(rows),
    "pass_count": len(rows) - len(review_rows),
    "review_count": len(review_rows),
    "rows": rows,
    "review_rows": review_rows,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(report(payload), encoding="utf-8")
print("DIRECT_PROJECT_BUSINESS_DATA_GAP_PROBE=" + json.dumps({key: payload[key] for key in ("status", "database", "row_count", "pass_count", "review_count")}, ensure_ascii=False, sort_keys=True))
