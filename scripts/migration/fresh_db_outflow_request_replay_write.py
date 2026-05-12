#!/usr/bin/env python3
"""Replay outflow request headers into allowed replay databases."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv").exists():
            return candidate
    return Path.cwd()


def ensure_allowed_db() -> None:
    allowlist = {item.strip() for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_migration_fresh").split(",") if item.strip()}
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bulk_load(csv_path: Path, temp_table: str, columns: list[str]) -> None:
    env.cr.execute(f"DROP TABLE IF EXISTS {temp_table}")  # noqa: F821
    env.cr.execute(f"CREATE TEMP TABLE {temp_table} ({', '.join(f'{col} text' for col in columns)}) ON COMMIT DROP")  # noqa: F821
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        env.cr.copy_expert(  # noqa: F821
            f"COPY {temp_table} ({', '.join(columns)}) FROM STDIN WITH CSV HEADER",
            handle,
        )


def resolve_partner(partner_ref: str, partner_model):
    if not partner_ref:
        return None
    if partner_ref.startswith("legacy_partner_sc_"):
        legacy_partner_id = partner_ref.removeprefix("legacy_partner_sc_").replace("_", "-")
        partner = partner_model.search([("legacy_partner_id", "=", legacy_partner_id)], limit=1)
        if partner:
            return partner
    if partner_ref.startswith("legacy_receipt_counterparty_sc_"):
        legacy_partner_id = partner_ref.removeprefix("legacy_receipt_counterparty_sc_").replace("_", "-")
        partner = partner_model.search([("legacy_partner_source", "=", "receipt_counterparty"), ("legacy_partner_id", "=", legacy_partner_id)], limit=1)
        if partner:
            return partner
    if partner_ref.startswith("legacy_contract_counterparty_sc_"):
        legacy_partner_id = partner_ref.removeprefix("legacy_contract_counterparty_sc_").replace("_", "-")
        partner = partner_model.search([("legacy_partner_source", "=", "contract_counterparty"), ("legacy_partner_id", "=", legacy_partner_id)], limit=1)
        if partner:
            return partner
    return None


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
INPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv"
INPUT_MANIFEST = REPO_ROOT / "artifacts/migration/fresh_db_outflow_request_replay_adapter_result_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "fresh_db_outflow_request_replay_write_result_v1.json"

ensure_allowed_db()
adapter = json.loads(INPUT_MANIFEST.read_text(encoding="utf-8"))
rows = read_csv(INPUT_CSV)
expected_rows = int(adapter["expected_rows"])
payload_columns = list(rows[0].keys()) if rows else []
if rows:
    bulk_load(INPUT_CSV, "tmp_outflow_request_replay_payload", payload_columns)

Request = env["payment.request"].sudo()  # noqa: F821
Project = env["project.project"].sudo()  # noqa: F821
Contract = env["construction.contract"].sudo()  # noqa: F821
Partner = env["res.partner"].sudo()  # noqa: F821

updated_existing = 0
if rows:
    env.cr.execute(  # noqa: F821
        """
        UPDATE payment_request pr
           SET legacy_source_table = COALESCE(NULLIF(pr.legacy_source_table, ''), NULLIF(t.legacy_source_table, '')),
               legacy_record_id = COALESCE(NULLIF(pr.legacy_record_id, ''), NULLIF(t.legacy_record_id, '')),
               creator_legacy_user_id = COALESCE(NULLIF(pr.creator_legacy_user_id, ''), NULLIF(t.creator_legacy_user_id, '')),
               creator_name = COALESCE(NULLIF(pr.creator_name, ''), NULLIF(t.creator_name, '')),
               created_time = COALESCE(pr.created_time, NULLIF(t.created_time, '')::timestamp),
               write_uid = %s,
               write_date = NOW()
          FROM tmp_outflow_request_replay_payload t
         WHERE pr.note = t.note
           AND (
                (NULLIF(t.legacy_source_table, '') IS NOT NULL AND NULLIF(pr.legacy_source_table, '') IS NULL)
             OR (NULLIF(t.legacy_record_id, '') IS NOT NULL AND NULLIF(pr.legacy_record_id, '') IS NULL)
             OR (NULLIF(t.creator_legacy_user_id, '') IS NOT NULL AND NULLIF(pr.creator_legacy_user_id, '') IS NULL)
             OR (NULLIF(t.creator_name, '') IS NOT NULL AND NULLIF(pr.creator_name, '') IS NULL)
             OR (NULLIF(t.created_time, '') IS NOT NULL AND pr.created_time IS NULL)
           )
        """,
        [env.uid],  # noqa: F821
    )
    updated_existing = env.cr.rowcount  # noqa: F821

existing_note_rows = Request.search_read([("note", "in", [row["note"] for row in rows])], ["note"], order="id")
existing_notes = {row["note"] for row in existing_note_rows if row.get("note")}

created = 0
skipped = 0
for row in rows:
    if row["note"] in existing_notes:
        skipped += 1
        continue
    project = Project.search([("legacy_project_id", "=", row["project_ref"].removeprefix("legacy_project_sc_"))], limit=1)
    partner = resolve_partner(row.get("partner_ref", ""), Partner)
    contract = None
    if row.get("contract_ref"):
        contract = Contract.search([("legacy_contract_id", "=", row["contract_ref"].removeprefix("legacy_contract_sc_"))], limit=1)
    if not project:
        raise RuntimeError({"missing_project_anchor": row["project_ref"], "external_id": row["external_id"]})
    if not partner:
        raise RuntimeError({"missing_partner_anchor": row.get("partner_ref"), "external_id": row["external_id"]})
    vals = {
        "type": row["type"],
        "project_id": project.id,
        "partner_id": partner.id,
        "amount": row["amount"],
        "note": row["note"],
    }
    if row.get("date_request"):
        vals["date_request"] = row["date_request"]
    for field in [
        "legacy_source_table",
        "legacy_record_id",
        "creator_legacy_user_id",
        "creator_name",
        "created_time",
    ]:
        if row.get(field):
            vals[field] = row[field]
    if contract:
        vals["contract_id"] = contract.id
    Request.create(vals)
    created += 1

env.cr.commit()  # noqa: F821
status = "PASS" if created + skipped == expected_rows else "FAIL"
payload = {
    "status": status,
    "mode": "fresh_db_outflow_request_replay_write",
    "database": env.cr.dbname,  # noqa: F821
    "input_rows": len(rows),
    "created_rows": created,
    "skipped_existing": skipped,
    "updated_existing": updated_existing,
    "db_writes": created,
    "decision": "outflow_request_replay_write_complete" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}
write_json(OUTPUT_JSON, payload)
print("FRESH_DB_OUTFLOW_REQUEST_REPLAY_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
