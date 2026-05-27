#!/usr/bin/env python3
"""Replay live-captured SCBS user-visible surface contracts.

The source CSV is produced from the live legacy system menu/config capture and
contains no credentials. This script enriches the existing 55-entry user
priority plan with old-system paths, ConfigIds, source tables, list fields, and
search contracts so later implementation work has one executable baseline.
"""

from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
INPUT_CSV = Path("docs/migration_alignment/scbs_55_user_visible_surface_live_alignment_v1.csv")
OUTPUT_JSON_NAME = "scbs_55_user_visible_surface_live_alignment_write_result_v1.json"


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / INPUT_CSV).exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(REPO_ROOT / "artifacts/migration")
    candidates.append(Path("/mnt/artifacts/migration"))
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


FIELD_PATTERN = re.compile(r"^(?P<label>.*?)(?:\((?P<field>[^()]*)\))?$")


def split_items(raw: str) -> list[str]:
    return [item.strip() for item in str(raw or "").split(";") if item.strip()]


def parse_field_items(raw: str) -> list[dict[str, object]]:
    fields: list[dict[str, object]] = []
    for index, item in enumerate(split_items(raw)):
        match = FIELD_PATTERN.match(item)
        label = (match.group("label") if match else item).strip()
        source_field = ((match.group("field") if match else "") or "").strip()
        fields.append(
            {
                "sequence": (index + 1) * 10,
                "legacy_label": label,
                "legacy_field": source_field,
                "legacy_table": source_field.split("$", 1)[1] if "$" in source_field else "",
                "required_for_alignment": True,
                "source": "scbs_live_lowcode_config",
            }
        )
    return fields


def parse_search_items(raw: str) -> list[dict[str, object]]:
    fields: list[dict[str, object]] = []
    for index, item in enumerate(split_items(raw)):
        match = FIELD_PATTERN.match(item)
        label = (match.group("label") if match else item).strip()
        source_field = ((match.group("field") if match else "") or "").strip()
        fields.append(
            {
                "sequence": (index + 1) * 10,
                "legacy_label": label,
                "legacy_field": source_field,
                "source": "scbs_live_lowcode_config",
            }
        )
    return fields


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def source_tables(row: dict[str, str]) -> str:
    parts = [row.get("main_table", "").strip()]
    parts.extend(item.strip() for item in row.get("from_table", "").split(",") if item.strip())
    return "; ".join(item for item in parts if item)


REPO_ROOT = repo_root()
ARTIFACT_ROOT = artifact_root()

ensure_allowed_db()
rows = read_rows(REPO_ROOT / INPUT_CSV)
Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821

updated = 0
missing: list[dict[str, object]] = []
status_counts: dict[str, int] = {}
for row in rows:
    status = row.get("capture_status", "")
    status_counts[status] = status_counts.get(status, 0) + 1
    record = Plan.search(
        [
            ("source_document", "=", SOURCE_DOCUMENT),
            ("legacy_menu_group", "=", row["group"]),
            ("legacy_menu_name", "=", row["name"]),
        ],
        limit=1,
    )
    if not record:
        missing.append({"seq": row.get("seq"), "group": row.get("group"), "name": row.get("name")})
        continue

    list_contract = parse_field_items(row.get("visible_columns", ""))
    hidden_contract = parse_field_items(row.get("hidden_columns", ""))
    search_contract = {
        "source": "scbs_live_lowcode_config",
        "capture_status": status,
        "match": row.get("match", ""),
        "config_id": row.get("config_id", ""),
        "config_type": row.get("config_type", ""),
        "old_link": row.get("old_link", ""),
        "default_order": row.get("order_info", ""),
        "filter_fields": parse_search_items(row.get("search_fields", "")),
        "hidden_columns": hidden_contract,
        "add_config_id": row.get("add_config_id", ""),
        "show_add_config_id": row.get("show_add_config_id", ""),
    }
    form_section_contract = [
        {
            "sequence": 10,
            "title": "老系统列表字段",
            "legacy_labels": [item["legacy_label"] for item in list_contract],
            "source": "scbs_live_lowcode_config",
        },
        {
            "sequence": 90,
            "title": "附件",
            "required": any(item["legacy_label"] == "附件" for item in list_contract),
            "source": "scbs_live_lowcode_config",
        },
        {
            "sequence": 100,
            "title": "日志",
            "required": True,
            "source": "unified_daily_business_form_structure",
        },
    ]
    note = (
        f"live_capture_status={status}; old_path={row.get('old_system_path', '')}; "
        f"config_id={row.get('config_id', '')}; main_table={row.get('main_table', '')}; "
        f"from_table={row.get('from_table', '')}"
    )
    record.write(
        {
            "old_system_path": row.get("old_system_path", "") or record.old_system_path,
            "legacy_source_tables": source_tables(row) or record.legacy_source_tables,
            "legacy_field_list": "; ".join(item["legacy_label"] for item in list_contract)
            or record.legacy_field_list,
            "extracted_evidence": note,
            "list_field_contract": list_contract,
            "search_contract": search_contract,
            "form_section_contract": form_section_contract,
            "default_order": row.get("order_info", "") or record.default_order,
            "surface_contract_status": "runtime_spec_landed"
            if status in {"captured", "report_config_id_captured"}
            else "view_gap_audit_required",
            "runtime_gap_summary": row.get("alignment_note", ""),
        }
    )
    updated += 1

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if updated == len(rows) and not missing else "FAIL",
    "mode": "scbs_55_user_visible_surface_live_alignment_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "input_csv": str(REPO_ROOT / INPUT_CSV),
    "input_rows": len(rows),
    "updated": updated,
    "missing": missing,
    "capture_status_counts": status_counts,
    "db_writes": updated,
    "decision": "scbs_55_live_surface_contracts_landed" if updated == len(rows) and not missing else "STOP_REVIEW_REQUIRED",
}
write_json(ARTIFACT_ROOT / OUTPUT_JSON_NAME, payload)
print("SCBS_55_USER_VISIBLE_SURFACE_LIVE_ALIGNMENT_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
