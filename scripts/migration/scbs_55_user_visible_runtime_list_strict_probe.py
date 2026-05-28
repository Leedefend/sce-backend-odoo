#!/usr/bin/env python3
"""Probe runtime list payloads for SCBS55 user-visible menus.

This checks the same assembled page contract used by the frontend, not only
the stored ir.ui.view tree architecture.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from odoo.addons.smart_core.app_config_engine.services.assemblers.page_assembler import PageAssembler


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OUTPUT_JSON_NAME = "scbs_55_user_visible_runtime_list_strict_probe_result_v1.json"
OUTPUT_REPORT_NAME = "scbs_55_user_visible_runtime_list_strict_probe_report_v1.md"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_runtime_list/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_runtime_list/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def alias_field_name(label: str) -> str:
    return "p1_visible_" + hashlib.sha1(label.encode("utf-8")).hexdigest()[:12]


def contract_labels(record) -> list[str]:
    labels: list[str] = []
    for item in record.list_field_contract or []:
        if isinstance(item, dict):
            label = str(item.get("legacy_label") or "").strip()
            if label:
                labels.append(label)
    return labels


def action_payload(action) -> dict[str, Any]:
    row = action.read(
        [
            "id",
            "name",
            "res_model",
            "view_mode",
            "views",
            "domain",
            "context",
            "target",
            "limit",
            "search_view_id",
        ]
    )[0]
    row["id"] = int(action.id)
    return row


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS55 Runtime List Strict Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| seq | menu | model | expected | runtime | extra | missing | record extra | status |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {seq} | {name} | {model} | {expected_count} | {runtime_count} | {extra_count} | "
            "{missing_count} | {record_extra_count} | {status} |".format(**row)
        )
    lines.extend(["", "## Failures", "", "```json", json.dumps(payload["failures"], ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
rows = Plan.search([("source_document", "=", SOURCE_DOCUMENT)], order="priority_sequence")
assembler = PageAssembler(env, su_env=env["ir.model"].sudo().env)  # noqa: F821

result_rows: list[dict[str, Any]] = []
for record in rows:
    labels = contract_labels(record)
    expected_fields = [alias_field_name(label) for label in labels]
    model = str(record.target_model or "")
    action = record.target_action_id
    if not labels:
        result_rows.append(
            {
                "seq": int(record.priority_sequence or 0),
                "name": record.legacy_menu_name or "",
                "group": record.legacy_menu_group or "",
                "model": model,
                "expected_count": 0,
                "runtime_count": 0,
                "extra_count": 0,
                "missing_count": 0,
                "record_extra_count": 0,
                "status": "SKIP_NO_LIST_CONTRACT",
            }
        )
        continue
    runtime_fields: list[str] = []
    record_extra_fields: list[str] = []
    note = ""
    try:
        action_dict = action_payload(action)
        params = {
            "model": model,
            "view_type": "tree",
            "view_types": ["tree"],
            "with_data": True,
            "domain": action.domain and __import__("ast").literal_eval(action.domain) or [],
            "limit": 5,
        }
        if record.target_view_id:
            params["view_id"] = int(record.target_view_id.id)
        assembled_result = assembler.assemble_page_contract(params, action=action_dict)
        assembled = assembled_result[0] if isinstance(assembled_result, tuple) else assembled_result
        runtime_fields = list(((assembled.get("views") or {}).get("tree") or {}).get("columns") or [])
        data_rows = ((assembled.get("data") or {}).get("list") or {}).get("records") or []
        allowed_keys = set(expected_fields + ["id"])
        for data_row in data_rows:
            for key in data_row:
                if key not in allowed_keys and key not in record_extra_fields:
                    record_extra_fields.append(key)
    except Exception as exc:
        note = repr(exc)
    extra_fields = [field for field in runtime_fields if field not in expected_fields]
    missing_fields = [field for field in expected_fields if field not in runtime_fields]
    status = "PASS"
    if note:
        status = "FAIL_RUNTIME_ASSEMBLE"
    elif extra_fields or missing_fields or record_extra_fields:
        status = "FAIL_RUNTIME_COLUMNS"
    result_rows.append(
        {
            "seq": int(record.priority_sequence or 0),
            "name": record.legacy_menu_name or "",
            "group": record.legacy_menu_group or "",
            "model": model,
            "action_id": int(action.id or 0),
            "view_id": int(record.target_view_id.id or 0),
            "expected_fields": expected_fields,
            "runtime_fields": runtime_fields,
            "extra_fields": extra_fields,
            "missing_fields": missing_fields,
            "record_extra_fields": record_extra_fields,
            "expected_count": len(expected_fields),
            "runtime_count": len(runtime_fields),
            "extra_count": len(extra_fields),
            "missing_count": len(missing_fields),
            "record_extra_count": len(record_extra_fields),
            "note": note,
            "status": status,
        }
    )

failures = [row for row in result_rows if str(row["status"]).startswith("FAIL")]
payload = {
    "status": "PASS" if not failures else "FAIL",
    "mode": "scbs_55_user_visible_runtime_list_strict_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "row_count": len(result_rows),
    "failure_count": len(failures),
    "failures": failures,
    "rows": result_rows,
    "db_writes": 0,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(report_markdown(payload), encoding="utf-8")
print(
    "SCBS_55_USER_VISIBLE_RUNTIME_LIST_STRICT_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "row_count": payload["row_count"],
            "failure_count": payload["failure_count"],
            "output_json": str(artifact_dir / OUTPUT_JSON_NAME),
            "output_report": str(artifact_dir / OUTPUT_REPORT_NAME),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if payload["status"] != "PASS":
    raise SystemExit(2)
