"""Authorized project v3 100-row create-only write for Odoo shell."""

from __future__ import annotations

import csv
import json
from pathlib import Path


INPUT_CSV = Path("/mnt/artifacts/migration/project_next_100_candidate_v3.csv")
PACKET_JSON = Path("/mnt/artifacts/migration/project_v3_100_write_authorization_packet.json")
PRE_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/project_v3_100_pre_write_snapshot.csv")
POST_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/project_v3_100_post_write_snapshot.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/project_v3_100_write_result.json")

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
SNAPSHOT_FIELDS = ["id", "legacy_project_id", "name", "lifecycle_state", "stage_id", "stage_name", "other_system_id", "other_system_code"]
EXPECTED_COUNT = 100


def clean(value):
    return ("" if value is None else str(value)).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot_records(records):
    rows = []
    for rec in records:
        stage = rec.stage_id
        rows.append(
            {
                "id": rec.id,
                "legacy_project_id": rec.legacy_project_id or "",
                "name": rec.name or "",
                "lifecycle_state": rec.lifecycle_state or "",
                "stage_id": stage.id if stage else "",
                "stage_name": stage.display_name if stage else "",
                "other_system_id": rec.other_system_id or "",
                "other_system_code": rec.other_system_code or "",
            }
        )
    return rows


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    packet = json.loads(PACKET_JSON.read_text(encoding="utf-8"))
    if packet.get("status") != "PASS":
        raise RuntimeError({"authorization_packet_not_pass": packet.get("status")})
    if packet.get("payload_rows") != EXPECTED_COUNT:
        raise RuntimeError({"authorization_payload_not_100": packet.get("payload_rows")})
    if packet.get("write_scope", {}).get("operation") != "create_only":
        raise RuntimeError({"write_scope_not_create_only": packet.get("write_scope")})

    fieldnames, rows = read_csv(INPUT_CSV)
    missing_fields = [field for field in SAFE_FIELDS if field not in fieldnames]
    extra_fields = [field for field in fieldnames if field not in SAFE_FIELDS]
    if missing_fields or extra_fields or len(rows) != EXPECTED_COUNT:
        raise RuntimeError({"candidate_shape_invalid": {"missing": missing_fields, "extra": extra_fields, "rows": len(rows)}})

    legacy_ids = [clean(row.get("legacy_project_id")) for row in rows]
    if any(not identity for identity in legacy_ids) or len(set(legacy_ids)) != EXPECTED_COUNT:
        raise RuntimeError({"candidate_legacy_ids_invalid": True})
    if any(not clean(row.get("name")) for row in rows):
        raise RuntimeError({"candidate_name_missing": True})

    model = env["project.project"].sudo()  # noqa: F821
    missing_model_fields = [field for field in SAFE_FIELDS if field not in model._fields]
    if missing_model_fields:
        raise RuntimeError({"missing_model_fields": missing_model_fields})

    pre_records = model.search([("legacy_project_id", "in", legacy_ids)], order="legacy_project_id,id")
    write_csv(PRE_WRITE_SNAPSHOT_CSV, SNAPSHOT_FIELDS, snapshot_records(pre_records))
    if pre_records:
        raise RuntimeError({"pre_existing_project_matches": snapshot_records(pre_records)})

    created = []
    try:
        for row in rows:
            vals = {field: clean(row.get(field)) for field in SAFE_FIELDS if clean(row.get(field))}
            rec = model.create(vals)
            created.append(rec)
        env.cr.commit()  # noqa: F821
    except Exception:
        env.cr.rollback()  # noqa: F821
        raise

    post_records = model.search([("legacy_project_id", "in", legacy_ids)], order="id")
    post_rows = snapshot_records(post_records)
    write_csv(POST_WRITE_SNAPSHOT_CSV, SNAPSHOT_FIELDS, post_rows)

    post_errors = []
    if len(post_records) != EXPECTED_COUNT:
        post_errors.append("post_write_identity_count_not_100")
    if len({row["legacy_project_id"] for row in post_rows}) != EXPECTED_COUNT:
        post_errors.append("post_write_duplicate_legacy_project_id")

    projection_mismatches = []
    for rec in post_records:
        expected_stage = rec._get_stage_for_lifecycle(rec.lifecycle_state)
        if expected_stage and rec.stage_id != expected_stage:
            projection_mismatches.append(
                {
                    "id": rec.id,
                    "legacy_project_id": rec.legacy_project_id or "",
                    "stage_id": rec.stage_id.id or False,
                    "expected_stage_id": expected_stage.id,
                }
            )
    if projection_mismatches:
        post_errors.append("stage_projection_mismatches")

    payload = {
        "status": "PASS" if not post_errors else "PASS_WITH_POST_ERRORS",
        "mode": "project_v3_100_create_only_write",
        "database": env.cr.dbname,  # noqa: F821
        "input": str(INPUT_CSV),
        "row_count": len(rows),
        "safe_field_count": len(SAFE_FIELDS),
        "summary": {
            "created": len(created),
            "updated": 0,
            "errors": 0,
            "post_write_identity_count": len(post_records),
            "projection_mismatches": len(projection_mismatches),
        },
        "created": post_rows,
        "post_errors": post_errors,
        "artifacts": {
            "pre_write_snapshot": str(PRE_WRITE_SNAPSHOT_CSV),
            "post_write_snapshot": str(POST_WRITE_SNAPSHOT_CSV),
        },
    }
    write_json(WRITE_RESULT_JSON, payload)
    print(
        "PROJECT_V3_100_WRITE_RESULT="
        + json.dumps(payload["summary"] | {"status": payload["status"]}, ensure_ascii=False, sort_keys=True)
    )
    if post_errors:
        raise RuntimeError({"project_v3_write_post_errors": post_errors})


main()
