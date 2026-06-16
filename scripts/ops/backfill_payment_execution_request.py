# -*- coding: utf-8 -*-
"""Backfill safe payment execution to payment request anchors.

Run inside ``odoo shell``.  The script only writes relationship anchors where
the legacy payment execution document number uniquely matches one pay request
and existing scope fields do not conflict.
"""

from __future__ import annotations

import json
import os
from collections import Counter, OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("PAYMENT_EXECUTION_REQUEST_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/payment_execution_request/{env.cr.dbname}")])  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except OSError:
            continue
    return Path("/tmp")


def fetch_rows(sql: str, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def safe_candidates():
    return fetch_rows(
        """
        WITH e AS (
            SELECT id,
                   project_id,
                   partner_id,
                   contract_id,
                   planned_amount,
                   paid_amount,
                   NULLIF(BTRIM(document_no), '') AS request_key
              FROM sc_payment_execution
             WHERE payment_request_id IS NULL
               AND COALESCE(document_no, '') <> ''
        ), req AS (
            SELECT name, COUNT(*)::integer AS request_count, MIN(id) AS request_id
              FROM payment_request
             WHERE type = 'pay'
             GROUP BY name
        ), candidate AS (
            SELECT e.*,
                   req.request_id,
                   req.request_count,
                   r.project_id AS request_project_id,
                   r.partner_id AS request_partner_id,
                   r.contract_id AS request_contract_id,
                   r.amount AS request_amount
              FROM e
              JOIN req ON req.name = e.request_key
              JOIN payment_request r ON r.id = req.request_id
             WHERE req.request_count = 1
        )
        SELECT *
          FROM candidate
         WHERE (project_id IS NULL OR request_project_id IS NULL OR project_id = request_project_id)
           AND (partner_id IS NULL OR request_partner_id IS NULL OR partner_id = request_partner_id)
           AND (contract_id IS NULL OR request_contract_id IS NULL OR contract_id = request_contract_id)
           AND (planned_amount <= 0 OR request_amount <= 0 OR ABS(planned_amount - request_amount) <= 0.01)
         ORDER BY id
        """
    )


dry_run = str(os.getenv("DRY_RUN", "")).strip().lower() in {"1", "true", "yes", "y"}
rows = safe_candidates()
stats = Counter()
write_samples = []

Execution = env["sc.payment.execution"].sudo()  # noqa: F821
for row in rows:
    vals = {"payment_request_id": int(row["request_id"])}
    if not row.get("partner_id") and row.get("request_partner_id"):
        vals["partner_id"] = int(row["request_partner_id"])
    if not row.get("contract_id") and row.get("request_contract_id"):
        vals["contract_id"] = int(row["request_contract_id"])
    stats["candidate_rows"] += 1
    stats["fill_payment_request_id"] += 1
    if "partner_id" in vals:
        stats["fill_partner_id"] += 1
    if "contract_id" in vals:
        stats["fill_contract_id"] += 1
    write_samples.append(
        OrderedDict(
            [
                ("execution_id", row["id"]),
                ("request_key", row["request_key"]),
                ("request_id", row["request_id"]),
                ("vals", vals),
            ]
        )
    )
    if dry_run:
        continue
    Execution.browse(int(row["id"])).write(vals)

if not dry_run:
    env.cr.commit()  # noqa: F821

result = OrderedDict(
    [
        ("status", "DRY_RUN" if dry_run else "PASS"),
        ("database", env.cr.dbname),  # noqa: F821
        ("stats", dict(stats)),
        ("samples", write_samples[:20]),
    ]
)
target = artifact_root() / f"payment_execution_request_backfill_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
