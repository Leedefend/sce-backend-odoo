#!/usr/bin/env python3
"""Probe user-visible business fact coverage against packaged legacy payloads.

This probe intentionally validates deterministic legacy fact identity coverage.
It does not force legacy data into new-system semantic categories when the old
system has no direct equivalent.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Iterable


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_replay_manifest_v1.json").exists():
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
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/adhoc")  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def csv_ids(file_name: str, field_name: str) -> set[str]:
    path = REPO_ROOT / "artifacts/migration" / file_name
    if not path.exists():
        return set()
    return {clean(row.get(field_name)) for row in read_csv(path) if clean(row.get(field_name))}


def target_values(model_name: str, field_name: str, domain: list[tuple] | None = None) -> set[str]:
    if model_name not in env:  # noqa: F821
        return set()
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    if field_name not in Model._fields:
        return set()
    values = Model.search(domain or []).mapped(field_name)
    return {clean(value) for value in values if clean(value)}


def note_marker_values(model_name: str, token: str) -> set[str]:
    if model_name not in env:  # noqa: F821
        return set()
    Model = env[model_name].sudo().with_context(active_test=False)  # noqa: F821
    if "note" not in Model._fields:
        return set()
    values: set[str] = set()
    for record in Model.search([("note", "ilike", token)]):
        note = clean(record.note)
        start = note.find(token)
        if start < 0:
            continue
        raw = note[start + len(token) :].split()[0].split(";")[0].strip()
        if raw:
            values.add(raw)
    return values


def count(model_name: str, domain: list[tuple] | None = None, *, user_login: str | None = None) -> int | None:
    if model_name not in env:  # noqa: F821
        return None
    Model = env[model_name].with_context(active_test=False)  # noqa: F821
    if user_login:
        user = env["res.users"].sudo().search([("login", "=", user_login)], limit=1)  # noqa: F821
        if not user:
            return None
        Model = Model.with_user(user)
    else:
        Model = Model.sudo()
    try:
        return Model.search_count(domain or [])
    except Exception:
        return None


def lane(
    key: str,
    label: str,
    payload_ids: Iterable[str],
    target_ids: Iterable[str],
    *,
    target_model: str,
    target_domain: list[tuple] | None = None,
    user_login: str = "wutao",
) -> dict[str, object]:
    payload = {item for item in payload_ids if item}
    target = {item for item in target_ids if item}
    missing = sorted(payload - target)
    extra = sorted(target - payload)
    sudo_count = count(target_model, target_domain)
    user_count = count(target_model, target_domain, user_login=user_login)
    permission_gap = None
    if isinstance(sudo_count, int) and isinstance(user_count, int):
        permission_gap = sudo_count - user_count
    status = "PASS" if not missing and permission_gap in (0, None) else "FAIL"
    return {
        "key": key,
        "label": label,
        "status": status,
        "target_model": target_model,
        "payload_identity_count": len(payload),
        "target_identity_count": len(target),
        "missing_identity_count": len(missing),
        "extra_identity_count": len(extra),
        "missing_identity_samples": missing[:20],
        "extra_identity_samples": extra[:20],
        "target_count_sudo": sudo_count,
        "target_count_user": user_count,
        "permission_gap": permission_gap,
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_report(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# User Visible Business Fact Alignment Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        "",
        "## Deterministic Lanes",
        "",
        "| lane | status | payload identities | target identities | missing | permission gap |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["lanes"]:
        lines.append(
            "| {label} | {status} | {payload_identity_count} | {target_identity_count} | "
            "{missing_identity_count} | {permission_gap} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## User Priority Plan",
            "",
            "```json",
            json.dumps(payload["user_priority_plan"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Boundary",
            "",
            "The probe checks old-system fact identities carried into the new database. It does not require old data to satisfy new customer/supplier or projection-only semantics when no deterministic legacy source key exists.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


REPO_ROOT = repo_root()
ARTIFACT_ROOT = artifact_root()
OUTPUT_JSON = ARTIFACT_ROOT / "user_visible_business_fact_alignment_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "user_visible_business_fact_alignment_probe_report_v1.md"

payment_target_ids = target_values("payment.request", "legacy_record_id")
receipt_note_ids = note_marker_values("payment.request", "legacy_receipt_id=")

lanes = [
    lane(
        "project_master",
        "项目主数据",
        csv_ids("fresh_db_project_anchor_replay_payload_v1.csv", "legacy_project_id"),
        target_values("project.project", "legacy_project_id"),
        target_model="project.project",
        target_domain=[("legacy_project_id", "!=", False)],
    ),
    lane(
        "partner_master",
        "往来单位主数据",
        csv_ids("fresh_db_partner_l4_replay_payload_v1.csv", "legacy_partner_id"),
        target_values("res.partner", "legacy_partner_id"),
        target_model="res.partner",
        target_domain=[("legacy_partner_id", "!=", False)],
    ),
    lane(
        "contract_headers",
        "合同台账事实",
        csv_ids("fresh_db_contract_remaining_replay_payload_v1.csv", "legacy_contract_id")
        | csv_ids("fresh_db_supplier_contract_replay_payload_v1.csv", "legacy_contract_id"),
        target_values("construction.contract", "legacy_contract_id"),
        target_model="construction.contract",
        target_domain=[("legacy_contract_id", "!=", False)],
    ),
    lane(
        "payment_requests",
        "付款申请事实",
        csv_ids("fresh_db_outflow_request_replay_payload_v1.csv", "legacy_record_id")
        | csv_ids("fresh_db_actual_outflow_replay_payload_v1.csv", "legacy_record_id"),
        payment_target_ids,
        target_model="payment.request",
        target_domain=[("type", "=", "pay")],
    ),
    lane(
        "receipt_requests",
        "收款事实",
        csv_ids("fresh_db_receipt_write_design_payload_v1.csv", "legacy_receipt_id"),
        payment_target_ids | receipt_note_ids,
        target_model="payment.request",
        target_domain=[],
    ),
    lane(
        "payment_request_lines",
        "付款明细事实",
        csv_ids("fresh_db_outflow_request_line_replay_payload_v1.csv", "legacy_line_id")
        | csv_ids("fresh_db_actual_outflow_line_replay_payload_v1.csv", "legacy_line_id"),
        target_values("payment.request.line", "legacy_line_id"),
        target_model="payment.request.line",
        target_domain=[("legacy_line_id", "!=", False)],
    ),
    lane(
        "invoice_registration_lines",
        "发票登记明细事实",
        csv_ids("fresh_db_legacy_invoice_registration_line_replay_payload_v1.csv", "legacy_line_id"),
        target_values("sc.legacy.invoice.registration.line", "legacy_line_id"),
        target_model="sc.legacy.invoice.registration.line",
        target_domain=[("legacy_line_id", "!=", False)],
    ),
    lane(
        "fund_daily_lines",
        "资金日报明细事实",
        csv_ids("fresh_db_legacy_fund_daily_line_replay_payload_v1.csv", "legacy_line_id"),
        target_values("sc.legacy.fund.daily.line", "legacy_line_id"),
        target_model="sc.legacy.fund.daily.line",
        target_domain=[("legacy_line_id", "!=", False)],
    ),
]

Plan = env["sc.legacy.user.priority.menu.plan"].sudo().with_context(active_test=False)  # noqa: F821
plan_domain = [("source_document", "=", "/home/odoo/workspace/partner_import_source/5.6优化（老系统菜单，字段列表展示）1.docx")]
plan_count = Plan.search_count(plan_domain) if "sc.legacy.user.priority.menu.plan" in env else 0  # noqa: F821
verified_count = Plan.search_count(plan_domain + [("replay_status", "=", "verified")]) if plan_count else 0
group_counts = {}
if plan_count:
    group_counts = {
        row.get("legacy_menu_group") or "": row.get("legacy_menu_group_count") or row.get("__count") or 0
        for row in Plan.read_group(plan_domain, ["legacy_menu_group"], ["legacy_menu_group"], lazy=False)
    }

errors = []
for row in lanes:
    if row["status"] != "PASS":
        errors.append(
            {
                "lane": row["key"],
                "missing_identity_count": row["missing_identity_count"],
                "permission_gap": row["permission_gap"],
            }
        )
if plan_count != 55 or verified_count != 55:
    errors.append({"lane": "user_priority_plan", "expected": 55, "row_count": plan_count, "verified_count": verified_count})

status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "user_visible_business_fact_alignment_probe",
    "database": env.cr.dbname,  # noqa: F821
    "lanes": lanes,
    "user_priority_plan": {
        "expected_rows": 55,
        "row_count": plan_count,
        "verified_count": verified_count,
        "group_counts": group_counts,
    },
    "errors": errors,
    "db_writes": 0,
    "decision": "user_visible_business_fact_alignment_passed" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
write_report(OUTPUT_REPORT, payload)
print("USER_VISIBLE_BUSINESS_FACT_ALIGNMENT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if errors:
    raise SystemExit(2)
