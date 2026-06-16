# -*- coding: utf-8 -*-
"""Backfill safe receipt income partner anchors from legacy partner names."""

from __future__ import annotations

import json
import os
from collections import Counter, OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("RECEIPT_INCOME_PARTNER_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/receipt_income_partner/{env.cr.dbname}")])  # noqa: F821
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
        WITH partner_names AS (
            SELECT name, COUNT(*)::integer AS partner_count, MIN(id) AS partner_id
              FROM res_partner
             GROUP BY name
        ), candidate AS (
            SELECT r.id,
                   r.legacy_partner_name,
                   p.partner_id,
                   pr.partner_id AS request_partner_id,
                   c.partner_id AS contract_partner_id
              FROM sc_receipt_income r
              JOIN partner_names p
                ON p.name = r.legacy_partner_name
               AND p.partner_count = 1
              LEFT JOIN payment_request pr ON pr.id = r.payment_request_id
              LEFT JOIN construction_contract c ON c.id = r.contract_id
             WHERE r.partner_id IS NULL
               AND COALESCE(r.legacy_partner_name, '') <> ''
        )
        SELECT *
          FROM candidate
         WHERE (request_partner_id IS NULL OR request_partner_id = partner_id)
           AND (contract_partner_id IS NULL OR contract_partner_id = partner_id)
         ORDER BY id
        """
    )


dry_run = str(os.getenv("DRY_RUN", "")).strip().lower() in {"1", "true", "yes", "y"}
rows = safe_candidates()
stats = Counter()
samples = []

Receipt = env["sc.receipt.income"].sudo()  # noqa: F821
for row in rows:
    vals = {"partner_id": int(row["partner_id"])}
    stats["candidate_rows"] += 1
    stats["fill_partner_id"] += 1
    samples.append(
        OrderedDict(
            [
                ("receipt_id", row["id"]),
                ("legacy_partner_name", row["legacy_partner_name"]),
                ("partner_id", row["partner_id"]),
            ]
        )
    )
    if dry_run:
        continue
    Receipt.browse(int(row["id"])).write(vals)

if not dry_run:
    env.cr.commit()  # noqa: F821

result = OrderedDict(
    [
        ("status", "DRY_RUN" if dry_run else "PASS"),
        ("database", env.cr.dbname),  # noqa: F821
        ("stats", dict(stats)),
        ("samples", samples[:20]),
    ]
)
target = artifact_root() / f"receipt_income_partner_backfill_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
