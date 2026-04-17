"""Sync deterministic payment.request company and contract links.

Run through Odoo shell:
SYNC_MODE=check odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/payment_linkage_fact_sync.py
SYNC_MODE=write odoo shell -d sc_demo -c /var/lib/odoo/odoo.conf < /mnt/scripts/migration/payment_linkage_fact_sync.py
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


RUN_ID = "ITER-2026-04-17-PAYMENT-LINKAGE-FACT-SYNC"
TARGET_DB = "sc_demo"
EXPECTED_COMPANY_UPDATES = 12108
EXPECTED_CONTRACT_UPDATES = 10305

OUTPUT_JSON = Path("/mnt/artifacts/migration/payment_linkage_fact_sync_result_v1.json")
SNAPSHOT_CSV = Path("/mnt/artifacts/migration/payment_linkage_fact_sync_snapshot_v1.csv")
ROLLBACK_CSV = Path("/mnt/artifacts/migration/payment_linkage_fact_sync_rollback_v1.csv")


def clean(value):
    return "" if value is None else str(value).strip()


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


def candidate_rows():
    return fetchall_dict(
        """
        WITH expected AS (
            SELECT pr.id AS payment_id,
                   imd.name AS external_id,
                   pr.company_id AS old_company_id,
                   pr.contract_id AS old_contract_id,
                   pr.project_id,
                   pr.partner_id,
                   pr.type AS payment_type,
                   CASE WHEN pr.type='pay' THEN 'in'
                        WHEN pr.type='receive' THEN 'out'
                        ELSE NULL END AS expected_contract_type
              FROM payment_request pr
              JOIN ir_model_data imd
                ON imd.module='migration_assets'
               AND imd.model='payment.request'
               AND imd.res_id=pr.id
        ),
        candidates AS (
            SELECT e.payment_id,
                   COUNT(cc.id) AS candidate_count,
                   MIN(cc.id) AS candidate_contract_id
              FROM expected e
              LEFT JOIN construction_contract cc
                ON cc.project_id = e.project_id
               AND cc.partner_id = e.partner_id
               AND cc.type = e.expected_contract_type
             GROUP BY e.payment_id
        ),
        planned AS (
            SELECT e.payment_id,
                   e.external_id,
                   e.old_company_id,
                   e.old_contract_id,
                   CASE
                     WHEN e.old_contract_id IS NOT NULL THEN e.old_contract_id
                     WHEN e.old_contract_id IS NULL AND c.candidate_count = 1 THEN c.candidate_contract_id
                     ELSE NULL
                   END AS proposed_contract_id,
                   CASE
                     WHEN e.old_contract_id IS NOT NULL THEN 'existing_contract'
                     WHEN e.old_contract_id IS NULL AND c.candidate_count = 1 THEN 'unique_project_partner_direction'
                     ELSE ''
                   END AS contract_source,
                   c.candidate_count
              FROM expected e
              JOIN candidates c ON c.payment_id = e.payment_id
        )
        SELECT p.payment_id,
               p.external_id,
               p.old_company_id,
               p.old_contract_id,
               p.proposed_contract_id,
               cc.company_id AS proposed_company_id,
               p.contract_source,
               CASE
                 WHEN p.old_contract_id IS NOT NULL THEN 'existing_contract'
                 WHEN p.old_contract_id IS NULL AND p.candidate_count = 1 THEN 'unique_project_partner_direction'
                 ELSE ''
               END AS company_source,
               p.candidate_count
          FROM planned p
          JOIN construction_contract cc ON cc.id = p.proposed_contract_id
         WHERE cc.company_id IS NOT NULL
           AND (
                (p.old_company_id IS NULL OR p.old_company_id <> cc.company_id)
                OR
                (p.old_contract_id IS NULL AND p.proposed_contract_id IS NOT NULL)
           )
           AND (p.old_contract_id IS NOT NULL OR p.candidate_count = 1)
         ORDER BY p.payment_id
        """
    )


def main():
    mode = clean(os.environ.get("SYNC_MODE") or "check")
    if mode not in {"check", "write"}:
        raise RuntimeError({"invalid_sync_mode": mode})
    if env.cr.dbname != TARGET_DB:  # noqa: F821
        raise RuntimeError({"database_not_sc_demo": env.cr.dbname})  # noqa: F821

    rows = candidate_rows()
    company_updates = [
        row for row in rows
        if clean(row["old_company_id"]) != clean(row["proposed_company_id"])
    ]
    contract_updates = [
        row for row in rows
        if not row["old_contract_id"] and row["proposed_contract_id"]
    ]
    if len(company_updates) not in (0, EXPECTED_COMPANY_UPDATES):
        raise RuntimeError({"company_target_count_drift": len(company_updates), "expected": EXPECTED_COMPANY_UPDATES})
    if len(contract_updates) not in (0, EXPECTED_CONTRACT_UPDATES):
        raise RuntimeError({"contract_target_count_drift": len(contract_updates), "expected": EXPECTED_CONTRACT_UPDATES})

    snapshot_rows = []
    rollback_rows = []
    for row in rows:
        snapshot_rows.append(
            {
                "payment_request_id": row["payment_id"],
                "external_id": row["external_id"],
                "old_company_id": clean(row["old_company_id"]),
                "new_company_id": clean(row["proposed_company_id"]),
                "company_source": row["company_source"],
                "old_contract_id": clean(row["old_contract_id"]),
                "new_contract_id": clean(row["proposed_contract_id"]),
                "contract_source": row["contract_source"],
                "candidate_count": row["candidate_count"],
            }
        )
        rollback_rows.append(
            {
                "payment_request_id": row["payment_id"],
                "external_id": row["external_id"],
                "restore_company_id": clean(row["old_company_id"]),
                "restore_contract_id": clean(row["old_contract_id"]),
            }
        )
    write_csv(
        SNAPSHOT_CSV,
        [
            "payment_request_id",
            "external_id",
            "old_company_id",
            "new_company_id",
            "company_source",
            "old_contract_id",
            "new_contract_id",
            "contract_source",
            "candidate_count",
        ],
        snapshot_rows,
    )
    write_csv(
        ROLLBACK_CSV,
        ["payment_request_id", "external_id", "restore_company_id", "restore_contract_id"],
        rollback_rows,
    )

    updated_company = 0
    updated_contract = 0
    if mode == "write" and rows:
        ids = [int(row["payment_id"]) for row in rows]
        uid = int(env.user.id or 1)  # noqa: F821
        env.cr.execute(  # noqa: F821
            """
            CREATE TEMP TABLE tmp_payment_linkage_fact_sync (
                payment_id integer PRIMARY KEY,
                company_id integer,
                contract_id integer
            ) ON COMMIT DROP
            """
        )
        env.cr.executemany(  # noqa: F821
            """
            INSERT INTO tmp_payment_linkage_fact_sync(payment_id, company_id, contract_id)
            VALUES (%s, %s, %s)
            """,
            [
                (
                    int(row["payment_id"]),
                    int(row["proposed_company_id"]),
                    int(row["proposed_contract_id"]),
                )
                for row in rows
            ],
        )
        env.cr.execute(  # noqa: F821
            """
            UPDATE payment_request pr
               SET company_id = tmp.company_id,
                   write_uid = %s,
                   write_date = NOW()
              FROM tmp_payment_linkage_fact_sync tmp
             WHERE pr.id = tmp.payment_id
               AND (pr.company_id IS NULL OR pr.company_id <> tmp.company_id)
            """,
            (uid,),
        )
        updated_company = env.cr.rowcount  # noqa: F821
        env.cr.execute(  # noqa: F821
            """
            UPDATE payment_request pr
               SET contract_id = tmp.contract_id,
                   write_uid = %s,
                   write_date = NOW()
              FROM tmp_payment_linkage_fact_sync tmp
             WHERE pr.id = tmp.payment_id
               AND pr.contract_id IS NULL
               AND tmp.contract_id IS NOT NULL
            """,
            (uid,),
        )
        updated_contract = env.cr.rowcount  # noqa: F821
        if updated_company not in (0, EXPECTED_COMPANY_UPDATES):
            raise RuntimeError({"updated_company_count_drift": updated_company})
        if updated_contract not in (0, EXPECTED_CONTRACT_UPDATES):
            raise RuntimeError({"updated_contract_count_drift": updated_contract})

        verify = fetchall_dict(
            """
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE company_id IS NOT NULL) AS company_linked,
                   COUNT(*) FILTER (WHERE contract_id IS NOT NULL) AS contract_linked
              FROM payment_request
            """
        )[0]
        if int(verify["company_linked"]) < EXPECTED_COMPANY_UPDATES:
            raise RuntimeError({"post_write_company_linked_too_low": verify})
        if int(verify["contract_linked"]) < EXPECTED_COMPANY_UPDATES:
            raise RuntimeError({"post_write_contract_linked_too_low": verify})
        env.cr.commit()  # noqa: F821
    else:
        env.cr.rollback()  # noqa: F821

    payload = {
        "status": "PASS",
        "mode": mode,
        "database": env.cr.dbname,  # noqa: F821
        "run_id": RUN_ID,
        "candidate_rows": len(rows),
        "company_updates_needed": len(company_updates),
        "contract_updates_needed": len(contract_updates),
        "updated_company": updated_company,
        "updated_contract": updated_contract,
        "snapshot_csv": str(SNAPSHOT_CSV),
        "rollback_csv": str(ROLLBACK_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print("PAYMENT_LINKAGE_FACT_SYNC=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


main()
