# -*- coding: utf-8 -*-
"""Audit borrowing fact de-duplication and business classification evidence.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/odoo_shell_exec.sh < scripts/verify/interfund_borrow_classification_gap_audit.py
"""

from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path


CONTRACTOR_BORROW_TABLE = "ZJGL_ZCDFSZ_FXJK_JK"
CONTRACTOR_BORROW_CATEGORY = "finance.loan.contractor_project_borrow"
PROJECT_COMPANY_BORROW_CATEGORY = "finance.loan.project_borrow_company"


def artifact_root() -> Path:
    raw = os.getenv("MIGRATION_ARTIFACT_ROOT") or os.getenv("INTERFUND_BORROW_ARTIFACT_ROOT")
    candidates = [Path(raw)] if raw else []
    candidates.extend([Path("/mnt/artifacts/backend"), Path(f"/tmp/interfund_borrow/{env.cr.dbname}")])  # noqa: F821
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


def sql_rows(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    return env.cr.dictfetchall()  # noqa: F821


def sql_one(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def table_count(table_name: str) -> int:
    return int(
        sql_one(
            """
            SELECT COUNT(*)
              FROM sc_financing_loan
             WHERE active IS TRUE
               AND loan_type = 'borrowing_request'
               AND direction = 'borrowed_fund'
               AND legacy_source_table = %s
            """,
            [table_name],
        )
        or 0
    )


def category_status() -> OrderedDict:
    rows = sql_rows(
        """
        SELECT code, name, target_model, source_aliases, domain_json, default_values_json, ledger_policy_json
          FROM sc_business_category
         WHERE active IS TRUE
           AND code IN %s
         ORDER BY code
        """,
        [(CONTRACTOR_BORROW_CATEGORY, PROJECT_COMPANY_BORROW_CATEGORY)],
    )
    return OrderedDict((row["code"], row) for row in rows)


def category_counts():
    return sql_rows(
        """
        SELECT COALESCE(category.code, '<missing>') AS business_category_code,
               COUNT(*)::integer AS active_rows,
               COUNT(DISTINCT loan.legacy_record_id) FILTER (WHERE loan.legacy_record_id IS NOT NULL)::integer
                   AS active_distinct_legacy_records,
               COALESCE(SUM(loan.amount), 0.0) AS amount
          FROM sc_financing_loan loan
          LEFT JOIN sc_business_category category ON category.id = loan.business_category_id
         WHERE loan.active IS TRUE
           AND loan.loan_type = 'borrowing_request'
           AND loan.direction = 'borrowed_fund'
         GROUP BY COALESCE(category.code, '<missing>')
         ORDER BY business_category_code
        """
    )


def missing_business_category_count() -> int:
    return int(
        sql_one(
            """
            SELECT COUNT(*)::integer
              FROM sc_financing_loan
             WHERE active IS TRUE
               AND loan_type = 'borrowing_request'
               AND direction = 'borrowed_fund'
               AND business_category_id IS NULL
            """
        )
        or 0
    )


def classification_confidence_counts():
    return sql_rows(
        """
        SELECT fact.classification_confidence,
               COUNT(*)::integer AS active_rows
          FROM sc_financing_loan loan
          JOIN sc_interfund_movement_fact fact
            ON fact.source_model = 'sc.financing.loan'
           AND fact.source_res_id = loan.id
         WHERE loan.active IS TRUE
           AND loan.loan_type = 'borrowing_request'
           AND loan.direction = 'borrowed_fund'
         GROUP BY fact.classification_confidence
         ORDER BY fact.classification_confidence
        """
    )


def non_high_confidence_count() -> int:
    return int(
        sql_one(
            """
            SELECT COUNT(*)::integer
              FROM sc_financing_loan loan
              JOIN sc_interfund_movement_fact fact
                ON fact.source_model = 'sc.financing.loan'
               AND fact.source_res_id = loan.id
             WHERE loan.active IS TRUE
               AND loan.loan_type = 'borrowing_request'
               AND loan.direction = 'borrowed_fund'
               AND fact.classification_confidence <> 'high'
            """
        )
        or 0
    )


duplicate_groups = sql_rows(
    """
    SELECT legacy_source_table,
           legacy_record_id,
           COUNT(*)::integer AS row_count,
           COUNT(*) FILTER (WHERE active IS TRUE)::integer AS active_count,
           string_agg(id::text || ':' || COALESCE(legacy_source_model, ''), ', ' ORDER BY id) AS records
      FROM sc_financing_loan
     WHERE loan_type = 'borrowing_request'
       AND direction = 'borrowed_fund'
       AND legacy_source_table IS NOT NULL
       AND legacy_record_id IS NOT NULL
     GROUP BY legacy_source_table, legacy_record_id
    HAVING COUNT(*) FILTER (WHERE active IS TRUE) > 1
     ORDER BY active_count DESC, legacy_source_table, legacy_record_id
     LIMIT 50
    """
)

table_summary = sql_rows(
    """
    SELECT legacy_source_table,
           COUNT(*) FILTER (WHERE active IS TRUE)::integer AS active_rows,
           COUNT(DISTINCT legacy_record_id) FILTER (WHERE active IS TRUE)::integer AS active_distinct_legacy_records,
           COUNT(*)::integer AS all_rows,
           COUNT(DISTINCT legacy_record_id)::integer AS all_distinct_legacy_records
      FROM sc_financing_loan
     WHERE loan_type = 'borrowing_request'
       AND direction = 'borrowed_fund'
       AND legacy_source_table IS NOT NULL
     GROUP BY legacy_source_table
     ORDER BY active_rows DESC, legacy_source_table
    """
)

movement_by_table = sql_rows(
    """
    SELECT loan.legacy_source_table,
           fact.movement_type,
           COUNT(*)::integer AS active_rows,
           COUNT(DISTINCT loan.legacy_record_id)::integer AS active_distinct_legacy_records,
           COALESCE(SUM(fact.amount), 0.0) AS amount
      FROM sc_financing_loan loan
      JOIN sc_interfund_movement_fact fact
        ON fact.source_model = 'sc.financing.loan'
       AND fact.source_res_id = loan.id
     WHERE loan.active IS TRUE
       AND loan.loan_type = 'borrowing_request'
       AND loan.direction = 'borrowed_fund'
     GROUP BY loan.legacy_source_table, fact.movement_type
     ORDER BY loan.legacy_source_table, fact.movement_type
    """
)

contractor_menu_not_contractor = sql_rows(
    """
    SELECT loan.id,
           loan.name,
           loan.document_no,
           loan.purpose,
           loan.legacy_source_model,
           loan.legacy_record_id,
           COALESCE(rp.name, loan.legacy_counterparty_name, loan.legacy_visible_applicant) AS partner_name,
           fact.movement_type,
           fact.amount
      FROM sc_financing_loan loan
      JOIN sc_interfund_movement_fact fact
        ON fact.source_model = 'sc.financing.loan'
       AND fact.source_res_id = loan.id
      LEFT JOIN res_partner rp ON rp.id = loan.partner_id
     WHERE loan.active IS TRUE
       AND loan.loan_type = 'borrowing_request'
       AND loan.direction = 'borrowed_fund'
       AND loan.legacy_source_table = %s
       AND fact.movement_type <> 'project_to_contractor_borrow'
     ORDER BY loan.document_no, loan.id
     LIMIT 50
    """,
    [CONTRACTOR_BORROW_TABLE],
)

text_classified_outside_old_menu = sql_rows(
    """
    SELECT loan.id,
           loan.name,
           loan.document_no,
           loan.purpose,
           loan.legacy_source_table,
           loan.legacy_source_model,
           loan.legacy_record_id,
           COALESCE(rp.name, loan.legacy_counterparty_name, loan.legacy_visible_applicant) AS partner_name,
           fact.amount
      FROM sc_financing_loan loan
      JOIN sc_interfund_movement_fact fact
        ON fact.source_model = 'sc.financing.loan'
       AND fact.source_res_id = loan.id
      LEFT JOIN res_partner rp ON rp.id = loan.partner_id
     WHERE loan.active IS TRUE
       AND loan.loan_type = 'borrowing_request'
       AND loan.direction = 'borrowed_fund'
       AND fact.movement_type = 'project_to_contractor_borrow'
       AND COALESCE(loan.legacy_source_table, '') <> %s
     ORDER BY loan.legacy_source_table, loan.document_no, loan.id
     LIMIT 50
    """,
    [CONTRACTOR_BORROW_TABLE],
)

categories = category_status()
business_category_counts = category_counts()
missing_business_categories_on_records = missing_business_category_count()
confidence_counts = classification_confidence_counts()
non_high_confidence_records = non_high_confidence_count()
errors = []
warnings = []

if duplicate_groups:
    errors.append(
        {
            "key": "active_borrowing_legacy_record_duplicates",
            "policy": "增量同步必须按旧表+旧记录号幂等合并；同一业务事实不能重复进入办理列表、往来事实或现金流台账。",
            "sample_count": len(duplicate_groups),
        }
    )

missing_categories = [
    code
    for code in (CONTRACTOR_BORROW_CATEGORY, PROJECT_COMPANY_BORROW_CATEGORY)
    if code not in categories
]
if missing_categories:
    errors.append({"key": "missing_business_categories", "codes": missing_categories})

if missing_business_categories_on_records:
    errors.append(
        {
            "key": "missing_business_category_on_active_borrowing_records",
            "count": missing_business_categories_on_records,
            "policy": "借款往来办理分类必须落到可维护业务分类字段，不能长期依赖用途文本推断。",
        }
    )

for code in (CONTRACTOR_BORROW_CATEGORY, PROJECT_COMPANY_BORROW_CATEGORY):
    category = categories.get(code)
    if category and "business_category_id.code" not in (category.get("domain_json") or ""):
        errors.append(
            {
                "key": "business_category_domain_not_dictionary_anchored",
                "code": code,
                "domain_json": category.get("domain_json"),
                "policy": "借款分类入口必须以 business_category_id.code 为长期锚点，文本只允许作为历史回填兜底。",
            }
        )

if non_high_confidence_records:
    errors.append(
        {
            "key": "financing_loan_interfund_fact_not_high_confidence",
            "count": non_high_confidence_records,
            "classification_confidence_counts": confidence_counts,
            "policy": "已回填业务分类的借款往来事实必须由字典分类驱动，不能继续以中/低置信度进入台账。",
        }
    )

contractor_active_count = table_count(CONTRACTOR_BORROW_TABLE)
if contractor_menu_not_contractor:
    warnings.append(
        {
            "key": "contractor_borrow_old_entry_split_by_current_text_classifier",
            "old_entry_active_count": contractor_active_count,
            "not_project_to_contractor_sample_count": len(contractor_menu_not_contractor),
            "policy": "旧入口名不能直接等同长期产品分类，但旧入口中的分流必须有用户可解释字段和字典化规则承接。",
        }
    )

if text_classified_outside_old_menu:
    warnings.append(
        {
            "key": "project_to_contractor_text_classifier_outside_old_entry",
            "sample_count": len(text_classified_outside_old_menu),
            "policy": "按用途文本识别到承包人借项目款的非旧入口记录需由业务分类字典确认，避免纯文本硬编码长期固化。",
        }
    )

summary = OrderedDict(
    [
        ("db", env.cr.dbname),  # noqa: F821
        ("status", "FAIL" if errors else "PASS"),
        (
            "policy",
            "往来借还款按公司、项目、承包人三主体识别；在线增量只补可见证据，同一旧业务事实必须幂等承载。",
        ),
        ("table_summary", table_summary),
        ("movement_by_table", movement_by_table),
        ("business_category_counts", business_category_counts),
        ("classification_confidence_counts", confidence_counts),
        ("business_categories", categories),
        ("duplicate_groups", duplicate_groups),
        ("contractor_menu_not_contractor_samples", contractor_menu_not_contractor),
        ("text_classified_outside_old_menu_samples", text_classified_outside_old_menu),
        ("warnings", warnings),
        ("errors", errors),
    ]
)

out = artifact_root() / f"interfund_borrow_classification_gap_audit_{env.cr.dbname}.json"
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))

if errors:
    raise SystemExit(1)
