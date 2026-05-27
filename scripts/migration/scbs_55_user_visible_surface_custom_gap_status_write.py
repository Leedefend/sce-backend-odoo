#!/usr/bin/env python3
"""Persist SCBS 55 custom/dashboard gap statuses from the read-only audit."""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_DOCUMENT = "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx"
GAP_RESULT_NAME = "scbs_55_user_visible_surface_custom_gap_probe_result_v1.json"
OUTPUT_JSON_NAME = "scbs_55_user_visible_surface_custom_gap_status_write_result_v1.json"

CUSTOM_CLOSE_RULES = {
    "组织机构": {
        "required_tokens": {"name", "parent_id", "manager_id", "company_id"},
        "reason": "custom_department_list_current_view_aligned",
    },
    "证照登记": {
        "required_tokens": {
            "document_no",
            "business_date",
            "certificate_name",
            "certificate_no",
            "holder_name",
            "valid_until",
            "state",
        },
        "reason": "custom_certificate_registration_current_view_aligned",
    },
    "供货合同分析": {
        "required_tokens": {"项目", "供应商", "计价方式", "合同金额", "合同状态"},
        "reason": "custom_supplier_contract_analysis_current_view_aligned",
    },
}

DASHBOARD_RULES = {
    "成本大屏": "dashboard_cost_visual_contract_required",
    "经营大屏": "dashboard_operation_visual_contract_required",
}


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


def normalize(value: object) -> str:
    return str(value or "").strip().replace(" ", "").replace("\u3000", "")


def target_tokens(row: dict[str, object]) -> set[str]:
    fields = row.get("target_view_fields") or []
    tokens: set[str] = set()
    if isinstance(fields, list):
        for item in fields:
            if not isinstance(item, dict):
                continue
            tokens.add(normalize(item.get("name")))
            tokens.add(normalize(item.get("string")))
    return {token for token in tokens if token}


def custom_rule_passed(name: str, row: dict[str, object]) -> tuple[bool, list[str]]:
    rule = CUSTOM_CLOSE_RULES[name]
    available = target_tokens(row)
    missing = sorted(token for token in rule["required_tokens"] if normalize(token) not in available)
    has_records = int(row.get("current_record_count") or 0) > 0
    return has_records and not missing, missing


ensure_allowed_db()
artifact_dir = artifact_root()
gap_path = artifact_dir / GAP_RESULT_NAME
if not gap_path.exists():
    raise RuntimeError({"missing_custom_gap_probe_result": str(gap_path)})

gap_payload = json.loads(gap_path.read_text(encoding="utf-8"))
entries = gap_payload.get("entries") if isinstance(gap_payload, dict) else []
if not isinstance(entries, list):
    raise RuntimeError({"invalid_custom_gap_entries": type(entries).__name__})

Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
closed: list[dict[str, object]] = []
kept_dashboard_gaps: list[dict[str, object]] = []
failed_custom: list[dict[str, object]] = []

for row in entries:
    name = str(row.get("legacy_menu_name") or "").strip()
    record = Plan.search(
        [
            ("source_document", "=", SOURCE_DOCUMENT),
            ("legacy_menu_name", "=", name),
        ],
        limit=1,
    )
    if not record:
        failed_custom.append({"name": name, "reason": "missing_plan_record"})
        continue

    if name in CUSTOM_CLOSE_RULES:
        passed, missing_tokens = custom_rule_passed(name, row)
        if not passed:
            record.write(
                {
                    "surface_contract_status": "view_gap_audit_required",
                    "runtime_gap_summary": json.dumps(
                        {
                            "status": "custom_route_view_gap_remaining",
                            "missing_tokens": missing_tokens,
                            "current_record_count": row.get("current_record_count"),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                }
            )
            failed_custom.append({"name": name, "missing_tokens": missing_tokens})
            continue
        record.write(
            {
                "surface_contract_status": "view_aligned",
                "runtime_gap_summary": json.dumps(
                    {
                        "status": CUSTOM_CLOSE_RULES[name]["reason"],
                        "current_record_count": row.get("current_record_count"),
                        "target_model": row.get("target_model"),
                        "target_action_name": row.get("target_action_name"),
                        "target_view_name": row.get("target_view_name"),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )
        closed.append({"name": name, "current_record_count": row.get("current_record_count")})
        continue

    if name in DASHBOARD_RULES:
        record.write(
            {
                "surface_contract_status": "view_gap_audit_required",
                "runtime_gap_summary": json.dumps(
                    {
                        "status": DASHBOARD_RULES[name],
                        "current_record_count": row.get("current_record_count"),
                        "target_model": row.get("target_model"),
                        "target_action_name": row.get("target_action_name"),
                        "target_view_name": row.get("target_view_name"),
                        "reason": "dashboard_entry_requires_visual_metric_layout_contract_before_view_aligned",
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
            }
        )
        kept_dashboard_gaps.append({"name": name, "current_record_count": row.get("current_record_count")})

env.cr.commit()  # noqa: F821

payload = {
    "status": "PASS" if len(closed) == 3 and len(kept_dashboard_gaps) == 2 and not failed_custom else "FAIL",
    "mode": "scbs_55_user_visible_surface_custom_gap_status_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_document": SOURCE_DOCUMENT,
    "input_rows": len(entries),
    "closed_custom_routes": closed,
    "kept_dashboard_gaps": kept_dashboard_gaps,
    "failed_custom": failed_custom,
    "db_writes": len(closed) + len(kept_dashboard_gaps) + len(failed_custom),
    "decision": "scbs_55_custom_routes_closed_dashboard_gaps_retained"
    if len(closed) == 3 and len(kept_dashboard_gaps) == 2 and not failed_custom
    else "STOP_REVIEW_REQUIRED",
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
print("SCBS_55_USER_VISIBLE_SURFACE_CUSTOM_GAP_STATUS_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] != "PASS":
    raise SystemExit(2)
