# -*- coding: utf-8 -*-
"""Audit receipt income partner anchor coverage."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
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


def sql_one(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def sql_rows(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


errors = []
summary = OrderedDict()

summary["totals"] = OrderedDict(
    [
        ("receipt_income", sql_one("SELECT COUNT(*)::integer FROM sc_receipt_income")),
        ("with_partner", sql_one("SELECT COUNT(*)::integer FROM sc_receipt_income WHERE partner_id IS NOT NULL")),
        ("without_partner", sql_one("SELECT COUNT(*)::integer FROM sc_receipt_income WHERE partner_id IS NULL")),
        (
            "without_partner_with_legacy_name",
            sql_one(
                """
                SELECT COUNT(*)::integer
                  FROM sc_receipt_income
                 WHERE partner_id IS NULL
                   AND COALESCE(legacy_partner_name, '') <> ''
                """
            ),
        ),
    ]
)

remaining_safe_candidates = sql_one(
    """
    WITH partner_names AS (
        SELECT name, COUNT(*)::integer AS partner_count, MIN(id) AS partner_id
          FROM res_partner
         GROUP BY name
    ), candidate AS (
        SELECT r.id,
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
    SELECT COUNT(*)::integer
      FROM candidate
     WHERE (request_partner_id IS NULL OR request_partner_id = partner_id)
       AND (contract_partner_id IS NULL OR contract_partner_id = partner_id)
    """
)
if int(remaining_safe_candidates or 0):
    errors.append({"key": "remaining_safe_candidates", "actual": remaining_safe_candidates, "expected": 0})

scope_conflicts = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_receipt_income r
      LEFT JOIN payment_request pr ON pr.id = r.payment_request_id
      LEFT JOIN construction_contract c ON c.id = r.contract_id
     WHERE r.partner_id IS NOT NULL
       AND COALESCE(r.legacy_partner_name, '') <> ''
       AND EXISTS (
            SELECT 1
              FROM res_partner p
             WHERE p.id = r.partner_id
               AND p.name = r.legacy_partner_name
       )
       AND (
            (pr.partner_id IS NOT NULL AND pr.partner_id <> r.partner_id)
            OR (c.partner_id IS NOT NULL AND c.partner_id <> r.partner_id)
       )
    """
)
if int(scope_conflicts or 0):
    errors.append({"key": "scope_conflicts", "actual": scope_conflicts, "expected": 0})

summary["remaining_safe_candidates"] = remaining_safe_candidates
summary["scope_conflicts"] = scope_conflicts
summary["residuals"] = OrderedDict(
    [
        (
            "legacy_name_no_partner_match",
            sql_one(
                """
                WITH partner_names AS (
                    SELECT name
                      FROM res_partner
                     GROUP BY name
                )
                SELECT COUNT(*)::integer
                  FROM sc_receipt_income r
                  LEFT JOIN partner_names p ON p.name = r.legacy_partner_name
                 WHERE r.partner_id IS NULL
                   AND COALESCE(r.legacy_partner_name, '') <> ''
                   AND p.name IS NULL
                """
            ),
        ),
        (
            "missing_legacy_partner_name",
            sql_one(
                """
                SELECT COUNT(*)::integer
                  FROM sc_receipt_income
                 WHERE partner_id IS NULL
                   AND COALESCE(legacy_partner_name, '') = ''
                """
            ),
        ),
    ]
)
summary["sample_linked"] = sql_rows(
    """
    SELECT r.id AS receipt_id,
           r.legacy_partner_name,
           r.partner_id,
           p.name AS partner_name
      FROM sc_receipt_income r
      JOIN res_partner p ON p.id = r.partner_id
     WHERE COALESCE(r.legacy_partner_name, '') <> ''
       AND r.legacy_partner_name = p.name
     ORDER BY r.id
     LIMIT 20
    """
)

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"receipt_income_partner_anchor_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
