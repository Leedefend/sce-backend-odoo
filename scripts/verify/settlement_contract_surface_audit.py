# -*- coding: utf-8 -*-
"""Audit settlement contract surface coverage rules.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/settlement_contract_surface_audit.py
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from pathlib import Path


DIRECT_ACCEPTANCE_PREFIX = "sc.legacy.direct.acceptance.fact"
DIRECT_ENGINEERING_SOURCE = "sc.legacy.direct.acceptance.fact:direct_engineering_settlement_order"
CONTRACT_BACKED_SOURCES = {
    "construction.contract.income:settlement_surface",
    "construction.contract.expense:settlement_surface",
}
BUSINESS_FIELDS = {
    "contract_id",
    "legacy_contract_no",
    "contract_subject",
    "engineering_address",
    "settlement_period_start",
    "settlement_period_end",
    "planned_settlement_date",
}


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    try:
        root.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        root = Path("/tmp/sce-migration-artifacts")
        root.mkdir(parents=True, exist_ok=True)
    return root


OUTPUT_JSON = artifact_root() / "settlement_contract_surface_audit_result_v1.json"


def _text(value) -> str:
    value = "" if value in (None, False) else str(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if value in {"False", "false", "None", "none"}:
        return ""
    return value


def _scalar(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def _fetchall(sql, params=None):
    env.cr.execute(sql, params or [])  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    return [dict(zip(names, row)) for row in env.cr.fetchall()]  # noqa: F821


def main():
    failures = []

    total = int(_scalar("SELECT COUNT(*) FROM sc_settlement_order") or 0)
    by_source = _fetchall(
        """
        SELECT COALESCE(legacy_fact_model, '') AS legacy_fact_model,
               COALESCE(legacy_acceptance_label, '') AS legacy_acceptance_label,
               COALESCE(settlement_type, '') AS settlement_type,
               COUNT(*) AS total,
               COUNT(*) FILTER (WHERE contract_id IS NOT NULL) AS with_contract,
               COUNT(*) FILTER (WHERE COALESCE(legacy_contract_no, '') <> '') AS with_legacy_contract_no,
               COUNT(*) FILTER (WHERE COALESCE(contract_subject, '') <> '') AS with_contract_subject,
               COUNT(*) FILTER (WHERE COALESCE(engineering_address, '') <> '') AS with_engineering_address,
               COUNT(*) FILTER (WHERE settlement_period_start IS NOT NULL) AS with_period_start,
               COUNT(*) FILTER (WHERE settlement_period_end IS NOT NULL) AS with_period_end,
               COUNT(*) FILTER (WHERE planned_settlement_date IS NOT NULL) AS with_planned_date
          FROM sc_settlement_order
         GROUP BY legacy_fact_model, legacy_acceptance_label, settlement_type
         ORDER BY total DESC
        """
    )

    contract_backed_missing = _fetchall(
        """
        SELECT s.id, s.name, s.legacy_fact_model, s.contract_id,
               s.legacy_contract_no, c.legacy_contract_no AS contract_legacy_contract_no,
               c.legacy_document_no AS contract_legacy_document_no, c.name AS contract_name,
               s.contract_subject, c.subject AS contract_subject_source,
               s.engineering_address, c.engineering_address AS contract_engineering_address
          FROM sc_settlement_order AS s
          JOIN construction_contract AS c ON c.id = s.contract_id
         WHERE s.legacy_fact_model = ANY(%s)
           AND (
                COALESCE(s.legacy_contract_no, '') = ''
                OR COALESCE(s.contract_subject, '') = ''
                OR (
                    COALESCE(c.engineering_address, '') <> ''
                    AND COALESCE(s.engineering_address, '') <> COALESCE(c.engineering_address, '')
                )
           )
         ORDER BY s.id
         LIMIT 20
        """,
        [list(CONTRACT_BACKED_SOURCES)],
    )
    contract_backed_missing_count = int(
        _scalar(
            """
            SELECT COUNT(*)
              FROM sc_settlement_order AS s
              JOIN construction_contract AS c ON c.id = s.contract_id
             WHERE s.legacy_fact_model = ANY(%s)
               AND (
                    COALESCE(s.legacy_contract_no, '') = ''
                    OR COALESCE(s.contract_subject, '') = ''
                    OR (
                        COALESCE(c.engineering_address, '') <> ''
                        AND COALESCE(s.engineering_address, '') <> COALESCE(c.engineering_address, '')
                    )
               )
            """,
            [list(CONTRACT_BACKED_SOURCES)],
        )
        or 0
    )
    if contract_backed_missing_count:
        failures.append(
            {
                "check": "contract_backed_settlement_contract_snapshot",
                "missing": contract_backed_missing_count,
                "sample": contract_backed_missing,
            }
        )

    direct_engineering_missing_count = int(
        _scalar(
            """
            SELECT COUNT(*)
              FROM sc_settlement_order
             WHERE legacy_fact_model = %s
               AND (
                    (COALESCE(legacy_visible_13, '') <> '' AND COALESCE(contract_subject, '') = '')
                    OR (COALESCE(legacy_visible_15, '') <> '' AND COALESCE(engineering_address, '') = '')
               )
            """,
            [DIRECT_ENGINEERING_SOURCE],
        )
        or 0
    )
    if direct_engineering_missing_count:
        failures.append(
            {
                "check": "direct_engineering_visible_contract_fields",
                "missing": direct_engineering_missing_count,
                "sample": _fetchall(
                    """
                    SELECT id, name, contract_subject, legacy_visible_13,
                           engineering_address, legacy_visible_15
                      FROM sc_settlement_order
                     WHERE legacy_fact_model = %s
                       AND (
                            (COALESCE(legacy_visible_13, '') <> '' AND COALESCE(contract_subject, '') = '')
                            OR (COALESCE(legacy_visible_15, '') <> '' AND COALESCE(engineering_address, '') = '')
                       )
                     ORDER BY id
                     LIMIT 20
                    """,
                    [DIRECT_ENGINEERING_SOURCE],
                ),
            }
        )

    no_contract_by_source = _fetchall(
        """
        SELECT COALESCE(legacy_fact_model, '') AS legacy_fact_model,
               COALESCE(legacy_acceptance_label, '') AS legacy_acceptance_label,
               COUNT(*) AS records_without_contract
          FROM sc_settlement_order
         WHERE contract_id IS NULL
         GROUP BY legacy_fact_model, legacy_acceptance_label
         ORDER BY records_without_contract DESC
        """
    )

    source_scope_notes = [
        {
            "source_prefix": DIRECT_ACCEPTANCE_PREFIX,
            "fields": sorted(BUSINESS_FIELDS),
            "decision": "direct_acceptance_settlements_may_not_have_formal_contract; user-confirmed visible fields are guarded separately",
        },
        {
            "source": DIRECT_ENGINEERING_SOURCE,
            "fields": ["contract_subject", "engineering_address"],
            "decision": "covered from legacy_visible_13 and legacy_visible_15 when present",
        },
        {
            "field": "planned_settlement_date",
            "decision": "not backfilled unless a distinct source value exists; current legacy projections do not carry a separate planned date",
        },
    ]

    result = {
        "audit": "settlement_contract_surface_audit",
        "status": "PASS" if not failures else "FAIL",
        "total": total,
        "by_source": by_source,
        "contract_backed_sources": sorted(CONTRACT_BACKED_SOURCES),
        "contract_backed_missing_count": contract_backed_missing_count,
        "direct_engineering_missing_count": direct_engineering_missing_count,
        "no_contract_by_source": no_contract_by_source,
        "source_scope_notes": source_scope_notes,
        "covered_business_fields": sorted(BUSINESS_FIELDS),
        "failures": failures,
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("SETTLEMENT_CONTRACT_SURFACE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not failures else 1


try:
    sys.exit(main())
except Exception as err:
    result = {
        "audit": "settlement_contract_surface_audit",
        "status": "FAIL",
        "error": str(err),
        "traceback": traceback.format_exc(),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("SETTLEMENT_CONTRACT_SURFACE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(1)
