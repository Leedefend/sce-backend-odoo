#!/usr/bin/env python3
"""Project accepted engineering-progress receipts into the formal receipt model.

Run through ``odoo shell``. This script is intentionally scoped to the
user-accepted engineering-progress receipt surface only.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


SOURCE_MODEL = "sc.legacy.receipt.income.fact"
SOURCE_TABLE = "C_JFHKLR"
SOURCE_FAMILY = "engineering_progress_receipt_visible"
OUTPUT_NAME = "engineering_progress_receipt_formal_projection_write_result_v1.json"


def ensure_allowed_db() -> None:
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def resolve_artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.extend([Path("/mnt/artifacts/migration"), Path.cwd() / "artifacts/migration", Path("/tmp")])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path("/tmp")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scalar(sql: str, params: list[object] | tuple[object, ...] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def fetchall(sql: str, params: list[object] | tuple[object, ...] | None = None) -> list[tuple[object, ...]]:
    env.cr.execute(sql, params or [])  # noqa: F821
    return env.cr.fetchall()  # noqa: F821


ensure_allowed_db()
artifact_root = resolve_artifact_root()
output_json = artifact_root / OUTPUT_NAME
currency_id = env.ref("base.CNY", raise_if_not_found=False).id  # noqa: F821

env.cr.execute("ALTER TABLE sc_receipt_income DROP CONSTRAINT IF EXISTS sc_receipt_income_amount_nonnegative")  # noqa: F821
env.cr.execute("ALTER TABLE sc_receipt_income DROP CONSTRAINT IF EXISTS sc_receipt_income_amount_manual_nonnegative")  # noqa: F821
env.cr.execute(  # noqa: F821
    """
    ALTER TABLE sc_receipt_income
      ADD CONSTRAINT sc_receipt_income_amount_manual_nonnegative
      CHECK (source_origin = 'legacy' OR amount >= 0)
    """
)

accepted_where = """
    legacy_source_table = %s
    AND source_family = %s
    AND operation_strategy IN ('direct', 'joint')
"""

source_count = int(
    scalar(
        "SELECT COUNT(*) FROM sc_legacy_receipt_income_fact WHERE " + accepted_where,
        [SOURCE_TABLE, SOURCE_FAMILY],
    )
    or 0
)
source_missing_project = int(
    scalar(
        "SELECT COUNT(*) FROM sc_legacy_receipt_income_fact WHERE " + accepted_where + " AND project_id IS NULL",
        [SOURCE_TABLE, SOURCE_FAMILY],
    )
    or 0
)
source_sum = str(
    scalar(
        "SELECT ROUND(COALESCE(SUM(source_amount), 0)::numeric, 2) FROM sc_legacy_receipt_income_fact WHERE "
        + accepted_where,
        [SOURCE_TABLE, SOURCE_FAMILY],
    )
    or "0.00"
)
source_by_strategy = [
    {"operation_strategy": row[0], "rows": row[1], "amount": str(row[2])}
    for row in fetchall(
        """
        SELECT operation_strategy, COUNT(*), ROUND(COALESCE(SUM(source_amount), 0)::numeric, 2)
        FROM sc_legacy_receipt_income_fact
        WHERE legacy_source_table = %s
          AND source_family = %s
          AND operation_strategy IN ('direct', 'joint')
        GROUP BY operation_strategy
        ORDER BY operation_strategy
        """,
        [SOURCE_TABLE, SOURCE_FAMILY],
    )
]

before_active_accepted = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_receipt_income income
        JOIN sc_legacy_receipt_income_fact fact
          ON fact.legacy_record_id = income.legacy_record_id
         AND fact.legacy_source_table = %s
         AND fact.source_family = %s
         AND fact.operation_strategy IN ('direct', 'joint')
        WHERE income.active
          AND income.legacy_source_table = %s
        """,
        [SOURCE_TABLE, SOURCE_FAMILY, SOURCE_TABLE],
    )
    or 0
)

