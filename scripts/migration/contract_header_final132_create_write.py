"""Create-only write for the approved final 132-row contract header payload."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


PAYLOAD_CSV = Path("/mnt/artifacts/migration/contract_header_final132_authorization_payload_v1.csv")
PACKET_JSON = Path("/mnt/artifacts/migration/contract_header_final132_authorization_packet_v1.json")
PRE_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/contract_header_final132_pre_write_snapshot_v1.csv")
POST_WRITE_SNAPSHOT_CSV = Path("/mnt/artifacts/migration/contract_header_final132_post_write_snapshot_v1.csv")
WRITE_RESULT_JSON = Path("/mnt/artifacts/migration/contract_header_final132_write_result_v1.json")
ROLLBACK_TARGET_CSV = Path("/mnt/artifacts/migration/contract_header_final132_rollback_targets_v1.csv")

RUN_ID = "ITER-2026-04-15-CONTRACT-FINAL132"
EXPECTED_COUNT = 132
SAFE_FIELDS = {
    "legacy_contract_id",
    "legacy_project_id",
    "project_id",
    "partner_id",
    "subject",
    "type",
    "legacy_contract_no",
    "legacy_document_no",
    "legacy_external_contract_no",
    "legacy_status",
    "legacy_deleted_flag",
    "legacy_counterparty_text",
}


def clean(value):
    return ("" if value is None else str(value)).replace("\r\n", "\n").replace("\r", "\n").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshot(model, path, ids):
    records = model.search([("legacy_contract_id", "in", ids)], order="legacy_contract_id,id")
    fields = [
        "contract_id",
        "legacy_contract_id",
        "legacy_project_id",
        "project_id",
        "partner_id",
        "name",
        "subject",
        "type",
        "state",
        "line_count",
        "is_locked",
    ]
    rows = []
    for rec in records:
        rows.append(
            {
                "contract_id": rec.id,
                "legacy_contract_id": rec.legacy_contract_id or "",
                "legacy_project_id": rec.legacy_project_id or "",
                "project_id": rec.project_id.id or "",
                "partner_id": rec.partner_id.id or "",
                "name": rec.name or "",
                "subject": rec.subject or "",
                "type": rec.type or "",
                "state": rec.state or "",
                "line_count": len(rec.line_ids),
                "is_locked": bool(rec.is_locked),
            }
        )
    write_csv(path, fields, rows)
    return records


def build_vals(row):
    vals = {
        "legacy_contract_id": clean(row.get("legacy_contract_id")),
        "legacy_project_id": clean(row.get("legacy_project_id")),
        "project_id": int(clean(row.get("project_id"))),
        "partner_id": int(clean(row.get("partner_id"))),
        "subject": clean(row.get("subject")),
        "type": clean(row.get("type")),
        "legacy_contract_no": clean(row.get("legacy_contract_no")),
        "legacy_document_no": clean(row.get("legacy_document_no")),
        "legacy_external_contract_no": clean(row.get("legacy_external_contract_no")),
        "legacy_status": clean(row.get("legacy_status")),
        "legacy_deleted_flag": clean(row.get("legacy_deleted_flag")),
        "legacy_counterparty_text": clean(row.get("legacy_counterparty_text")),
    }
    return {field: value for field, value in vals.items() if value not in ("", None)}


def main():
    if env.cr.dbname != "sc_demo":  # noqa: F821
        raise RuntimeError({"db_name_not_sc_demo": env.cr.dbname})  # noqa: F821

    packet = json.loads(PACKET_JSON.read_text(encoding="utf-8"))
    rows = read_csv(PAYLOAD_CSV)
    ids = [clean(row.get("legacy_contract_id")) for row in rows]
    duplicate_input_ids = sorted(identity for identity, count in Counter(ids).items() if identity and count > 1)

    model = env["construction.contract"].sudo()  # noqa: F821
    project_model = env["project.project"].sudo()  # noqa: F821
    partner_model = env["res.partner"].sudo()  # noqa: F821

    pre_records = snapshot(model, PRE_WRITE_SNAPSHOT_CSV, ids)
    precheck_errors = []
    if packet.get("status") != "PASS":
        precheck_errors.append({"error": "authorization_packet_not_pass", "status": packet.get("status")})
    if packet.get("payload_rows") != EXPECTED_COUNT:
        precheck_errors.append({"error": "authorization_payload_not_132_rows", "count": packet.get("payload_rows")})
    if len(rows) != EXPECTED_COUNT:
        precheck_errors.append({"error": "payload_not_132_rows", "count": len(rows)})
    if duplicate_input_ids:
        precheck_errors.append({"error": "duplicate_input_legacy_contract_id", "ids": duplicate_input_ids})
    if pre_records:
        precheck_errors.append({"error": "pre_existing_contracts", "count": len(pre_records)})

    create_vals = []
    for row in rows:
        vals = build_vals(row)
        unsafe_fields = sorted(set(vals) - SAFE_FIELDS)
        if unsafe_fields:
            precheck_errors.append({"error": "unsafe_fields", "legacy_contract_id": vals.get("legacy_contract_id"), "fields": unsafe_fields})
        if vals.get("type") not in {"out", "in"}:
            precheck_errors.append({"error": "invalid_contract_type", "legacy_contract_id": vals.get("legacy_contract_id"), "type": vals.get("type")})
        if not project_model.browse(vals["project_id"]).exists():
            precheck_errors.append({"error": "project_missing", "legacy_contract_id": vals.get("legacy_contract_id"), "project_id": vals["project_id"]})
        if not partner_model.browse(vals["partner_id"]).exists():
            precheck_errors.append({"error": "partner_missing", "legacy_contract_id": vals.get("legacy_contract_id"), "partner_id": vals["partner_id"]})
        create_vals.append(vals)

    if precheck_errors:
        env.cr.rollback()  # noqa: F821
        raise RuntimeError({"pre_write_check_failed": precheck_errors})

    created = []
    try:
        for vals in create_vals:
            rec = model.create(vals)
            created.append(
                {
                    "contract_id": rec.id,
                    "legacy_contract_id": rec.legacy_contract_id or "",
                    "name": rec.name or "",
                    "subject": rec.subject or "",
                    "type": rec.type or "",
                    "state": rec.state or "",
                }
            )
        env.cr.commit()  # noqa: F821
    except Exception:
        env.cr.rollback()  # noqa: F821
        raise

    post_records = snapshot(model, POST_WRITE_SNAPSHOT_CSV, ids)
    grouped = {}
    for rec in post_records:
        grouped.setdefault(rec.legacy_contract_id or "", []).append(rec)

    rollback_rows = []
    for row in rows:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        for rec in grouped.get(legacy_contract_id, []):
            rollback_rows.append(
                {
                    "run_id": RUN_ID,
                    "contract_id": rec.id,
                    "legacy_contract_id": rec.legacy_contract_id or "",
                    "legacy_project_id": rec.legacy_project_id or "",
                    "project_id": rec.project_id.id or "",
                    "partner_id": rec.partner_id.id or "",
                    "name": rec.name or "",
                    "subject": rec.subject or "",
                    "type": rec.type or "",
                    "state": rec.state or "",
                    "line_count": len(rec.line_ids),
                    "is_locked": bool(rec.is_locked),
                    "write_action_result": "created",
                }
            )
    rollback_fields = [
        "run_id",
        "contract_id",
        "legacy_contract_id",
        "legacy_project_id",
        "project_id",
        "partner_id",
        "name",
        "subject",
        "type",
        "state",
        "line_count",
        "is_locked",
        "write_action_result",
    ]
    write_csv(ROLLBACK_TARGET_CSV, rollback_fields, rollback_rows)

    duplicate_matches = [
        {"legacy_contract_id": identity, "ids": [rec.id for rec in records]}
        for identity, records in sorted(grouped.items())
        if len(records) > 1
    ]
    missing_ids = [identity for identity in ids if identity not in grouped]
    post_errors = []
    if len(created) != EXPECTED_COUNT:
        post_errors.append({"error": "created_count_not_132", "created": len(created)})
    if len(post_records) != EXPECTED_COUNT:
        post_errors.append({"error": "post_write_match_count_not_132", "matched": len(post_records)})
    if len(rollback_rows) != EXPECTED_COUNT:
        post_errors.append({"error": "rollback_target_count_not_132", "count": len(rollback_rows)})
    if duplicate_matches:
        post_errors.append({"error": "duplicate_legacy_identity_matches", "duplicates": duplicate_matches})
    if missing_ids:
        post_errors.append({"error": "missing_post_write_legacy_ids", "ids": missing_ids})

    payload = {
        "status": "PASS" if not post_errors else "FAIL",
        "mode": "contract_header_final132_create_only_write",
        "database": env.cr.dbname,  # noqa: F821
        "run_id": RUN_ID,
        "expected_count": EXPECTED_COUNT,
        "created": len(created),
        "updated": 0,
        "pre_existing_count": len(pre_records),
        "post_write_match_count": len(post_records),
        "rollback_target_rows": len(rollback_rows),
        "duplicate_matches": duplicate_matches,
        "missing_ids": missing_ids,
        "post_errors": post_errors,
        "created_rows": created,
        "artifacts": {
            "pre_write_snapshot": str(PRE_WRITE_SNAPSHOT_CSV),
            "post_write_snapshot": str(POST_WRITE_SNAPSHOT_CSV),
            "rollback_targets": str(ROLLBACK_TARGET_CSV),
        },
    }
    write_json(WRITE_RESULT_JSON, payload)
    print(
        "CONTRACT_HEADER_FINAL132_CREATE_WRITE="
        + json.dumps(
            {
                "status": payload["status"],
                "created": payload["created"],
                "updated": payload["updated"],
                "rollback_target_rows": payload["rollback_target_rows"],
                "post_errors": payload["post_errors"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if post_errors:
        raise RuntimeError({"contract_header_final132_write_failed": post_errors})


main()
