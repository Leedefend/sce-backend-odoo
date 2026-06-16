# -*- coding: utf-8 -*-
"""Backfill safe invoice and tax deduction partner anchors."""

from __future__ import annotations

import json
import os
from collections import Counter, OrderedDict
from pathlib import Path


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("INVOICE_TAX_PARTNER_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/invoice_tax_partner/{env.cr.dbname}")])  # noqa: F821
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


INVOICE_SQL = """
    WITH partner_names AS (
        SELECT name, COUNT(*)::integer AS partner_count, MIN(id) AS partner_id
          FROM res_partner
         GROUP BY name
    ), candidate AS (
        SELECT i.id,
               COALESCE(NULLIF(i.legacy_visible_partner_name, ''), NULLIF(i.legacy_partner_name, ''), NULLIF(i.recipient_unit_name, '')) AS anchor_name,
               COALESCE(pv.partner_id, pl.partner_id, pr.partner_id) AS partner_id,
               ARRAY_REMOVE(ARRAY[pv.partner_id, pl.partner_id, pr.partner_id], NULL) AS matched_partner_ids,
               c.partner_id AS contract_partner_id,
               s.partner_id AS settlement_partner_id
          FROM sc_invoice_registration i
          LEFT JOIN partner_names pv ON pv.name = i.legacy_visible_partner_name AND pv.partner_count = 1
          LEFT JOIN partner_names pl ON pl.name = i.legacy_partner_name AND pl.partner_count = 1
          LEFT JOIN partner_names pr ON pr.name = i.recipient_unit_name AND pr.partner_count = 1
          LEFT JOIN construction_contract c ON c.id = i.contract_id
          LEFT JOIN sc_settlement_order s ON s.id = i.settlement_id
         WHERE i.partner_id IS NULL
           AND COALESCE(i.legacy_visible_partner_name, i.legacy_partner_name, i.recipient_unit_name, '') <> ''
    )
    SELECT *
      FROM candidate
     WHERE partner_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
              FROM unnest(matched_partner_ids) AS mp(partner_id)
             WHERE mp.partner_id <> candidate.partner_id
       )
       AND (contract_partner_id IS NULL OR contract_partner_id = partner_id)
       AND (settlement_partner_id IS NULL OR settlement_partner_id = partner_id)
     ORDER BY id
"""

TAX_SQL = """
    WITH partner_names AS (
        SELECT name, COUNT(*)::integer AS partner_count, MIN(id) AS partner_id
          FROM res_partner
         GROUP BY name
    )
    SELECT t.id,
           t.partner_name AS anchor_name,
           p.partner_id
      FROM sc_tax_deduction_registration t
      JOIN partner_names p
        ON p.name = t.partner_name
       AND p.partner_count = 1
     WHERE t.partner_id IS NULL
       AND COALESCE(t.partner_name, '') <> ''
     ORDER BY t.id
"""


dry_run = str(os.getenv("DRY_RUN", "")).strip().lower() in {"1", "true", "yes", "y"}
stats = Counter()
samples = []

Invoice = env["sc.invoice.registration"].sudo()  # noqa: F821
for row in fetch_rows(INVOICE_SQL):
    vals = {"partner_id": int(row["partner_id"])}
    stats["invoice_candidates"] += 1
    stats["invoice_fill_partner_id"] += 1
    samples.append(
        OrderedDict(
            [
                ("model", "sc.invoice.registration"),
                ("record_id", row["id"]),
                ("anchor_name", row["anchor_name"]),
                ("partner_id", row["partner_id"]),
            ]
        )
    )
    if not dry_run:
        Invoice.browse(int(row["id"])).write(vals)

Tax = env["sc.tax.deduction.registration"].sudo()  # noqa: F821
for row in fetch_rows(TAX_SQL):
    vals = {"partner_id": int(row["partner_id"])}
    stats["tax_candidates"] += 1
    stats["tax_fill_partner_id"] += 1
    samples.append(
        OrderedDict(
            [
                ("model", "sc.tax.deduction.registration"),
                ("record_id", row["id"]),
                ("anchor_name", row["anchor_name"]),
                ("partner_id", row["partner_id"]),
            ]
        )
    )
    if not dry_run:
        Tax.browse(int(row["id"])).write(vals)

if not dry_run:
    env.cr.commit()  # noqa: F821

result = OrderedDict(
    [
        ("status", "DRY_RUN" if dry_run else "PASS"),
        ("database", env.cr.dbname),  # noqa: F821
        ("stats", dict(stats)),
        ("samples", samples[:30]),
    ]
)
target = artifact_root() / f"invoice_tax_partner_backfill_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
