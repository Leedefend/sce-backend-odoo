#!/usr/bin/env python3
"""Read-only closure probe for SCBS55 user-visible list surfaces."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_user_visible_list_closure_probe_result_v1.json"
OUTPUT_REPORT_NAME = "scbs_55_user_visible_list_closure_probe_report_v1.md"
ALLOWED_ZERO_BY_SEQUENCE = {
    130: "old source tables BGGL_XZ_JJ/BGGL_XZ_JJ_CB contain 0 rows",
}


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_list_closure/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_list_closure/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def contract_labels(record) -> list[str]:
    labels: list[str] = []
    for item in record.list_field_contract or []:
        if not isinstance(item, dict):
            continue
        label = str(item.get("legacy_label") or "").strip()
        if label:
            labels.append(label)
    return labels


def action_domain(action) -> list[Any]:
    try:
        return ast.literal_eval(action.domain or "[]")
    except Exception:
        return []


def view_fields(view) -> list[str]:
    if not view:
        return []
    try:
        return [node.attrib.get("name", "") for node in ET.fromstring(view.arch).iter("field")]
    except Exception as exc:
        return [f"PARSE_ERROR:{exc}"]


def status_for(row: dict[str, Any]) -> str:
    if row["contract_field_count"] == 0:
        return "SKIP_NO_LIST_CONTRACT"
    if row["missing_alias_labels"] or row["field_order_mismatch"]:
        return "FAIL_FIELD_CONTRACT"
    if not row["action_id"] or row["model_missing"]:
        return "FAIL_ACTION"
    if row["delivered_count"] == 0:
        return "PASS_ZERO_LEGACY_EMPTY" if row["seq"] in ALLOWED_ZERO_BY_SEQUENCE else "FAIL_ZERO_DATA"
    return "PASS"


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS55 User Visible List Closure Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| seq | menu | model | fields | count | status | note |",
        "| ---: | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {seq} | {name} | {model} | {contract_field_count} | {delivered_count} | {status} | {note} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Failures",
            "",
            "```json",
            json.dumps(payload["failures"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
rows = Plan.search([("source_document", "=", SOURCE_DOCUMENT)], order="priority_sequence")

result_rows: list[dict[str, Any]] = []
for record in rows:
    labels = contract_labels(record)
    expected_fields = [alias_field_name(label) for label in labels]
    model = str(record.target_model or "")
    action = record.target_action_id
    view = record.target_view_id
    model_missing = bool(model and model not in env)  # noqa: F821
    missing_alias_labels: list[str] = []
    delivered_count = None
    domain: list[Any] = []

    if model and not model_missing:
        missing_alias_labels = [
            label for label, field_name in zip(labels, expected_fields) if field_name not in env[model]._fields  # noqa: F821
        ]
    actual_fields = view_fields(view)
    field_order_mismatch = bool(labels and actual_fields != expected_fields)
    if action and model and not model_missing:
        domain = action_domain(action)
        delivered_count = env[model].sudo().search_count(domain)  # noqa: F821

    row = {
        "seq": int(record.priority_sequence or 0),
        "name": record.legacy_menu_name or "",
        "group": record.legacy_menu_group or "",
        "model": model,
        "model_missing": model_missing,
        "action_id": int(action.id or 0),
        "view_id": int(view.id or 0),
        "domain": domain,
        "contract_field_count": len(labels),
        "missing_alias_labels": missing_alias_labels,
        "field_order_mismatch": field_order_mismatch,
        "delivered_count": delivered_count,
        "note": ALLOWED_ZERO_BY_SEQUENCE.get(int(record.priority_sequence or 0), ""),
    }
    row["status"] = status_for(row)
    result_rows.append(row)

failures = [row for row in result_rows if str(row["status"]).startswith("FAIL")]
list_contract_rows = [row for row in result_rows if row["contract_field_count"]]
zero_rows = [row for row in list_contract_rows if row["delivered_count"] == 0]
payload = {
    "status": "PASS" if not failures else "FAIL",
    "mode": "scbs_55_user_visible_list_closure_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "row_count": len(result_rows),
    "list_contract_count": len(list_contract_rows),
    "skip_no_list_contract_count": len(result_rows) - len(list_contract_rows),
    "failure_count": len(failures),
    "zero_count": len(zero_rows),
    "allowed_zero_count": len([row for row in zero_rows if row["status"] == "PASS_ZERO_LEGACY_EMPTY"]),
    "failures": failures,
    "zero_rows": zero_rows,
    "rows": result_rows,
    "db_writes": 0,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(report_markdown(payload), encoding="utf-8")
print("SCBS_55_USER_VISIBLE_LIST_CLOSURE_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
