"""Sync payment.request state from downstream legacy actual-outflow facts.

Run through Odoo shell:
SYNC_MODE=check odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/legacy_payment_approval_downstream_fact_state_sync.py
SYNC_MODE=write odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/legacy_payment_approval_downstream_fact_state_sync.py
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from decimal import Decimal
from pathlib import Path


INPUT_CSV = Path("/mnt/artifacts/migration/legacy_payment_approval_downstream_fact_screen_rows_v1.csv")
OUTPUT_JSON = Path("/mnt/artifacts/migration/legacy_payment_approval_downstream_fact_state_sync_result_v1.json")
SNAPSHOT_CSV = Path("/mnt/artifacts/migration/legacy_payment_approval_downstream_fact_state_sync_snapshot_v1.csv")
ROLLBACK_CSV = Path("/mnt/artifacts/migration/legacy_payment_approval_downstream_fact_state_sync_rollback_v1.csv")

RUN_ID = "ITER-2026-04-17-LEGACY-PAYMENT-APPROVAL-DOWNSTREAM-FACT-STATE-SYNC"
EXPECTED_TARGETS = 12194
TARGET_FACT = "historical_approved_by_downstream_business_fact"
TARGET_DB = "sc_demo"


def clean(value):
    return ("" if value is None else str(value)).strip()


def read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def decimal_text(value):
    if value is None:
        return "0.00"
    return format(Decimal(str(value)).quantize(Decimal("0.01")), "f")


def fetchall_dict(query, params=None):
    env.cr.execute(query, params or ())  # noqa: F821
    columns = [item[0] for item in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def main():
    mode = clean(os.environ.get("SYNC_MODE") or "check")
    if mode not in {"check", "write"}:
        raise RuntimeError({"invalid_sync_mode": mode})
    if env.cr.dbname != TARGET_DB:  # noqa: F821
        raise RuntimeError({"database_not_sc_demo": env.cr.dbname})  # noqa: F821

    fields, rows = read_csv(INPUT_CSV)
    required_fields = {
        "target_external_id",
        "target_lane",
        "final_approval_fact",
        "actual_outflow_count",
        "actual_outflow_amount",
        "sample_downstream_external_ids",
    }
    missing = sorted(required_fields - set(fields))
    if missing:
        raise RuntimeError({"missing_input_columns": missing})

    target_rows = [
        row
        for row in rows
        if clean(row.get("final_approval_fact")) == TARGET_FACT
        and clean(row.get("target_lane")) == "outflow_request"
        and int(clean(row.get("actual_outflow_count")) or "0") > 0
    ]
    target_external_ids = [clean(row.get("target_external_id")) for row in target_rows]
    duplicate_targets = [key for key, count in Counter(target_external_ids).items() if count > 1]
    if len(target_rows) != EXPECTED_TARGETS or len(target_external_ids) != EXPECTED_TARGETS:
        raise RuntimeError({"target_count_drift": len(target_rows), "expected": EXPECTED_TARGETS})
    if duplicate_targets:
        raise RuntimeError({"duplicate_target_external_ids": duplicate_targets[:20]})

    evidence_by_external_id = {clean(row.get("target_external_id")): row for row in target_rows}

    imd_rows = fetchall_dict(
        """
        SELECT name, res_id
          FROM ir_model_data
         WHERE module = %s
           AND model = %s
           AND name = ANY(%s)
        """,
        ("migration_assets", "payment.request", target_external_ids),
    )
    res_id_by_external = {clean(row["name"]): int(row["res_id"]) for row in imd_rows}
    missing_external = sorted(set(target_external_ids) - set(res_id_by_external))
    if missing_external:
        raise RuntimeError({"missing_external_id_resolution": missing_external[:50], "count": len(missing_external)})

    ids = sorted(res_id_by_external.values())
    request_rows = fetchall_dict(
        """
        SELECT pr.id,
               imd.name AS external_id,
               pr.name,
               pr.state,
               pr.validation_status,
               pr.amount,
               pr.project_id,
               pr.partner_id,
               pr.currency_id,
               pr.company_id,
               COALESCE(ledger.ledger_count, 0) AS ledger_count,
               COALESCE(ledger.ledger_sum, 0) AS ledger_sum
          FROM payment_request pr
          JOIN ir_model_data imd
            ON imd.module = 'migration_assets'
           AND imd.model = 'payment.request'
           AND imd.res_id = pr.id
          LEFT JOIN (
                SELECT payment_request_id,
                       COUNT(*) AS ledger_count,
                       COALESCE(SUM(amount), 0) AS ledger_sum
                  FROM payment_ledger
                 WHERE payment_request_id = ANY(%s)
                 GROUP BY payment_request_id
          ) ledger ON ledger.payment_request_id = pr.id
         WHERE pr.id = ANY(%s)
           AND imd.name = ANY(%s)
        """,
        (ids, ids, target_external_ids),
    )
    if len(request_rows) != EXPECTED_TARGETS:
        raise RuntimeError({"payment_request_count_drift": len(request_rows), "expected": EXPECTED_TARGETS})

    snapshot_rows = []
    rollback_rows = []
    already_done = 0
    needs_state_sync = 0
    needs_ledger_create = 0
    needs_ledger_update = 0
    ledger_conflicts = []
    for row in request_rows:
        external_id = clean(row["external_id"])
        evidence = evidence_by_external_id[external_id]
        ledger_count = int(row["ledger_count"] or 0)
        ledger_sum = Decimal(str(row["ledger_sum"] or "0"))
        amount = Decimal(str(row["amount"] or "0"))
        if ledger_count > 1:
            ledger_conflicts.append({"id": row["id"], "external_id": external_id, "ledger_count": ledger_count})
        old_state = clean(row["state"])
        old_validation_status = clean(row["validation_status"])
        if old_state == "done" and old_validation_status == "validated":
            already_done += 1
        else:
            needs_state_sync += 1
        if ledger_count == 0:
            needs_ledger_create += 1
        elif ledger_sum != amount:
            needs_ledger_update += 1
        snapshot_rows.append(
            {
                "payment_request_id": row["id"],
                "external_id": external_id,
                "name": clean(row["name"]),
                "old_state": old_state,
                "old_validation_status": old_validation_status,
                "amount": decimal_text(amount),
                "old_ledger_count": ledger_count,
                "old_ledger_sum": decimal_text(ledger_sum),
                "actual_outflow_count": clean(evidence.get("actual_outflow_count")),
                "actual_outflow_amount": clean(evidence.get("actual_outflow_amount")),
                "sample_downstream_external_ids": clean(evidence.get("sample_downstream_external_ids")),
            }
        )
        rollback_rows.append(
            {
                "payment_request_id": row["id"],
                "external_id": external_id,
                "restore_state": old_state,
                "restore_validation_status": old_validation_status,
                "delete_ledger_ref": f"{RUN_ID}:{external_id}",
                "old_ledger_count": ledger_count,
                "old_ledger_sum": decimal_text(ledger_sum),
            }
        )
    if ledger_conflicts:
        raise RuntimeError({"multiple_ledger_rows_found": ledger_conflicts[:50], "count": len(ledger_conflicts)})

    write_csv(
        SNAPSHOT_CSV,
        [
            "payment_request_id",
            "external_id",
            "name",
            "old_state",
            "old_validation_status",
            "amount",
            "old_ledger_count",
            "old_ledger_sum",
            "actual_outflow_count",
            "actual_outflow_amount",
            "sample_downstream_external_ids",
        ],
        snapshot_rows,
    )
    write_csv(
        ROLLBACK_CSV,
        [
            "payment_request_id",
            "external_id",
            "restore_state",
            "restore_validation_status",
            "delete_ledger_ref",
            "old_ledger_count",
            "old_ledger_sum",
        ],
        rollback_rows,
    )

    db_writes = 0
    if mode == "write":
        uid = int(env.user.id or 1)  # noqa: F821
        env.cr.execute(  # noqa: F821
            """
            INSERT INTO payment_ledger (
                payment_request_id,
                project_id,
                partner_id,
                currency_id,
                company_id,
                amount,
                paid_at,
                ref,
                note,
                create_uid,
                write_uid,
                create_date,
                write_date
            )
            SELECT pr.id,
                   pr.project_id,
                   pr.partner_id,
                   pr.currency_id,
                   pr.company_id,
                   pr.amount,
                   NOW(),
                   %s || ':' || imd.name,
                   'legacy downstream actual-outflow fact state sync; actual_outflow evidence recorded in rollback snapshot',
                   %s,
                   %s,
                   NOW(),
                   NOW()
              FROM payment_request pr
              JOIN ir_model_data imd
                ON imd.module = 'migration_assets'
               AND imd.model = 'payment.request'
               AND imd.res_id = pr.id
              LEFT JOIN payment_ledger existing
                ON existing.payment_request_id = pr.id
             WHERE pr.id = ANY(%s)
               AND existing.id IS NULL
            """,
            (RUN_ID, uid, uid, ids),
        )
        created_ledgers = env.cr.rowcount  # noqa: F821
        db_writes += created_ledgers
        env.cr.execute(  # noqa: F821
            """
            UPDATE payment_ledger ledger
               SET amount = pr.amount,
                   write_uid = %s,
                   write_date = NOW(),
                   note = COALESCE(ledger.note, '') || E'\nlegacy downstream fact sync adjusted ledger amount to payment request amount'
              FROM payment_request pr
             WHERE ledger.payment_request_id = pr.id
               AND pr.id = ANY(%s)
               AND ledger.amount <> pr.amount
            """,
            (uid, ids),
        )
        updated_ledgers = env.cr.rowcount  # noqa: F821
        db_writes += updated_ledgers
        env.cr.execute(  # noqa: F821
            """
            UPDATE payment_request
               SET state = 'done',
                   validation_status = 'validated',
                   write_uid = %s,
                   write_date = NOW()
             WHERE id = ANY(%s)
               AND (state <> 'done' OR validation_status IS DISTINCT FROM 'validated')
            """,
            (uid, ids),
        )
        updated_requests = env.cr.rowcount  # noqa: F821
        db_writes += updated_requests

        verify_rows = fetchall_dict(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE pr.state = 'done' AND pr.validation_status = 'validated') AS done_validated,
                   COUNT(*) FILTER (WHERE COALESCE(ledger.ledger_sum, 0) = pr.amount) AS paid_equal_request
              FROM payment_request pr
              LEFT JOIN (
                    SELECT payment_request_id, COALESCE(SUM(amount), 0) AS ledger_sum
                      FROM payment_ledger
                     WHERE payment_request_id = ANY(%s)
                     GROUP BY payment_request_id
              ) ledger ON ledger.payment_request_id = pr.id
             WHERE pr.id = ANY(%s)
            """,
            (ids, ids),
        )[0]
        if int(verify_rows["total"]) != EXPECTED_TARGETS:
            raise RuntimeError({"post_write_total_drift": verify_rows})
        if int(verify_rows["done_validated"]) != EXPECTED_TARGETS:
            raise RuntimeError({"post_write_state_not_synced": verify_rows})
        if int(verify_rows["paid_equal_request"]) != EXPECTED_TARGETS:
            raise RuntimeError({"post_write_ledger_not_equal_request": verify_rows})
    else:
        created_ledgers = 0
        updated_ledgers = 0
        updated_requests = 0

    payload = {
        "status": "PASS",
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "run_id": RUN_ID,
        "target_fact": TARGET_FACT,
        "target_count": EXPECTED_TARGETS,
        "already_done_validated": already_done,
        "needs_state_sync": needs_state_sync,
        "needs_ledger_create": needs_ledger_create,
        "needs_ledger_update_to_request_amount": needs_ledger_update,
        "created_ledgers": created_ledgers,
        "updated_ledgers": updated_ledgers,
        "updated_payment_requests": updated_requests,
        "db_writes": db_writes,
        "snapshot_csv": str(SNAPSHOT_CSV),
        "rollback_csv": str(ROLLBACK_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    if mode == "check":
        env.cr.rollback()  # noqa: F821
    else:
        env.cr.commit()  # noqa: F821
    print("LEGACY_PAYMENT_APPROVAL_DOWNSTREAM_FACT_STATE_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
