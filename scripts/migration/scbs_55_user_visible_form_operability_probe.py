#!/usr/bin/env python3
"""Read-only probe for SCBS55 user-visible form alignment and operability."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
OLD_FORM_BASELINE_NAME = "scbs_55_old_system_form_surface_login_probe_result_v1.json"
OUTPUT_JSON_NAME = "scbs_55_user_visible_form_operability_probe_result_v1.json"
OUTPUT_REPORT_NAME = "scbs_55_user_visible_form_operability_probe_report_v1.md"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_form_operability/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_form_operability/{env.cr.dbname}")  # noqa: F821


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


def clean(value: object) -> str:
    return str(value or "").strip()


def old_baseline_by_key(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {(clean(row.get("group")), clean(row.get("name"))): row for row in payload.get("rows") or []}


def view_arch_fields(model_name: str, view_id: int | None = None) -> tuple[list[str], str, str]:
    if model_name not in env:  # noqa: F821
        return [], "", "model_missing"
    try:
        Model = env[model_name].sudo()  # noqa: F821
        data = Model.get_view(view_id=view_id or None, view_type="form") if hasattr(Model, "get_view") else {}
        arch = data.get("arch") or ""
    except Exception as exc:
        return [], "", f"get_view_failed:{exc}"
    try:
        root = ET.fromstring(arch)
    except Exception as exc:
        return [], arch, f"parse_failed:{exc}"
    return [node.attrib.get("name", "") for node in root.iter("field") if node.attrib.get("name")], arch, ""


def old_form_labels(row: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for key in ("add", "show"):
        cfg = row.get(key) or {}
        for item in (cfg.get("main_fields") or []) + (cfg.get("line_fields") or []):
            label = str(item.get("label") or "").strip()
            if label and label not in labels:
                labels.append(label)
    return labels


def old_sections(row: dict[str, Any]) -> list[str]:
    for key in ("add", "show"):
        cfg = row.get(key) or {}
        sections = [str(item or "").strip() for item in cfg.get("sections") or [] if str(item or "").strip()]
        if sections:
            return sections
    return []


def new_form_label_set(model_name: str, fields_in_arch: list[str]) -> set[str]:
    if model_name not in env:  # noqa: F821
        return set()
    Model = env[model_name].sudo()  # noqa: F821
    labels = set()
    for field_name in fields_in_arch:
        field = Model._fields.get(field_name)
        if field and getattr(field, "string", None):
            labels.add(str(field.string).strip())
    return labels


def hidden_required_without_defaults(model_name: str, form_fields: list[str]) -> list[str]:
    if model_name not in env:  # noqa: F821
        return []
    Model = env[model_name].sudo()  # noqa: F821
    required = [
        name
        for name, field in Model._fields.items()
        if getattr(field, "required", False)
        and not getattr(field, "compute", None)
        and not getattr(field, "related", None)
        and getattr(field, "type", "") not in {"one2many", "many2many"}
    ]
    try:
        defaults = Model.default_get(required)
    except Exception:
        defaults = {}
    visible = set(form_fields)
    return [name for name in required if name not in visible and defaults.get(name) in (None, False, "")]


def effective_form_contract_fields(model_name: str, action_id: int = 0, view_id: int = 0) -> list[str]:
    if "ui.business.config.contract" not in env or model_name not in env:  # noqa: F821
        return []
    Contract = env["ui.business.config.contract"].sudo()  # noqa: F821
    rows = Contract._effective_view_orchestration_contracts(
        model_name,
        view_type="form",
        action_id=action_id or None,
        view_id=view_id or None,
    )
    names: list[str] = []
    for row in rows:
        payload = row.get("contract_json") if isinstance(row, dict) else row.contract_json
        form = (((payload or {}).get("view_orchestration") or {}).get("views") or {}).get("form") or {}
        for item in form.get("fields") or []:
            name = item.get("name") if isinstance(item, dict) else item
            if name and str(name) not in names:
                names.append(str(name))
    return names


def status_for(row: dict[str, Any]) -> str:
    if row["model_missing"] or row["get_view_error"]:
        return "FAIL_FORM_VIEW"
    if row["missing_list_alias_fields"]:
        return "FAIL_FORM_LIST_FACTS"
    if row["old_form_field_count"] and row["old_label_match_count"] == 0:
        return "FAIL_OLD_FORM_SURFACE_UNMAPPED"
    if row["create_access"] and row["hidden_required_without_defaults"]:
        return "WARN_HIDDEN_REQUIRED_DEFAULTS"
    return "PASS"


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS55 User Visible Form Operability Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| seq | menu | model | old fields | label hits | list facts missing | create | status |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {seq} | {name} | {model} | {old_form_field_count} | {old_label_match_count} | "
            "{missing_list_alias_count} | {create_access} | {status} |".format(**row)
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
old_baseline = old_baseline_by_key(artifact_dir / OLD_FORM_BASELINE_NAME)
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
records = Plan.search([("source_document", "=", SOURCE_DOCUMENT)], order="priority_sequence")

result_rows: list[dict[str, Any]] = []
for record in records:
    seq = int(record.priority_sequence or 0)
    model = str(record.target_model or "")
    model_missing = bool(model and model not in env)  # noqa: F821
    view_id = int(record.target_view_id.id or 0)
    form_view_id = view_id if getattr(record.target_view_id, "type", "") == "form" else 0
    form_fields, _arch, get_view_error = view_arch_fields(model, form_view_id or None)
    labels = contract_labels(record)
    expected_alias_fields = [alias_field_name(label) for label in labels]
    contract_fields = effective_form_contract_fields(model, int(record.target_action_id.id or 0), form_view_id)
    missing_list_alias_fields = [field for field in expected_alias_fields if field not in contract_fields and field not in form_fields]
    old_row = old_baseline.get((clean(record.legacy_menu_group), clean(record.legacy_menu_name)), {})
    old_labels = old_form_labels(old_row)
    old_label_hits = sorted(new_form_label_set(model, form_fields + contract_fields).intersection(old_labels))
    create_access = False
    access_error = ""
    if model and not model_missing:
        try:
            create_access = bool(env[model].sudo().check_access_rights("create", raise_exception=False))  # noqa: F821
        except Exception as exc:
            access_error = repr(exc)
    row = {
        "seq": seq,
        "name": record.legacy_menu_name or "",
        "group": record.legacy_menu_group or "",
        "model": model,
        "model_missing": model_missing,
        "view_id": view_id,
        "form_view_id": form_view_id,
        "get_view_error": get_view_error,
        "form_arch_field_count": len(form_fields),
        "contract_form_field_count": len(contract_fields),
        "list_fact_count": len(expected_alias_fields),
        "missing_list_alias_fields": missing_list_alias_fields,
        "missing_list_alias_count": len(missing_list_alias_fields),
        "old_sections": old_sections(old_row),
        "planned_sections": record.form_section_contract or [],
        "old_form_field_count": len(old_labels),
        "old_label_match_count": len(old_label_hits),
        "old_label_hits": old_label_hits,
        "create_access": create_access,
        "access_error": access_error,
        "hidden_required_without_defaults": hidden_required_without_defaults(model, form_fields) if create_access else [],
        "attachment_required": bool(record.attachment_required),
        "chatter_required": bool(record.chatter_required),
    }
    row["status"] = status_for(row)
    result_rows.append(row)

failures = [row for row in result_rows if str(row["status"]).startswith("FAIL")]
warnings = [row for row in result_rows if str(row["status"]).startswith("WARN")]
payload = {
    "status": "PASS" if not failures else "FAIL",
    "mode": "scbs_55_user_visible_form_operability_probe",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "old_form_baseline_path": str(artifact_dir / OLD_FORM_BASELINE_NAME),
    "row_count": len(result_rows),
    "failure_count": len(failures),
    "warning_count": len(warnings),
    "failures": failures,
    "warnings": warnings,
    "rows": result_rows,
    "db_writes": 0,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(report_markdown(payload), encoding="utf-8")
print(
    "SCBS_55_USER_VISIBLE_FORM_OPERABILITY_PROBE="
    + json.dumps(
        {
            "status": payload["status"],
            "row_count": payload["row_count"],
            "failure_count": payload["failure_count"],
            "warning_count": payload["warning_count"],
            "output_json": str(artifact_dir / OUTPUT_JSON_NAME),
            "output_report": str(artifact_dir / OUTPUT_REPORT_NAME),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if payload["status"] != "PASS":
    raise SystemExit(2)
