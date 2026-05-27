#!/usr/bin/env python3
"""Read-only business data quality probe for SCBS 55 user-visible entries.

The probe is intentionally evidence-oriented: it does not backfill or update
business rows. It records the old visible count, current delivered count, user
confirmed exclusions, and any unexplained gap for the entries already reviewed.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OUTPUT_JSON_NAME = "scbs_55_business_data_quality_probe_result_v1.json"
OUTPUT_REPORT_NAME = "scbs_55_business_data_quality_probe_report_v1.md"


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/scbs_55_quality/{env.cr.dbname}"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/scbs_55_quality/{env.cr.dbname}")  # noqa: F821


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_one(sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any]:
    env.cr.execute(sql, params or ())  # noqa: F821
    names = [desc[0] for desc in env.cr.description]  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return dict(zip(names, row or []))


def table_exists(table_name: str) -> bool:
    return bool(fetch_one("SELECT to_regclass(%s) IS NOT NULL AS exists", (table_name,)).get("exists"))


def count_sql(table: str, where: str = "TRUE") -> dict[str, int]:
    if not table_exists(table):
        return {"rows": 0, "active_rows": 0, "missing_table": 1}
    row = fetch_one(
        f"""
        SELECT COUNT(*)::int AS rows,
               COUNT(*) FILTER (WHERE active IS TRUE)::int AS active_rows
          FROM {table}
         WHERE {where}
        """
    )
    return {"rows": int(row["rows"] or 0), "active_rows": int(row["active_rows"] or 0), "missing_table": 0}


def scalar(sql: str) -> int:
    row = fetch_one(sql)
    value = next(iter(row.values()), 0)
    return int(value or 0)


def decimal_scalar(sql: str) -> float:
    row = fetch_one(sql)
    value = next(iter(row.values()), 0)
    return float(value or 0)


def entry(
    seq: int,
    name: str,
    old_rows: int,
    old_active: int,
    delivered_active: int,
    *,
    delivered_rows: int | None = None,
    user_confirmed_excluded: int = 0,
    status_override: str | None = None,
    note: str = "",
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    unexplained_gap = old_active - delivered_active - user_confirmed_excluded
    status = status_override or ("PASS" if unexplained_gap == 0 else "REVIEW")
    return {
        "seq": seq,
        "entry": name,
        "old_rows": old_rows,
        "old_active": old_active,
        "delivered_rows": delivered_rows if delivered_rows is not None else delivered_active,
        "delivered_active": delivered_active,
        "user_confirmed_excluded": user_confirmed_excluded,
        "unexplained_gap": unexplained_gap,
        "status": status,
        "note": note,
        "metrics": metrics or {},
    }


def office_admin_entry(seq: int, name: str, fact_type: str, old_rows: int, old_active: int) -> dict[str, Any]:
    counts = count_sql("sc_office_admin_document", f"fact_type = '{fact_type}'")
    return entry(seq, name, old_rows, old_active, counts["active_rows"], delivered_rows=counts["rows"])


def hr_payroll_entry(seq: int, name: str, fact_type: str, old_rows: int, old_active: int) -> dict[str, Any]:
    counts = count_sql("sc_hr_payroll_document", f"fact_type = '{fact_type}'")
    return entry(seq, name, old_rows, old_active, counts["active_rows"], delivered_rows=counts["rows"])


def dkqr_document_entry() -> dict[str, Any]:
    counts = count_sql("sc_legacy_fund_confirmation_document")
    return entry(
        35,
        "到款确认表-旧单据事实",
        2655,
        2595,
        counts["active_rows"],
        delivered_rows=counts["rows"],
        note="旧库 ZJGL_SZQR_DKQRB 单据级事实；用户可见金额已按 KPSKQK_BQS。",
    )


def dkqr_income_entry() -> dict[str, Any]:
    if not table_exists("sc_receipt_income"):
        return entry(35, "到款确认表-收入投影", 2556, 2556, 0, status_override="REVIEW", note="missing table")
    delivered = scalar(
        """
        SELECT COUNT(*)
          FROM sc_receipt_income
         WHERE active IS TRUE
           AND source_kind = 'receipt_income'
           AND receipt_type = '到款确认表'
        """
    )
    line_active = scalar(
        """
        SELECT COUNT(*)
          FROM sc_receipt_income
         WHERE active IS TRUE
           AND receipt_type = '到款确认表'
           AND legacy_source_model = 'sc.legacy.fund.confirmation.line'
        """
    )
    duplicate_active = scalar(
        """
        SELECT COUNT(*)
          FROM (
            SELECT document_no, COUNT(*)
              FROM sc_receipt_income
             WHERE active IS TRUE
               AND source_kind = 'receipt_income'
               AND receipt_type = '到款确认表'
             GROUP BY document_no
            HAVING COUNT(*) > 1
          ) d
        """
    )
    row = entry(
        35,
        "到款确认表-用户收入入口",
        2556,
        2556,
        delivered,
        note="单据级投影；旧明细级 active 必须为 0，active 单据不得重复。",
        metrics={"line_grain_active": line_active, "duplicate_active_documents": duplicate_active},
    )
    if row["status"] == "PASS" and (line_active or duplicate_active):
        row["status"] = "REVIEW"
    return row


def prepaid_tax_entry() -> dict[str, Any]:
    if not table_exists("sc_invoice_registration"):
        return entry(41, "预缴税款", 5395, 5395, 0, status_override="REVIEW", note="missing table")
    delivered = scalar(
        """
        SELECT COUNT(*)
          FROM sc_invoice_registration
         WHERE active IS TRUE
           AND source_kind = 'prepaid_tax'
           AND direction = 'prepaid'
        """
    )
    metrics = fetch_one(
        """
        SELECT COUNT(*) FILTER (WHERE active IS TRUE AND COALESCE(amount_total, 0) = 0)::int AS active_zero_amount,
               COUNT(*) FILTER (WHERE active IS TRUE AND COALESCE(tax_type, '') = '')::int AS active_no_tax_type,
               COUNT(*) FILTER (WHERE active IS TRUE AND COALESCE(tax_certificate_no, '') = '')::int AS active_no_cert,
               COUNT(*) FILTER (WHERE active IS TRUE AND COALESCE(legacy_attachment_ref, '') <> '')::int AS active_attachment
          FROM sc_invoice_registration
         WHERE source_kind = 'prepaid_tax'
           AND direction = 'prepaid'
        """
    )
    return entry(
        41,
        "预缴税款",
        5455,
        5395,
        delivered,
        delivered_rows=scalar(
            """
            SELECT COUNT(*)
              FROM sc_invoice_registration
             WHERE source_kind = 'prepaid_tax'
               AND direction = 'prepaid'
            """
        ),
        user_confirmed_excluded=5,
        note="2026-05-27 用户确认旧项目缺失的 5 条不交付；用户树视图已移除旧系统不可见空列。",
        metrics={key: int(value or 0) for key, value in metrics.items()},
    )


def wjz_entry() -> dict[str, Any]:
    counts = count_sql("sc_legacy_payment_residual_fact", "payment_family = 'tax_certificate_registration'")
    return entry(
        44,
        "外经证登记",
        318,
        317,
        counts["active_rows"],
        delivered_rows=counts["rows"],
        note="附件 fallback 已改为 legacy-file 链接，不再裸露 hash 作为附件名。",
    )


def material_stock_fact_entry() -> dict[str, Any]:
    counts = count_sql("sc_legacy_material_stock_fact")
    return entry(
        46,
        "库存统计表（新）-材料库存事实",
        20922,
        16389,
        counts["active_rows"],
        delivered_rows=counts["rows"],
        note="旧库材料出入库事实层已落地；用户报表使用汇总视图过滤无材料和 inactive 项目。",
    )


def material_stock_summary_entry() -> dict[str, Any]:
    if not table_exists("sc_material_stock_summary"):
        return entry(46, "库存统计表（新）-用户汇总入口", 14, 14, 0, status_override="REVIEW", note="missing table")
    rows = scalar("SELECT COUNT(*) FROM sc_material_stock_summary")
    metrics = {
        "no_material_rows": scalar(
            "SELECT COUNT(*) FROM sc_material_stock_summary WHERE COALESCE(material_name, '') = ''"
        ),
        "no_project_name_rows": scalar(
            "SELECT COUNT(*) FROM sc_material_stock_summary WHERE COALESCE(project_name, '') = ''"
        ),
        "test_project_rows": scalar(
            """
            SELECT COUNT(*)
              FROM sc_material_stock_summary
             WHERE project_name ILIKE '%测试%'
                OR project_name ILIKE '%占位%'
            """
        ),
        "stock_amount": round(decimal_scalar("SELECT COALESCE(SUM(stock_amount), 0) FROM sc_material_stock_summary"), 2),
        "price_diff_sum": round(decimal_scalar("SELECT COALESCE(SUM(price_diff), 0) FROM sc_material_stock_summary"), 2),
        "profit_amount": round(decimal_scalar("SELECT COALESCE(SUM(profit_amount), 0) FROM sc_material_stock_summary"), 2),
    }
    row = entry(
        46,
        "库存统计表（新）-用户汇总入口",
        14,
        14,
        rows,
        status_override="PASS_WITH_SCHEMA_RECHECK",
        note="数量和脏数据过滤已闭合；旧 LowCode/Report 利润字段已承载，仍需复核日期和项目过滤口径。",
        metrics=metrics,
    )
    if any(int(metrics[key]) for key in ("no_material_rows", "no_project_name_rows", "test_project_rows")):
        row["status"] = "REVIEW"
    return row


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS 55 Business Data Quality Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Database: {payload['database']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| seq | entry | old active | delivered active | user excluded | unexplained gap | status | note |",
        "| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["entries"]:
        lines.append(
            "| {seq} | {entry} | {old_active} | {delivered_active} | {user_confirmed_excluded} | "
            "{unexplained_gap} | {status} | {note} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            "```json",
            json.dumps(payload["entries"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


artifact_dir = artifact_root()
entries = [
    office_admin_entry(5, "请假/休假审批单", "leave_request", 347, 339),
    office_admin_entry(6, "印章使用审批表", "seal_use", 1565, 1565),
    hr_payroll_entry(9, "社保人员登记", "social_person_registration", 167, 156),
    hr_payroll_entry(13, "奖金", "bonus", 0, 0),
    dkqr_document_entry(),
    dkqr_income_entry(),
    prepaid_tax_entry(),
    wjz_entry(),
    material_stock_fact_entry(),
    material_stock_summary_entry(),
]

hard_fail_statuses = {"FAIL", "REVIEW"}
unexplained_gap_total = sum(abs(int(row["unexplained_gap"])) for row in entries)
review_entries = [row for row in entries if row["status"] in hard_fail_statuses or int(row["unexplained_gap"]) != 0]
schema_recheck_entries = [row for row in entries if row["status"] == "PASS_WITH_SCHEMA_RECHECK"]
payload = {
    "status": "REVIEW"
    if review_entries
    else ("PASS_WITH_SCHEMA_RECHECK" if schema_recheck_entries else "PASS"),
    "mode": "scbs_55_business_data_quality_probe",
    "database": env.cr.dbname,  # noqa: F821
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "entry_count": len(entries),
    "unexplained_gap_total": unexplained_gap_total,
    "review_entry_count": len(review_entries),
    "schema_recheck_entry_count": len(schema_recheck_entries),
    "entries": entries,
    "db_writes": 0,
}
write_json(artifact_dir / OUTPUT_JSON_NAME, payload)
(artifact_dir / OUTPUT_REPORT_NAME).write_text(report_markdown(payload), encoding="utf-8")
print("SCBS_55_BUSINESS_DATA_QUALITY_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if payload["status"] == "REVIEW":
    raise SystemExit(2)
