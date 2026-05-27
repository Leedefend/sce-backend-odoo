#!/usr/bin/env python3
"""Read-only audit for SCBS 55 custom pages and dashboard gaps."""

from __future__ import annotations

import json
import os
from pathlib import Path
from xml.etree import ElementTree

from odoo.tools.safe_eval import safe_eval


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
EXPECTED_NAMES = ["组织机构", "证照登记", "供货合同分析", "成本大屏", "经营大屏"]
OUTPUT_JSON_NAME = "scbs_55_user_visible_surface_custom_gap_probe_result_v1.json"
OUTPUT_REPORT_NAME = "scbs_55_user_visible_surface_custom_gap_probe_report_v1.md"


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


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def xml_fields(arch: str) -> list[dict[str, str]]:
    if not arch:
        return []
    try:
        root = ElementTree.fromstring(arch.encode("utf-8"))
    except Exception:
        return []
    return [
        {
            "name": str(node.attrib.get("name") or "").strip(),
            "string": str(node.attrib.get("string") or "").strip(),
            "optional": str(node.attrib.get("optional") or "").strip(),
        }
        for node in root.iter("field")
        if str(node.attrib.get("name") or "").strip()
    ]


def action_domain(action) -> list[object]:
    raw = str(action.domain or "[]")
    try:
        value = safe_eval(raw, {"context": {}})
    except Exception:
        return []
    return value if isinstance(value, list) else []


def record_count(model: str, domain: list[object]) -> int | None:
    if not model or model not in env:  # noqa: F821
        return None
    try:
        return env[model].sudo().search_count(domain)  # noqa: F821
    except Exception:
        return None


def view_fields_for_model(model: str, view_type: str) -> list[dict[str, str]]:
    if not model or model not in env:  # noqa: F821
        return []
    try:
        views = env[model].sudo().get_views([(False, view_type)], {})  # noqa: F821
    except Exception:
        return []
    view = ((views.get("views") or {}).get(view_type) or {}) if isinstance(views, dict) else {}
    return xml_fields(str(view.get("arch") or ""))


def decision_for(record) -> str:
    search_contract = record.search_contract or {}
    capture_status = search_contract.get("capture_status")
    if capture_status == "menu_without_link":
        return "dashboard_visual_contract_required"
    return "custom_route_runtime_capture_required"


def report_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# SCBS 55 Custom Gap Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        "",
        "| seq | entry | old path | target model | action | view | rows | decision |",
        "| ---: | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in payload["entries"]:
        lines.append(
            "| {priority_sequence} | {legacy_menu_name} | {old_system_path} | `{target_model}` | "
            "{target_action_name} | {target_view_name} | {current_record_count} | {audit_decision} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Detail",
            "",
            "```json",
            json.dumps(payload["entries"], ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


artifact_dir = artifact_root()
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
domain = [
    ("source_document", "=", SOURCE_DOCUMENT),
    ("legacy_menu_name", "in", EXPECTED_NAMES),
]
records = Plan.search(domain, order="priority_sequence")

entries = []
missing = sorted(set(EXPECTED_NAMES) - set(records.mapped("legacy_menu_name")))
for record in records:
    action = record.target_action_id
    domain_value = action_domain(action)
    target_model = str(record.target_model or "")
    current_count = record_count(target_model, domain_value)
    search_contract = record.search_contract or {}
    entries.append(
        {
            "priority_sequence": record.priority_sequence,
            "legacy_menu_group": record.legacy_menu_group,
            "legacy_menu_name": record.legacy_menu_name,
            "old_system_path": record.old_system_path or "",
            "old_link": search_contract.get("old_link") or "",
            "capture_status": search_contract.get("capture_status") or "",
            "target_model": target_model,
            "target_action_id": int(action.id or 0),
            "target_action_name": action.name if action else "",
            "target_action_domain": str(action.domain or "") if action else "",
            "target_view_id": int(record.target_view_id.id or 0),
            "target_view_name": record.target_view_id.name if record.target_view_id else "",
            "target_view_type": record.target_view_id.type if record.target_view_id else "",
            "target_view_fields": xml_fields(record.target_view_id.arch_db or "") if record.target_view_id else [],
            "default_tree_fields": view_fields_for_model(target_model, "tree"),
            "default_form_fields": view_fields_for_model(target_model, "form"),
            "current_record_count": current_count if current_count is not None else -1,
            "audit_decision": decision_for(record),
            "remaining_gap_reason": record.runtime_gap_summary or "",
        }
    )

payload = {
    "status": "PASS"
    if len(entries) == len(EXPECTED_NAMES)
    and not missing
    and all(row["target_model"] and row["target_action_id"] and row["target_view_id"] for row in entries)
    else "FAIL",
    "mode": "scbs_55_user_visible_surface_custom_gap_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "expected_names": EXPECTED_NAMES,
    "row_count": len(entries),
    "missing": missing,
    "entries": entries,
    "summary": {
        "custom_route_runtime_capture_required": sum(
            1 for row in entries if row["audit_decision"] == "custom_route_runtime_capture_required"
        ),
        "dashboard_visual_contract_required": sum(
            1 for row in entries if row["audit_decision"] == "dashboard_visual_contract_required"
        ),
        "with_records": sum(1 for row in entries if int(row["current_record_count"]) > 0),
    },
    "db_writes": 0,
    "decision": "scbs_55_custom_gap_audit_landed" if len(entries) == len(EXPECTED_NAMES) and not missing else "STOP_REVIEW_REQUIRED",
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(report_markdown(payload), encoding="utf-8")
print("SCBS_55_USER_VISIBLE_SURFACE_CUSTOM_GAP_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