# Existing formal rows for the same accepted legacy receipts are not trusted.
# Keep them for audit, but remove them from the user-visible active surface.
env.cr.execute(  # noqa: F821
    """
    UPDATE sc_receipt_income income
       SET active = FALSE,
           note = CONCAT_WS(E'\n', NULLIF(income.note, ''), '[migration:engineering_progress_receipt_formal] superseded_by_user_accepted_fact'),
           write_uid = 1,
           write_date = NOW()
      FROM sc_legacy_receipt_income_fact fact
     WHERE fact.legacy_source_table = %s
       AND fact.source_family = %s
       AND fact.operation_strategy IN ('direct', 'joint')
       AND fact.legacy_record_id = income.legacy_record_id
       AND income.legacy_source_table = %s
       AND income.legacy_source_model <> %s
       AND income.active
    """,
    [SOURCE_TABLE, SOURCE_FAMILY, SOURCE_TABLE, SOURCE_MODEL],
)
superseded_old_active = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    INSERT INTO sc_receipt_income (
      name, source_origin, source_kind, source_family, state,
      project_id, legacy_project_name, company_id, legacy_company_name,
      partner_id, legacy_partner_name, operation_strategy, legacy_contract_no,
      date_receipt, document_no, receipt_type, legacy_receipt_type, legacy_receipt_subtype,
      income_category, payment_method, receiving_account, amount, currency_id,
      legacy_source_model, legacy_source_table, legacy_record_id, legacy_document_state,
      legacy_document_state_label, legacy_attachment_ref, legacy_note, creator_legacy_user_id, creator_name, created_time,
      note, active, create_uid, write_uid, create_date, write_date
    )
    SELECT
      COALESCE(NULLIF(f.document_no, ''), 'LEGACY-ENGINEERING-RECEIPT-' || f.legacy_record_id),
      'legacy',
      'receipt_income',
      f.source_family,
      'legacy_confirmed',
      f.project_id,
      NULLIF(f.legacy_project_name, ''),
      project.company_id,
      NULLIF(f.legacy_company_name, ''),
      f.partner_id,
      NULLIF(f.legacy_partner_name, ''),
      f.operation_strategy,
      NULLIF(f.legacy_contract_no, ''),
      COALESCE(f.document_date, f.created_time::date, CURRENT_DATE),
      NULLIF(f.document_no, ''),
      NULLIF(f.receipt_type, ''),
      NULLIF(f.receipt_type, ''),
      NULLIF(f.receipt_subtype, ''),
      NULLIF(f.income_category, ''),
      NULL,
      NULLIF(f.legacy_receiving_account, ''),
      COALESCE(f.source_amount, 0),
      %s,
      %s,
      f.legacy_source_table,
      f.legacy_record_id,
      NULLIF(f.legacy_state, ''),
      CASE f.legacy_state::varchar
        WHEN '-1' THEN '已驳回'
        WHEN '0' THEN '未审核'
        WHEN '1' THEN '审核中'
        WHEN '2' THEN '已审核'
        ELSE NULLIF(f.legacy_state::varchar, '')
      END,
      NULLIF(f.legacy_attachment_ref, ''),
      NULLIF(f.note, ''),
      NULLIF(f.creator_legacy_user_id, ''),
      NULLIF(f.creator_name, ''),
      f.created_time,
      CONCAT_WS(E'\n',
        '[migration:engineering_progress_receipt_formal] user_accepted_source=' || f.source_family,
        'operation_strategy=' || COALESCE(f.operation_strategy, ''),
        'legacy_record_id=' || f.legacy_record_id,
        NULLIF(f.legacy_project_name, ''),
        NULLIF(f.legacy_partner_name, ''),
        NULLIF(f.note, '')
      ),
      TRUE,
      1,
      1,
      NOW(),
      NOW()
    FROM sc_legacy_receipt_income_fact f
    JOIN project_project project ON project.id = f.project_id
    WHERE f.legacy_source_table = %s
      AND f.source_family = %s
      AND f.operation_strategy IN ('direct', 'joint')
      AND f.project_id IS NOT NULL
    ON CONFLICT (legacy_source_model, legacy_record_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      source_origin = EXCLUDED.source_origin,
      source_kind = EXCLUDED.source_kind,
      source_family = EXCLUDED.source_family,
      state = EXCLUDED.state,
      project_id = EXCLUDED.project_id,
      legacy_project_name = EXCLUDED.legacy_project_name,
      company_id = EXCLUDED.company_id,
      legacy_company_name = EXCLUDED.legacy_company_name,
      partner_id = EXCLUDED.partner_id,
      legacy_partner_name = EXCLUDED.legacy_partner_name,
      operation_strategy = EXCLUDED.operation_strategy,
      legacy_contract_no = EXCLUDED.legacy_contract_no,
      date_receipt = EXCLUDED.date_receipt,
      document_no = EXCLUDED.document_no,
      receipt_type = EXCLUDED.receipt_type,
      legacy_receipt_type = EXCLUDED.legacy_receipt_type,
      legacy_receipt_subtype = EXCLUDED.legacy_receipt_subtype,
      income_category = EXCLUDED.income_category,
      payment_method = EXCLUDED.payment_method,
      receiving_account = EXCLUDED.receiving_account,
      amount = EXCLUDED.amount,
      currency_id = EXCLUDED.currency_id,
      legacy_source_table = EXCLUDED.legacy_source_table,
      legacy_document_state = EXCLUDED.legacy_document_state,
      legacy_document_state_label = EXCLUDED.legacy_document_state_label,
      legacy_attachment_ref = EXCLUDED.legacy_attachment_ref,
      legacy_note = EXCLUDED.legacy_note,
      creator_legacy_user_id = EXCLUDED.creator_legacy_user_id,
      creator_name = EXCLUDED.creator_name,
      created_time = EXCLUDED.created_time,
      note = EXCLUDED.note,
      active = EXCLUDED.active,
      write_uid = 1,
      write_date = NOW()
    """,
    [currency_id, SOURCE_MODEL, SOURCE_TABLE, SOURCE_FAMILY],
)
upserted = env.cr.rowcount  # noqa: F821

env.cr.execute(  # noqa: F821
    """
    UPDATE sc_receipt_income income
       SET operation_strategy = fact.operation_strategy,
           company_id = project.company_id,
           write_uid = 1,
           write_date = NOW()
      FROM sc_legacy_receipt_income_fact fact
      JOIN project_project project ON project.id = fact.project_id
     WHERE fact.legacy_record_id = income.legacy_record_id
       AND fact.legacy_source_table = %s
       AND fact.source_family = %s
       AND fact.operation_strategy IN ('direct', 'joint')
       AND income.legacy_source_model = %s
       AND income.legacy_source_table = %s
       AND income.active
       AND (
         COALESCE(income.operation_strategy, '') <> COALESCE(fact.operation_strategy, '')
         OR income.company_id IS DISTINCT FROM project.company_id
       )
    """,
    [SOURCE_TABLE, SOURCE_FAMILY, SOURCE_MODEL, SOURCE_TABLE],
)
operation_strategy_synced = env.cr.rowcount  # noqa: F821
env.cr.commit()  # noqa: F821

projected_count = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_receipt_income income
        JOIN sc_legacy_receipt_income_fact fact
          ON fact.legacy_record_id = income.legacy_record_id
         AND fact.legacy_source_table = %s
         AND fact.source_family = %s
         AND fact.operation_strategy IN ('direct', 'joint')
        WHERE income.legacy_source_model = %s
          AND income.legacy_source_table = %s
          AND income.active
        """,
        [SOURCE_TABLE, SOURCE_FAMILY, SOURCE_MODEL, SOURCE_TABLE],
    )
    or 0
)
active_coverage = int(
    scalar(
        """
        SELECT COUNT(DISTINCT fact.legacy_record_id)
        FROM sc_legacy_receipt_income_fact fact
        JOIN sc_receipt_income income
          ON income.legacy_record_id = fact.legacy_record_id
         AND income.legacy_source_table = fact.legacy_source_table
         AND income.active
        WHERE fact.legacy_source_table = %s
          AND fact.source_family = %s
          AND fact.operation_strategy IN ('direct', 'joint')
        """,
        [SOURCE_TABLE, SOURCE_FAMILY],
    )
    or 0
)
active_duplicates = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM (
          SELECT fact.legacy_record_id
          FROM sc_legacy_receipt_income_fact fact
          JOIN sc_receipt_income income
            ON income.legacy_record_id = fact.legacy_record_id
           AND income.legacy_source_table = fact.legacy_source_table
           AND income.active
          WHERE fact.legacy_source_table = %s
            AND fact.source_family = %s
            AND fact.operation_strategy IN ('direct', 'joint')
          GROUP BY fact.legacy_record_id
          HAVING COUNT(*) > 1
        ) dup
        """,
        [SOURCE_TABLE, SOURCE_FAMILY],
    )
    or 0
)
projected_sum = str(
    scalar(
        """
        SELECT ROUND(COALESCE(SUM(income.amount), 0)::numeric, 2)
        FROM sc_receipt_income income
        JOIN sc_legacy_receipt_income_fact fact
          ON fact.legacy_record_id = income.legacy_record_id
         AND fact.legacy_source_table = %s
         AND fact.source_family = %s
         AND fact.operation_strategy IN ('direct', 'joint')
        WHERE income.legacy_source_model = %s
          AND income.legacy_source_table = %s
          AND income.active
        """,
        [SOURCE_TABLE, SOURCE_FAMILY, SOURCE_MODEL, SOURCE_TABLE],
    )
    or "0.00"
)
projected_by_strategy = [
    {"operation_strategy": row[0], "rows": row[1], "amount": str(row[2])}
    for row in fetchall(
        """
        SELECT fact.operation_strategy, COUNT(*), ROUND(COALESCE(SUM(income.amount), 0)::numeric, 2)
        FROM sc_receipt_income income
        JOIN sc_legacy_receipt_income_fact fact
          ON fact.legacy_record_id = income.legacy_record_id
         AND fact.legacy_source_table = %s
         AND fact.source_family = %s
         AND fact.operation_strategy IN ('direct', 'joint')
        WHERE income.legacy_source_model = %s
          AND income.legacy_source_table = %s
          AND income.active
        GROUP BY fact.operation_strategy
        ORDER BY fact.operation_strategy
        """,
        [SOURCE_TABLE, SOURCE_FAMILY, SOURCE_MODEL, SOURCE_TABLE],
    )
]
with_receiving_account = int(
    scalar(
        """
        SELECT COUNT(*)
        FROM sc_receipt_income income
        JOIN sc_legacy_receipt_income_fact fact
          ON fact.legacy_record_id = income.legacy_record_id
         AND fact.legacy_source_table = %s
         AND fact.source_family = %s
         AND fact.operation_strategy IN ('direct', 'joint')
        WHERE income.legacy_source_model = %s
          AND income.legacy_source_table = %s
          AND income.active
          AND COALESCE(income.receiving_account, '') <> ''
        """,
        [SOURCE_TABLE, SOURCE_FAMILY, SOURCE_MODEL, SOURCE_TABLE],
    )
    or 0
)

field_mismatches = {}
for field_name, formal_expr, source_expr in [
    ("document_no", "COALESCE(NULLIF(income.document_no, ''), '')", "COALESCE(NULLIF(fact.document_no, ''), '')"),
    ("date_receipt", "income.date_receipt", "fact.document_date"),
    ("project_id", "income.project_id", "fact.project_id"),
    ("legacy_project_name", "COALESCE(NULLIF(income.legacy_project_name, ''), '')", "COALESCE(NULLIF(fact.legacy_project_name, ''), '')"),
    ("partner_id", "income.partner_id", "fact.partner_id"),
    ("legacy_partner_name", "COALESCE(NULLIF(income.legacy_partner_name, ''), '')", "COALESCE(NULLIF(fact.legacy_partner_name, ''), '')"),
    ("legacy_company_name", "COALESCE(NULLIF(income.legacy_company_name, ''), '')", "COALESCE(NULLIF(fact.legacy_company_name, ''), '')"),
    ("amount", "ROUND(COALESCE(income.amount, 0)::numeric, 2)", "ROUND(COALESCE(fact.source_amount, 0)::numeric, 2)"),
    ("receipt_type", "COALESCE(NULLIF(income.receipt_type, ''), '')", "COALESCE(NULLIF(fact.receipt_type, ''), '')"),
    ("income_category", "COALESCE(NULLIF(income.income_category, ''), '')", "COALESCE(NULLIF(fact.income_category, ''), '')"),
    (
        "legacy_document_state_label",
        "COALESCE(NULLIF(income.legacy_document_state_label, ''), '')",
        """COALESCE(NULLIF(CASE fact.legacy_state::varchar
             WHEN '-1' THEN '已驳回'
             WHEN '0' THEN '未审核'
             WHEN '1' THEN '审核中'
             WHEN '2' THEN '已审核'
             ELSE fact.legacy_state::varchar
           END, ''), '')""",
    ),
    ("legacy_contract_no", "COALESCE(NULLIF(income.legacy_contract_no, ''), '')", "COALESCE(NULLIF(fact.legacy_contract_no, ''), '')"),
    ("receiving_account", "COALESCE(NULLIF(income.receiving_account, ''), '')", "COALESCE(NULLIF(fact.legacy_receiving_account, ''), '')"),
    ("legacy_attachment_ref", "COALESCE(NULLIF(income.legacy_attachment_ref, ''), '')", "COALESCE(NULLIF(fact.legacy_attachment_ref, ''), '')"),
    ("creator_name", "COALESCE(NULLIF(income.creator_name, ''), '')", "COALESCE(NULLIF(fact.creator_name, ''), '')"),
    ("created_time", "income.created_time", "fact.created_time"),
    ("legacy_note", "COALESCE(NULLIF(income.legacy_note, ''), '')", "COALESCE(NULLIF(fact.note, ''), '')"),
]:
    comparator = f"({formal_expr}) IS DISTINCT FROM ({source_expr})"
    field_mismatches[field_name] = int(
        scalar(
            f"""
            SELECT COUNT(*)
            FROM sc_receipt_income income
            JOIN sc_legacy_receipt_income_fact fact
              ON fact.legacy_record_id = income.legacy_record_id
             AND fact.legacy_source_table = %s
             AND fact.source_family = %s
             AND fact.operation_strategy IN ('direct', 'joint')
            WHERE income.legacy_source_model = %s
              AND income.legacy_source_table = %s
              AND income.source_family = %s
              AND income.active
              AND {comparator}
            """,
            [SOURCE_TABLE, SOURCE_FAMILY, SOURCE_MODEL, SOURCE_TABLE, SOURCE_FAMILY],
        )
        or 0
    )

expected_projected = source_count - source_missing_project
payload = {
    "status": "PASS"
    if (
        source_count > 0
        and source_missing_project == 0
        and projected_count == source_count
        and active_coverage == source_count
        and active_duplicates == 0
        and projected_sum == source_sum
        and not any(field_mismatches.values())
    )
    else "FAIL",
    "mode": "engineering_progress_receipt_formal_projection_write",
    "database": env.cr.dbname,  # noqa: F821
    "source_model": SOURCE_MODEL,
    "source_table": SOURCE_TABLE,
    "source_family": SOURCE_FAMILY,
    "before_active_accepted_formal_rows": before_active_accepted,
    "source_count": source_count,
    "source_missing_project": source_missing_project,
    "expected_projected": expected_projected,
    "upserted": upserted,
    "operation_strategy_synced": operation_strategy_synced,
    "superseded_old_active": superseded_old_active,
    "projected_active_count": projected_count,
    "active_coverage": active_coverage,
    "active_duplicates": active_duplicates,
    "source_amount_sum": source_sum,
    "projected_amount_sum": projected_sum,
    "source_by_strategy": source_by_strategy,
    "projected_by_strategy": projected_by_strategy,
    "with_receiving_account": with_receiving_account,
    "field_mismatches": field_mismatches,
    "decision": "formal_receipt_income_uses_user_accepted_engineering_progress_receipts_as_authoritative_source",
}
write_json(output_json, payload)
print("ENGINEERING_PROGRESS_RECEIPT_FORMAL_PROJECTION_WRITE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
