# -*- coding: utf-8 -*-
"""Audit payment execution to payment request anchor coverage."""

from __future__ import annotations

import json
import os
from collections import OrderedDict
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
        ("payment_execution", sql_one("SELECT COUNT(*)::integer FROM sc_payment_execution")),
        (
            "with_payment_request",
            sql_one("SELECT COUNT(*)::integer FROM sc_payment_execution WHERE payment_request_id IS NOT NULL"),
        ),
        (
            "without_payment_request",
            sql_one("SELECT COUNT(*)::integer FROM sc_payment_execution WHERE payment_request_id IS NULL"),
        ),
    ]
)

remaining_safe_candidates = sql_one(
    """
    WITH e AS (
        SELECT id,
               project_id,
               partner_id,
               contract_id,
               planned_amount,
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
    SELECT COUNT(*)::integer
      FROM candidate
     WHERE (project_id IS NULL OR request_project_id IS NULL OR project_id = request_project_id)
       AND (partner_id IS NULL OR request_partner_id IS NULL OR partner_id = request_partner_id)
       AND (contract_id IS NULL OR request_contract_id IS NULL OR contract_id = request_contract_id)
       AND (planned_amount <= 0 OR request_amount <= 0 OR ABS(planned_amount - request_amount) <= 0.01)
    """
)
if int(remaining_safe_candidates or 0):
    errors.append({"key": "remaining_safe_candidates", "actual": remaining_safe_candidates, "expected": 0})

scope_conflicts = sql_one(
    """
    SELECT COUNT(*)::integer
      FROM sc_payment_execution e
      JOIN payment_request r ON r.id = e.payment_request_id
     WHERE e.document_no = r.name
       AND (
            (r.type IS NOT NULL AND r.type <> 'pay')
            OR (e.project_id IS NOT NULL AND r.project_id IS NOT NULL AND e.project_id <> r.project_id)
            OR (e.partner_id IS NOT NULL AND r.partner_id IS NOT NULL AND e.partner_id <> r.partner_id)
            OR (e.contract_id IS NOT NULL AND r.contract_id IS NOT NULL AND e.contract_id <> r.contract_id)
            OR (e.planned_amount > 0 AND r.amount > 0 AND ABS(e.planned_amount - r.amount) > 0.01)
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
            "duplicate_request_name",
            sql_one(
                """
                WITH e AS (
                    SELECT NULLIF(BTRIM(document_no), '') AS request_key
                      FROM sc_payment_execution
                     WHERE payment_request_id IS NULL
                       AND COALESCE(document_no, '') <> ''
                ), req AS (
                    SELECT name, COUNT(*)::integer AS request_count
                      FROM payment_request
                     WHERE type = 'pay'
                     GROUP BY name
                )
                SELECT COUNT(*)::integer
                  FROM e
                  JOIN req ON req.name = e.request_key
                 WHERE req.request_count <> 1
                """
            ),
        ),
        (
            "no_request_name_match",
            sql_one(
                """
                WITH e AS (
                    SELECT NULLIF(BTRIM(document_no), '') AS request_key
                      FROM sc_payment_execution
                     WHERE payment_request_id IS NULL
                       AND COALESCE(document_no, '') <> ''
                ), req AS (
                    SELECT name
                      FROM payment_request
                     WHERE type = 'pay'
                     GROUP BY name
                )
                SELECT COUNT(*)::integer
                  FROM e
                  LEFT JOIN req ON req.name = e.request_key
                 WHERE req.name IS NULL
                """
            ),
        ),
    ]
)
summary["sample_linked"] = sql_rows(
    """
    SELECT e.id AS execution_id,
           e.document_no,
           e.payment_request_id,
           e.project_id,
           r.project_id AS request_project_id,
           e.partner_id,
           r.partner_id AS request_partner_id,
           e.planned_amount,
           r.amount AS request_amount
      FROM sc_payment_execution e
      JOIN payment_request r ON r.id = e.payment_request_id
     WHERE e.document_no = r.name
     ORDER BY e.id
     LIMIT 20
    """
)

result = OrderedDict()
result["status"] = "PASS" if not errors else "FAIL"
result["database"] = env.cr.dbname  # noqa: F821
result["summary"] = summary
result["errors"] = errors

target = artifact_root() / f"payment_execution_request_anchor_audit_{env.cr.dbname}.json"  # noqa: F821
target.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if errors:
    raise SystemExit(1)
