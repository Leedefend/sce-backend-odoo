"""Create-only project skeleton write trial for Odoo shell.

Run only through:

    ENV=dev DB_NAME=sc_demo make odoo.shell.exec

The script expects the Odoo shell global ``env``. It writes exactly the approved
30-row safe-slice sample, refuses update/upsert behavior, and emits JSON/CSV
artifacts under /mnt/artifacts/migration.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


SAFE_FIELDS = [
    "legacy_project_id",
    "legacy_parent_id",
    "name",
    "short_name",
    "project_environment",
    "legacy_company_id",
    "legacy_company_name",
    "legacy_specialty_type_id",
    "specialty_type_name",
    "legacy_price_method",
    "business_nature",
    "detail_address",
    "project_profile",
    "project_area",
    "legacy_is_shared_base",
    "legacy_sort",
    "legacy_attachment_ref",
    "project_overview",
    "legacy_project_nature",
    "legacy_is_material_library",
    "other_system_id",
    "other_system_code",
]

INPUT_CSV = Path("/mnt/artifacts/migration/project_sample_v1.csv")
PRE_IDENTITY_CSV = Path("/mnt/artifacts/migration/project_existing_identity_snapshot_pre_write_v1.csv")
PRE_DRY_RUN_JSON = Path("/mnt/artifacts/migration/project_dry_run_pre_write_result_v1.json")
PRE_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/project_create_only_pre_write_snapshot_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/project_create_only_write_result_v1.json")
POST_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/project_create_only_post_write_snapshot_v1.csv")

NULL_VALUES = {"", "null", "none", "n/a", "na"}
SINGLE_LINE_FIELDS = set(SAFE_FIELDS) - {"project_profile", "project_overview"}


def clean_value(value, *, single_line=True):
    raw = "" if value is None else str(value)
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if raw.lower() in NULL_VALUES:
        return ""
    if single_line:
        raw = raw.replace("\n", " ")
        raw = re.sub(r"[ \t]+", " ", raw)
    return raw


def read_sample():
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        rows = [dict(row) for row in reader]
    missing = [field for field in SAFE_FIELDS if field not in fieldnames]
    extra = [field for field in fieldnames if field not in SAFE_FIELDS]
    if missing or extra:
        raise RuntimeError({"missing_safe_fields": missing, "unsafe_extra_fields": extra})
    return [
        {field: clean_value(row.get(field), single_line=field in SINGLE_LINE_FIELDS) for field in SAFE_FIELDS}
        for row in rows
    ]


def export_identities(model, path, ids=None):
    domain = []
    if ids is not None:
        domain = [("legacy_project_id", "in", ids)]
    elif "legacy_project_id" in model._fields:
        domain = [("legacy_project_id", "!=", False)]
    records = model.search(domain, order="id")
    fields = ["id", "legacy_project_id", "name", "other_system_id", "other_system_code"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rec in records:
            writer.writerow(
                {
                    "id": rec.id,
                    "legacy_project_id": rec.legacy_project_id or "",
                    "name": rec.name or "",
                    "other_system_id": rec.other_system_id or "",
                    "other_system_code": rec.other_system_code or "",
                }
            )
    return records


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    model = env["project.project"].sudo()  # noqa: F821 - provided by Odoo shell
    missing_model_fields = [field for field in SAFE_FIELDS if field not in model._fields]
    if missing_model_fields:
        raise RuntimeError({"missing_model_fields": missing_model_fields})

    rows = read_sample()
    ids = [row["legacy_project_id"] for row in rows]
    id_counts = Counter(ids)

    precheck_errors = []
    if len(rows) != 30:
        precheck_errors.append({"error": "sample_not_30_rows", "rows": len(rows)})
    for index, row in enumerate(rows, start=2):
        row_errors = []
        if not row["legacy_project_id"]:
            row_errors.append("missing legacy_project_id")
        if not row["name"]:
            row_errors.append("missing name")
        if row["legacy_project_id"] and id_counts[row["legacy_project_id"]] > 1:
            row_errors.append("duplicate legacy_project_id in input")
        for error in row_errors:
            precheck_errors.append({"line": index, "legacy_project_id": row["legacy_project_id"], "error": error})

    existing_records = export_identities(model, PRE_IDENTITY_CSV, ids)
    target_matches = [
        {
            "id": rec.id,
            "legacy_project_id": rec.legacy_project_id or "",
            "name": rec.name or "",
        }
        for rec in existing_records
    ]
    if target_matches:
        precheck_errors.append({"error": "target_identity_not_empty_before_write", "matches": target_matches})

    dry_run_payload = {
        "status": "PASS" if not precheck_errors else "FAIL",
        "mode": "pre_write_create_only_check",
        "row_count": len(rows),
        "safe_field_count": len(SAFE_FIELDS),
        "summary": {
            "create": 0 if precheck_errors else len(rows),
            "update": len(target_matches),
            "error": len(precheck_errors),
            "header_error": 0,
        },
        "precheck_errors": precheck_errors,
        "target_matches": target_matches,
    }
    write_json(PRE_DRY_RUN_JSON, dry_run_payload)

    export_identities(model, PRE_WRITE_SNAPSHOT_CSV, ids)
    if precheck_errors:
        env.cr.rollback()  # noqa: F821 - provided by Odoo shell
        raise RuntimeError({"pre_write_check_failed": precheck_errors})

    created = []
    try:
        for row in rows:
            vals = {field: value for field, value in row.items() if value}
            rec = model.create(vals)
            created.append(
                {
                    "id": rec.id,
                    "legacy_project_id": rec.legacy_project_id or "",
                    "name": rec.name or "",
                }
            )
        env.cr.commit()  # noqa: F821 - explicit authorized write commit
    except Exception:
        env.cr.rollback()  # noqa: F821 - provided by Odoo shell
        raise

    post_records = export_identities(model, POST_WRITE_SNAPSHOT_CSV, ids)
    post_ids = [rec.legacy_project_id for rec in post_records if rec.legacy_project_id]
    post_counts = Counter(post_ids)
    post_errors = []
    if len(post_records) != 30:
        post_errors.append({"error": "post_write_identity_count_mismatch", "count": len(post_records)})
    duplicates = sorted(identity for identity, count in post_counts.items() if count > 1)
    if duplicates:
        post_errors.append({"error": "post_write_duplicate_legacy_project_id", "ids": duplicates})

    payload = {
        "status": "PASS" if not post_errors else "FAIL",
        "mode": "create_only_write_trial",
        "database": env.cr.dbname,  # noqa: F821 - provided by Odoo shell
        "input": str(INPUT_CSV),
        "row_count": len(rows),
        "safe_field_count": len(SAFE_FIELDS),
        "summary": {
            "created": len(created),
            "updated": 0,
            "errors": len(post_errors),
            "post_write_identity_count": len(post_records),
        },
        "created": created,
        "post_errors": post_errors,
        "artifacts": {
            "pre_identity_snapshot": str(PRE_IDENTITY_CSV),
            "pre_dry_run": str(PRE_DRY_RUN_JSON),
            "pre_write_snapshot": str(PRE_WRITE_SNAPSHOT_CSV),
            "post_write_snapshot": str(POST_WRITE_SNAPSHOT_CSV),
        },
    }
    write_json(WRITE_RESULT_JSON, payload)
    print(json.dumps(payload["summary"], ensure_ascii=False))
    if post_errors:
        raise RuntimeError({"post_write_check_failed": post_errors})


main()
