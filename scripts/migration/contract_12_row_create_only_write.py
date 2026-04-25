"""Create-only write for the authorized 12-row contract payload.

Run only through:

    DB_NAME=sc_demo make odoo.shell.exec < scripts/migration/contract_12_row_create_only_write.py

The script expects the Odoo shell global ``env``. It creates exactly the
authorized 12 construction.contract rows and emits rollback targets keyed by
legacy_contract_id.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/contract_12_row_write_authorization_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821 - provided by Odoo shell
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))

PAYLOAD_CSV = REPO_ROOT / "artifacts/migration/contract_12_row_write_authorization_payload_v1.csv"
PACKET_JSON = REPO_ROOT / "artifacts/migration/contract_12_row_write_authorization_packet_v1.json"
PRE_WRITE_SNAPSHOT_CSV = ARTIFACT_ROOT / "contract_12_row_pre_write_snapshot_v1.csv"
POST_WRITE_SNAPSHOT_CSV = ARTIFACT_ROOT / "contract_12_row_post_write_snapshot_v1.csv"
WRITE_RESULT_JSON = ARTIFACT_ROOT / "contract_12_row_write_result_v1.json"
ROLLBACK_TARGET_CSV = ARTIFACT_ROOT / "contract_12_row_rollback_target_list_v1.csv"
RESOLUTION_CSV = ARTIFACT_ROOT / "contract_12_row_missing_partner_anchor_resolution_v1.csv"

RUN_ID = "ITER-2026-04-14-0004"
EXPECTED_COUNT = 12
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


def contract_domain(ids):
    return [("legacy_contract_id", "in", ids)]


SNAPSHOT_FIELDS = [
    "contract_id",
    "legacy_contract_id",
    "legacy_project_id",
    "project_id",
    "project_name",
    "partner_id",
    "partner_name",
    "name",
    "subject",
    "type",
    "state",
    "legacy_contract_no",
    "legacy_document_no",
    "legacy_external_contract_no",
    "legacy_status",
    "legacy_deleted_flag",
    "legacy_counterparty_text",
    "line_count",
    "payment_request_count",
    "settlement_count",
    "is_locked",
]


def snapshot(model, path, ids):
    records = model.search(contract_domain(ids), order="legacy_contract_id,id")
    rows = []
    for rec in records:
        rows.append(
            {
                "contract_id": rec.id,
                "legacy_contract_id": rec.legacy_contract_id or "",
                "legacy_project_id": rec.legacy_project_id or "",
                "project_id": rec.project_id.id or "",
                "project_name": rec.project_id.display_name or "",
                "partner_id": rec.partner_id.id or "",
                "partner_name": rec.partner_id.display_name or "",
                "name": rec.name or "",
                "subject": rec.subject or "",
                "type": rec.type or "",
                "state": rec.state or "",
                "legacy_contract_no": rec.legacy_contract_no or "",
                "legacy_document_no": rec.legacy_document_no or "",
                "legacy_external_contract_no": rec.legacy_external_contract_no or "",
                "legacy_status": rec.legacy_status or "",
                "legacy_deleted_flag": rec.legacy_deleted_flag or "",
                "legacy_counterparty_text": rec.legacy_counterparty_text or "",
                "line_count": len(rec.line_ids),
                "payment_request_count": rec.payment_request_count,
                "settlement_count": rec.settlement_count,
                "is_locked": bool(rec.is_locked),
            }
        )
    write_csv(path, SNAPSHOT_FIELDS, rows)
    return records


def build_vals(row):
    vals = {
        "legacy_contract_id": clean(row.get("legacy_contract_id")),
        "legacy_project_id": clean(row.get("legacy_project_id")),
        "project_id": int(clean(row.get("project_id"))) if clean(row.get("project_id")) else None,
        "partner_id": int(clean(row.get("partner_id"))) if clean(row.get("partner_id")) else None,
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


def resolve_project_id(row, project_model):
    legacy_project_id = clean(row.get("legacy_project_id"))
    if legacy_project_id:
        matches = project_model.search([("legacy_project_id", "=", legacy_project_id)], limit=2)
        if len(matches) == 1:
            return matches.id
        if len(matches) > 1:
            raise RuntimeError({"duplicate_legacy_project_matches": legacy_project_id, "project_ids": matches.ids})
    project_id = clean(row.get("project_id"))
    if project_id:
        rec = project_model.browse(int(project_id)).exists()
        if rec:
            return rec.id
    return None


def resolve_partner_id(row, partner_model):
    if RESOLUTION_CSV.exists():
        _columns, resolution_rows = read_csv(RESOLUTION_CSV)
        resolution = {clean(item.get("anchor_name")): int(clean(item.get("partner_id"))) for item in resolution_rows if clean(item.get("partner_id"))}
        partner_text = clean(row.get("legacy_counterparty_text"))
        if partner_text in resolution:
            return resolution[partner_text]
    partner_id = clean(row.get("partner_id"))
    if partner_id:
        rec = partner_model.browse(int(partner_id)).exists()
        if rec:
            return rec.id
    partner_text = clean(row.get("legacy_counterparty_text"))
    if partner_text:
        matches = partner_model.search([("name", "=", partner_text)], limit=2)
        if len(matches) == 1:
            return matches.id
        if len(matches) > 1:
            raise RuntimeError({"duplicate_partner_name_matches": partner_text, "partner_ids": matches.ids})
    return None


def main():
    ensure_allowed_db()

    packet = json.loads(PACKET_JSON.read_text(encoding="utf-8"))
    _columns, rows = read_csv(PAYLOAD_CSV)
    ids = [clean(row.get("legacy_contract_id")) for row in rows]
    id_counts = Counter(ids)
    duplicate_input_ids = sorted(identity for identity, count in id_counts.items() if identity and count > 1)
    model = env["construction.contract"].sudo()  # noqa: F821
    project_model = env["project.project"].sudo()  # noqa: F821
    partner_model = env["res.partner"].sudo()  # noqa: F821

    pre_records = snapshot(model, PRE_WRITE_SNAPSHOT_CSV, ids)
    precheck_errors = []
    if packet.get("status") != "PASS":
        precheck_errors.append({"error": "authorization_packet_not_pass", "status": packet.get("status")})
    if len(rows) != EXPECTED_COUNT:
        precheck_errors.append({"error": "payload_not_12_rows", "count": len(rows)})
    if duplicate_input_ids:
        precheck_errors.append({"error": "duplicate_input_legacy_contract_id", "ids": duplicate_input_ids})
    pre_existing_by_legacy = {rec.legacy_contract_id or "": rec for rec in pre_records}

    create_vals = []
    for row in rows:
        vals = build_vals(row)
        if vals.get("legacy_contract_id") in pre_existing_by_legacy:
            continue
        resolved_project_id = resolve_project_id(row, project_model)
        resolved_partner_id = resolve_partner_id(row, partner_model)
        if resolved_project_id:
            vals["project_id"] = resolved_project_id
        if resolved_partner_id:
            vals["partner_id"] = resolved_partner_id
        unsafe_fields = sorted(set(vals) - SAFE_FIELDS)
        if unsafe_fields:
            precheck_errors.append({"error": "unsafe_fields", "legacy_contract_id": vals.get("legacy_contract_id"), "fields": unsafe_fields})
        if vals.get("type") not in {"out", "in"}:
            precheck_errors.append({"error": "invalid_contract_type", "legacy_contract_id": vals.get("legacy_contract_id"), "type": vals.get("type")})
        if not vals.get("project_id") or not project_model.browse(vals["project_id"]).exists():
            precheck_errors.append({"error": "project_missing", "legacy_contract_id": vals.get("legacy_contract_id"), "project_id": vals["project_id"]})
        if not vals.get("partner_id") or not partner_model.browse(vals["partner_id"]).exists():
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
        env.cr.commit()  # noqa: F821 - explicit authorized write commit
    except Exception:
        env.cr.rollback()  # noqa: F821
        raise

    post_records = snapshot(model, POST_WRITE_SNAPSHOT_CSV, ids)
    grouped = {}
    for rec in post_records:
        grouped.setdefault(rec.legacy_contract_id or "", []).append(rec)

    duplicate_matches = [
        {"legacy_contract_id": identity, "ids": [rec.id for rec in records]}
        for identity, records in sorted(grouped.items())
        if len(records) > 1
    ]
    missing_ids = [identity for identity in ids if identity not in grouped]
    out_of_scope = [
        {
            "contract_id": rec.id,
            "legacy_contract_id": rec.legacy_contract_id or "",
            "name": rec.name or "",
        }
        for rec in post_records
        if (rec.legacy_contract_id or "") not in id_counts
    ]

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
                    "payment_request_count": rec.payment_request_count,
                    "settlement_count": rec.settlement_count,
                    "is_locked": bool(rec.is_locked),
                    "write_action_result": "created",
                }
            )
    write_csv(
        ROLLBACK_TARGET_CSV,
        [
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
            "payment_request_count",
            "settlement_count",
            "is_locked",
            "write_action_result",
        ],
        rollback_rows,
    )

    post_errors = []
    skipped_existing = len(pre_existing_by_legacy)
    if len(created) + skipped_existing != EXPECTED_COUNT:
        post_errors.append({"error": "resolved_count_not_12", "created": len(created), "skipped_existing": skipped_existing})
    if len(post_records) != EXPECTED_COUNT:
        post_errors.append({"error": "post_write_identity_count_mismatch", "count": len(post_records)})
    if duplicate_matches:
        post_errors.append({"error": "duplicate_legacy_contract_identity", "rows": duplicate_matches})
    if missing_ids:
        post_errors.append({"error": "missing_post_write_identity", "ids": missing_ids})
    if out_of_scope:
        post_errors.append({"error": "out_of_scope_post_write_match", "rows": out_of_scope})
    if any(row["line_count"] for row in rollback_rows):
        post_errors.append({"error": "contract_lines_created"})
    if any(row["payment_request_count"] or row["settlement_count"] for row in rollback_rows):
        post_errors.append({"error": "payment_or_settlement_linkage_created"})

    payload = {
        "status": "PASS" if not post_errors else "FAIL",
        "mode": "contract_12_row_create_only_write",
        "database": env.cr.dbname,  # noqa: F821
        "input": str(PAYLOAD_CSV),
        "row_count": len(rows),
        "safe_field_count": len(SAFE_FIELDS),
        "rollback_key": "legacy_contract_id",
        "summary": {
            "created": len(created),
            "skipped_existing": skipped_existing,
            "updated": 0,
            "errors": len(post_errors),
            "post_write_identity_count": len(post_records),
            "rollback_targets": len(rollback_rows),
        },
        "created": created,
        "post_errors": post_errors,
        "artifacts": {
            "pre_write_snapshot": str(PRE_WRITE_SNAPSHOT_CSV),
            "post_write_snapshot": str(POST_WRITE_SNAPSHOT_CSV),
            "rollback_target_list": str(ROLLBACK_TARGET_CSV),
        },
    }
    write_json(WRITE_RESULT_JSON, payload)
    print("CONTRACT_12_ROW_WRITE_RESULT=" + json.dumps(payload["summary"], ensure_ascii=False, sort_keys=True))
    if post_errors:
        raise RuntimeError({"post_write_check_failed": post_errors})


main()
