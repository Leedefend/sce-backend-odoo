# -*- coding: utf-8 -*-
"""Replay legacy social-security registration facts into the HR payroll surface."""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime
from pathlib import Path


SOURCE_TABLE = "BGGL_XZ_JXDJ"
INPUT_CSV_NAME = "fresh_db_legacy_social_security_registration_payload_v1.csv"
FACT_TYPE = "social_registration"


def ensure_allowed_db():
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration" / INPUT_CSV_NAME).exists():
            return candidate
    return Path.cwd()


def artifact_root() -> Path:
    root = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("HISTORY_CONTINUITY_ARTIFACT_ROOT")
    return Path(root) if root else repo_root() / "artifacts/migration"


def input_csv() -> Path:
    env_path = os.getenv("MIGRATION_SOCIAL_SECURITY_REGISTRATION_CSV")
    candidates = [Path(env_path)] if env_path else []
    candidates.append(repo_root() / "artifacts/migration" / INPUT_CSV_NAME)
    candidates.append(Path("/mnt/artifacts/migration") / INPUT_CSV_NAME)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("missing social security registration csv: %s" % [str(c) for c in candidates])


def clean(value):
    return "" if value is None else str(value).strip()


def parse_float(value):
    text = clean(value)
    return float(text) if text else 0.0


def parse_int(value):
    try:
        return int(float(clean(value)))
    except Exception:
        return 0


def parse_date(value):
    text = clean(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def bool_active(value):
    return clean(value) not in {"0", "False", "false"}


def period_date(year, month):
    if year and month:
        return parse_date("%04d-%02d-01" % (year, month))
    return None


def department_id_by_name(name):
    text = clean(name)
    if not text:
        return None
    dept = env["hr.department"].sudo().search([("name", "=", text)], limit=1)  # noqa: F821
    if not dept:
        dept = env["hr.department"].sudo().search([("name", "ilike", text)], limit=1)  # noqa: F821
    return dept.id or None


ensure_allowed_db()

output_json = artifact_root() / "fresh_db_legacy_social_security_registration_write_result_v1.json"
output_json.parent.mkdir(parents=True, exist_ok=True)
source_csv = input_csv()

Model = env["sc.hr.payroll.document"].sudo().with_context(active_test=False)  # noqa: F821
existing = {
    rec["legacy_source_id"]
    for rec in Model.search_read(
        [("legacy_source_table", "=", SOURCE_TABLE), ("legacy_source_id", "!=", False)],
        ["legacy_source_id"],
        limit=False,
    )
}

created = 0
updated = 0
skipped = 0
active_rows = 0
amount_2026_by_type = {}
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821

with source_csv.open(newline="", encoding="utf-8-sig") as handle:
    for row in csv.DictReader(handle):
        legacy_line_id = clean(row.get("legacy_line_id"))
        if not legacy_line_id:
            skipped += 1
            continue
        legacy_source_id = "%s:social_registration" % legacy_line_id
        year = parse_int(row.get("period_year"))
        month = parse_int(row.get("period_month"))
        amount = parse_float(row.get("amount"))
        if amount <= 0:
            skipped += 1
            continue
        person_type = clean(row.get("person_type")) or "社保登记"
        occurrence_date = period_date(year, month) or parse_date(row.get("created_time"))
        is_active = bool_active(row.get("active"))
        values = {
            "name": "社保登记 - %s %s-%02d" % (clean(row.get("employee_name")) or "历史人员", year or 0, month or 0),
            "document_no": clean(row.get("document_no")) or None,
            "fact_type": FACT_TYPE,
            "state": "done" if clean(row.get("document_state")) == "2" else "in_progress",
            "business_date": occurrence_date,
            "department_id": department_id_by_name(row.get("department_name")),
            "employee_name": clean(row.get("employee_name")) or None,
            "period_year": year,
            "period_month": month,
            "payer_unit": clean(row.get("payer_unit")) or None,
            "company_amount": amount,
            "individual_amount": 0.0,
            "amount": amount,
            "item_type": person_type,
            "occurrence_date": occurrence_date,
            "description": "\n".join(
                [
                    "来源表: BGGL_XZ_JXDJ",
                    "来源主表: BGGL_XZ_JXDJ_ZB",
                    "人员类型: %s" % person_type,
                    "岗位: %s" % (clean(row.get("position_name")) or ""),
                    "联系电话: %s" % (clean(row.get("contact")) or ""),
                    "备注: %s" % (clean(row.get("note")) or ""),
                ]
            ),
            "legacy_document_no": clean(row.get("document_no")) or None,
            "legacy_document_state": clean(row.get("document_state")) or None,
            "legacy_source_table": SOURCE_TABLE,
            "legacy_source_id": legacy_source_id,
            "currency_id": currency_id,
            "active": is_active,
        }
        if year == 2026 and is_active:
            amount_2026_by_type[person_type] = amount_2026_by_type.get(person_type, 0.0) + amount
        if is_active:
            active_rows += 1
        if legacy_source_id in existing:
            rec = Model.search([("legacy_source_table", "=", SOURCE_TABLE), ("legacy_source_id", "=", legacy_source_id)], limit=1)
            rec.write(values)
            updated += 1
            continue
        Model.create(values)
        existing.add(legacy_source_id)
        created += 1

env.cr.commit()  # noqa: F821

result = {
    "mode": "fresh_db_legacy_social_security_registration_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_csv": str(source_csv),
    "source_table": SOURCE_TABLE,
    "target_model": "sc.hr.payroll.document",
    "created": created,
    "updated": updated,
    "skipped": skipped,
    "active_rows": active_rows,
    "amount_2026_by_type": {key: round(value, 2) for key, value in sorted(amount_2026_by_type.items())},
    "decision": "legacy_social_security_registration_replay_complete",
}
output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
