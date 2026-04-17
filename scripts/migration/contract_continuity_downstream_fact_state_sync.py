"""Sync imported construction.contract state from downstream facts.

Run through Odoo shell:
SYNC_MODE=check odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/contract_continuity_downstream_fact_state_sync.py
SYNC_MODE=write odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/contract_continuity_downstream_fact_state_sync.py
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


RUN_ID = "ITER-2026-04-17-CONTRACT-CONTINUITY-DOWNSTREAM-FACT-STATE-SYNC"
TARGET_DB = "sc_demo"
EXPECTED_TOTAL = 6685
EXPECTED_RUNNING = 4783
EXPECTED_CONFIRMED = 1902
OUTPUT_JSON = Path("/mnt/artifacts/migration/contract_continuity_downstream_fact_state_sync_result_v1.json")
SNAPSHOT_CSV = Path("/mnt/artifacts/migration/contract_continuity_downstream_fact_state_sync_snapshot_v1.csv")
ROLLBACK_CSV = Path("/mnt/artifacts/migration/contract_continuity_downstream_fact_state_sync_rollback_v1.csv")
PAYMENT_LINKAGE_ROLLBACK_CSV = Path("/mnt/artifacts/migration/payment_linkage_fact_sync_rollback_v1.csv")


def clean(value):
    return ("" if value is None else str(value)).strip()


def fetchall_dict(query, params=None):
    env.cr.execute(query, params or ())  # noqa: F821
    columns = [item[0] for item in env.cr.description]  # noqa: F821
    return [dict(zip(columns, row)) for row in env.cr.fetchall()]  # noqa: F821


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def replay_inferred_payment_request_ids():
    """Exclude contract links produced by the later payment-linkage replay step.

    Contract continuity must be based on original downstream/source facts. After
    payment linkage sync has run, inferred payment_request.contract_id values
    would otherwise feed back into this script and change the historical target
    count. The rollback CSV records which payment requests had no original
    contract link; those links are replay-derived and must not affect contract
    continuity.
    """
    if not PAYMENT_LINKAGE_ROLLBACK_CSV.exists():
        return []
    excluded_ids = []
    with PAYMENT_LINKAGE_ROLLBACK_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if clean(row.get("restore_contract_id")):
                continue
            payment_id = clean(row.get("payment_request_id"))
            if payment_id:
                excluded_ids.append(int(payment_id))
    return excluded_ids


def target_rows():
    excluded_payment_ids = replay_inferred_payment_request_ids()
    return fetchall_dict(
        """
        WITH pr AS (
              SELECT contract_id, count(*) request_count
                FROM payment_request
               WHERE contract_id IS NOT NULL
                 AND NOT (id = ANY(%s))
               GROUP BY contract_id
             ),
             pla AS (
              SELECT contract_id, count(*) line_count
                FROM payment_request_line
               WHERE contract_id IS NOT NULL
               GROUP BY contract_id
             ),
             wa AS (
              SELECT target_external_id,
                     count(*) audit_count,
                     count(*) FILTER (WHERE approved_at IS NOT NULL) approved_audit_count
                FROM sc_legacy_workflow_audit
               WHERE target_model = 'construction.contract'
               GROUP BY target_external_id
             ),
             imd AS (
              SELECT name, res_id
                FROM ir_model_data
               WHERE module = 'migration_assets'
                 AND model = 'construction.contract'
             )
        SELECT cc.id,
               cc.name,
               cc.type,
               cc.state,
               cc.legacy_contract_id,
               cc.project_id,
               cc.partner_id,
               cc.company_id,
               cc.amount_total,
               COALESCE(pr.request_count, 0) AS request_count,
               COALESCE(pla.line_count, 0) AS line_count,
               COALESCE(wa.audit_count, 0) AS audit_count,
               COALESCE(wa.approved_audit_count, 0) AS approved_audit_count,
               CASE WHEN COALESCE(pr.request_count, 0) > 0 OR COALESCE(pla.line_count, 0) > 0 THEN 'running'
                    WHEN COALESCE(wa.approved_audit_count, 0) > 0 THEN 'confirmed'
                    ELSE ''
               END AS target_state
          FROM construction_contract cc
          LEFT JOIN pr ON pr.contract_id = cc.id
          LEFT JOIN pla ON pla.contract_id = cc.id
          LEFT JOIN imd ON imd.res_id = cc.id
          LEFT JOIN wa ON wa.target_external_id = imd.name
         WHERE COALESCE(cc.legacy_contract_id, '') <> ''
           AND cc.state IN ('draft', 'confirmed', 'running')
           AND (
                COALESCE(pr.request_count, 0) > 0
             OR COALESCE(pla.line_count, 0) > 0
             OR COALESCE(wa.approved_audit_count, 0) > 0
           )
        ORDER BY cc.id
        """
        ,
        (excluded_payment_ids,),
    )


def main():
    mode = clean(os.environ.get("SYNC_MODE") or "check")
    if mode not in {"check", "write"}:
        raise RuntimeError({"invalid_sync_mode": mode})
    if env.cr.dbname != TARGET_DB:  # noqa: F821
        raise RuntimeError({"database_not_sc_demo": env.cr.dbname})  # noqa: F821

    rows = target_rows()
    running_ids = [int(row["id"]) for row in rows if clean(row.get("target_state")) == "running"]
    confirmed_ids = [int(row["id"]) for row in rows if clean(row.get("target_state")) == "confirmed"]
    running_needs_sync_ids = [
        int(row["id"])
        for row in rows
        if clean(row.get("target_state")) == "running" and clean(row.get("state")) != "running"
    ]
    confirmed_needs_sync_ids = [
        int(row["id"])
        for row in rows
        if clean(row.get("target_state")) == "confirmed" and clean(row.get("state")) != "confirmed"
    ]
    already_synced = len(rows) - len(running_needs_sync_ids) - len(confirmed_needs_sync_ids)
    if len(rows) != EXPECTED_TOTAL:
        raise RuntimeError({"target_count_drift": len(rows), "expected": EXPECTED_TOTAL})
    if len(running_ids) != EXPECTED_RUNNING:
        raise RuntimeError({"running_count_drift": len(running_ids), "expected": EXPECTED_RUNNING})
    if len(confirmed_ids) != EXPECTED_CONFIRMED:
        raise RuntimeError({"confirmed_count_drift": len(confirmed_ids), "expected": EXPECTED_CONFIRMED})

    snapshot_fields = [
        "id",
        "legacy_contract_id",
        "name",
        "type",
        "state",
        "target_state",
        "project_id",
        "partner_id",
        "company_id",
        "amount_total",
        "request_count",
        "line_count",
        "audit_count",
        "approved_audit_count",
    ]
    snapshot_rows = [{field: clean(row.get(field)) for field in snapshot_fields} for row in rows]
    rollback_rows = [
        {
            "id": clean(row.get("id")),
            "legacy_contract_id": clean(row.get("legacy_contract_id")),
            "state": clean(row.get("state")),
        }
        for row in rows
    ]
    write_csv(SNAPSHOT_CSV, snapshot_fields, snapshot_rows)
    write_csv(ROLLBACK_CSV, ["id", "legacy_contract_id", "state"], rollback_rows)

    if mode == "write":
        Contract = env["construction.contract"].sudo()  # noqa: F821
        if running_needs_sync_ids:
            Contract.browse(running_needs_sync_ids).write({"state": "running"})
        if confirmed_needs_sync_ids:
            Contract.browse(confirmed_needs_sync_ids).write({"state": "confirmed"})
        env.cr.commit()  # noqa: F821

    result = {
        "run_id": RUN_ID,
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "target_total": len(rows),
        "running_count": len(running_ids),
        "confirmed_count": len(confirmed_ids),
        "needs_sync_count": len(running_needs_sync_ids) + len(confirmed_needs_sync_ids),
        "already_synced_count": already_synced,
        "written_count": len(running_needs_sync_ids) + len(confirmed_needs_sync_ids) if mode == "write" else 0,
        "snapshot_csv": str(SNAPSHOT_CSV),
        "rollback_csv": str(ROLLBACK_CSV),
        "sample_running_ids": running_ids[:20],
        "sample_confirmed_ids": confirmed_ids[:20],
    }
    write_json(OUTPUT_JSON, result)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


main()
