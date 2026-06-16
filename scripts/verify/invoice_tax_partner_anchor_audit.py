# -*- coding: utf-8 -*-
"""Audit invoice and tax deduction partner anchor coverage."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
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


def sql_one(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def sql_rows(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


INVOICE_SAFE_CANDIDATE_COUNT_SQL = """
    WITH partner_names AS (
        SELECT name, COUNT(*)::integer AS partner_count, MIN(id) AS partner_id
          FROM res_partner
         GROUP BY name
    ), candidate AS (
        SELECT i.id,
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
    SELECT COUNT(*)::integer
      FROM candidate
     WHERE partner_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
              FROM unnest(matched_partner_ids) AS mp(partner_id)
             WHERE mp.partner_id <> candidate.partner_id
       )
       AND (contract_partner_id IS NULL OR contract_partner_id = partner_id)
       AND (settlement_partner_id IS NULL OR settlement_partner_id = partner_id)
"""

TAX_SAFE_CANDIDATE_COUNT_SQL = """
    WITH partner_names AS (
        SELECT name, COUNT(*)::integer AS partner_count, MIN(id) AS partner_id
          FROM res_partner
         GROUP BY name
    )
    SELECT COUNT(*)::integer
      FROM sc_tax_deduction_registration t
      JOIN partner_names p
        ON p.name = t.partner_name
       AND p.partner_count = 1
     WHERE t.partner_id IS NULL
       AND COALESCE(t.partner_name, '') <> ''
"""


errors = []
summary = OrderedDict()

summary["invoice_totals"] = OrderedDict(
    [
        ("total", sql_one("SELECT COUNT(*)::integer FROM sc_invoice_registration")),
        ("with_partner", sql_one("SELECT COUNT(*)::integer FROM sc_invoice_registration WHERE partner_id IS NOT NULL")),
        ("without_partner", sql_one("SELECT COUNT(*)::integer FROM sc_invoice_registration WHERE partner_id IS NULL")),
        (
            "without_partner_with_name",
            sql_one(
                """
                SELECT COUNT(*)::integer
                  FROM sc_invoice_registration
                 WHERE partner_id IS NULL
                   AND COALESCE(legacy_visible_partner_name, legacy_partner_name, recipient_unit_name, '') <> ''
                """
            ),
        ),
    ]
)
summary["tax_totals"] = OrderedDict(
    [
        ("total", sql_one("SELECT COUNT(*)::integer FROM sc_tax_deduction_registration")),
        ("with_partner", sql_one("SELECT COUNT(*)::integer FROM sc_tax_deduction_registration WHERE partner_id IS NOT NULL")),
        ("without_partner", sql_one("SELECT COUNT(*)::integer FROM sc_tax_deduction_registration WHERE partner_id IS NULL")),
        (
            "without_partner_with_name",
            sql_one(
                """
                SELECT COUNT(*)::integer
                  FROM sc_tax_deduction_registration
                 WHERE partner_id IS NULL
                   AND COALESCE(partner_name, '') <> ''
                """
            ),
        ),
    ]
)

remaining_invoice_safe_candidates = sql_one(INVOICE_SAFE_CANDIDATE_COUNT_SQL)
remaining_tax_safe_candidates = sql_one(TAX_SAFE_CANDIDATE_COUNT_SQL)
if int(remaining_invoice_safe_candidates or 0):
    errors.append({"key": "remaining_invoice_safe_candidates", "actual": remaining_invoice_safe_candidates, "expected": 0})
if int(remaining_tax_safe_candidates or 0):
    errors.append({"key": "remaining_tax_safe_candidates", "actual": remaining_tax_safe_candidates, "expected": 0})

invoice_scope_conflicts = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_invoice_registration i
      LEFT JOIN construction_contract c ON c.id = i.contract_id
      LEFT JOIN sc_settlement_order s ON s.id = i.settlement_id
     WHERE i.partner_id IS NOT NULL
       AND COALESCE(i.legacy_visible_partner_name, i.legacy_partner_name, i.recipient_unit_name, '') <> ''
       AND (
            (c.partner_id IS NOT NULL AND c.partner_id <> i.partner_id)
            OR (s.partner_id IS NOT NULL AND s.partner_id <> i.partner_id)
       )
    """
)
if int(invoice_scope_conflicts or 0):
    errors.append({"key": "invoice_scope_conflicts", "actual": invoice_scope_conflicts, "expected": 0})

summary["remaining_safe_candidates"] = OrderedDict(
    [
        ("invoice", remaining_invoice_safe_candidates),
        ("tax", remaining_tax_safe_candidates),
    ]
)
summary["scope_conflicts"] = OrderedDict([("invoice", invoice_scope_conflicts)])
summary["residuals"] = OrderedDict(
    [
        (
            "invoice_without_partner_no_name",
            sql_one(
                """
                SELECT COUNT(*)::integer
                  FROM sc_invoice_registration
                 WHERE partner_id IS NULL
                   AND COALESCE(legacy_visible_partner_name, legacy_partner_name, recipient_unit_name, '') = ''
                """
            ),
        ),
        (
            "tax_without_partner_no_name",
            sql_one(
                """
                SELECT COUNT(*)::integer
                  FROM sc_tax_deduction_registration
                 WHERE partner_id IS NULL
                   AND COALESCE(partner_name, '') = ''
                """
            ),
        ),
    ]
)
summary["sample_invoice_linked"] = sql_rows(
    """
    SELECT i.id AS invoice_id,
           COALESCE(i.legacy_visible_partner_name, i.legacy_partner_name, i.recipient_unit_name) AS anchor_name,
           i.partner_id,
           p.name AS partner_name
      FROM sc_invoice_registration i
      JOIN res_partner p ON p.id = i.partner_id
     WHERE COALESCE(i.legacy_visible_partner_name, i.legacy_partner_name, i.recipient_unit_name, '') <> ''
       AND p.name IN (i.legacy_visible_partner_name, i.legacy_partner_name, i.recipient_unit_name)
     ORDER BY i.id
     LIMIT 20
    """
)
summary["sample_tax_linked"] = sql_rows(
    """
    SELECT t.id AS tax_deduction_id,
           t.partner_name AS anchor_name,
           t.partner_id,
           p.name AS partner_name
      FROM sc_tax_deduction_registration t
      JOIN res_partner p ON p.id = t.partner_id
     WHERE COALESCE(t.partner_name, '') <> ''
       AND p.name = t.partner_name
     ORDER BY t.id
     LIMIT 20
    """
)

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"invoice_tax_partner_anchor_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
