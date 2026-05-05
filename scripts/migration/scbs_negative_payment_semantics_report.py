#!/usr/bin/env python3
"""Classify SCBS negative payment residual semantics.

The current formal payment execution model represents positive paid amounts.
Negative SCBS payment rows are therefore analyzed here as historical facts
before any future refund/reversal/adjustment carrier is selected.
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from pathlib import Path


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def amount(value: str | None) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def clean(value: str | None) -> str:
    normalized = str(value or "").strip()
    if normalized.upper() == "NULL":
        return ""
    return normalized


def classify(row: dict[str, str]) -> str:
    text = " ".join(
        clean(row.get(field))
        for field in ["document_no", "project_name", "partner_name", "legacy_xmmc", "legacy_partner_name", "note"]
    )
    if any(token in text for token in ["调户", "调账", "调整", "冲账", "冲销", "保证金"]):
        return "account_or_internal_adjustment"
    if any(token in text for token in ["退回", "退款", "退还", "退付", "返还", "还款", "退税"]):
        return "refund_or_return"
    return "negative_without_text_semantics"


def main() -> None:
    artifacts = artifact_root()
    residual_rows = [
        row
        for row in read_csv(artifacts / "scbs_unified_residual_register_v1.csv")
        if row.get("category") == "payment_negative_project_confirmed"
    ]
    staging_by_id = {
        row["legacy_record_id"]: row
        for row in read_csv(artifacts / "scbs_fact_staging_v1.csv")
        if row.get("source_table") == "T_FK_Supplier"
    }

    detail_rows: list[dict[str, object]] = []
    summary = defaultdict(lambda: {"classification": "", "rows": 0, "amount_total": 0.0, "abs_amount_total": 0.0})
    project_buckets = defaultdict(lambda: {"project_id": "", "project_name": "", "rows": 0, "amount_total": 0.0})
    partner_buckets = defaultdict(lambda: {"partner_id": "", "partner_name": "", "rows": 0, "amount_total": 0.0})

    for row in residual_rows:
        source = staging_by_id.get(row["legacy_record_id"], {})
        merged = {**source, **row}
        classification = classify(merged)
        row_amount = amount(row.get("amount_total"))
        detail_rows.append(
            {
                "classification": classification,
                "legacy_record_id": row.get("legacy_record_id"),
                "document_no": row.get("document_no"),
                "document_date": row.get("document_date"),
                "project_id": row.get("project_id"),
                "project_name": row.get("project_name"),
                "partner_id": row.get("partner_id"),
                "partner_name": row.get("partner_name"),
                "amount_total": row_amount,
                "note": clean(source.get("note")),
            }
        )
        summary[classification]["classification"] = classification
        summary[classification]["rows"] += 1
        summary[classification]["amount_total"] += row_amount
        summary[classification]["abs_amount_total"] += abs(row_amount)

        project_key = row.get("project_id") or ""
        project_buckets[project_key]["project_id"] = project_key
        project_buckets[project_key]["project_name"] = row.get("project_name") or ""
        project_buckets[project_key]["rows"] += 1
        project_buckets[project_key]["amount_total"] += row_amount

        partner_key = row.get("partner_id") or ""
        partner_buckets[partner_key]["partner_id"] = partner_key
        partner_buckets[partner_key]["partner_name"] = row.get("partner_name") or ""
        partner_buckets[partner_key]["rows"] += 1
        partner_buckets[partner_key]["amount_total"] += row_amount

    summary_rows = sorted(summary.values(), key=lambda item: (-item["abs_amount_total"], item["classification"]))
    project_rows = sorted(project_buckets.values(), key=lambda item: (item["amount_total"], -item["rows"]))[:50]
    partner_rows = sorted(partner_buckets.values(), key=lambda item: (item["amount_total"], -item["rows"]))[:50]

    detail_csv = artifacts / "scbs_negative_payment_semantics_detail_v1.csv"
    summary_csv = artifacts / "scbs_negative_payment_semantics_summary_v1.csv"
    project_csv = artifacts / "scbs_negative_payment_semantics_by_project_v1.csv"
    partner_csv = artifacts / "scbs_negative_payment_semantics_by_partner_v1.csv"
    report_md = artifacts / "scbs_negative_payment_semantics_report_v1.md"
    result_json = artifacts / "scbs_negative_payment_semantics_result_v1.json"

    write_csv(
        detail_csv,
        detail_rows,
        [
            "classification",
            "legacy_record_id",
            "document_no",
            "document_date",
            "project_id",
            "project_name",
            "partner_id",
            "partner_name",
            "amount_total",
            "note",
        ],
    )
    write_csv(summary_csv, summary_rows, ["classification", "rows", "amount_total", "abs_amount_total"])
    write_csv(project_csv, project_rows, ["project_id", "project_name", "rows", "amount_total"])
    write_csv(partner_csv, partner_rows, ["partner_id", "partner_name", "rows", "amount_total"])

    status = "PASS"
    md_lines = [
        "# SCBS Negative Payment Semantics Report",
        "",
        "Status: `%s`" % status,
        "",
        "## Summary",
        "",
        "| Classification | Rows | Amount | Abs Amount |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in summary_rows:
        md_lines.append(
            "| {classification} | {rows} | {amount_total:.2f} | {abs_amount_total:.2f} |".format(**row)
        )
    md_lines.extend(
        [
            "",
            "## Judgment",
            "",
            "- These rows have confirmed project anchors, but their amounts are negative.",
            "- They must not be written into `sc.payment.execution`, which represents positive payment execution.",
            "- Rows with refund/return or adjustment wording need a future refund/reversal/adjustment carrier before formal write.",
            "- Rows without text semantics remain historical negative payment residuals until source-chain semantics are confirmed.",
        ]
    )
    report_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    payload = {
        "status": status,
        "rows": len(detail_rows),
        "amount_total": sum(row["amount_total"] for row in detail_rows),
        "summary": summary_rows,
        "detail_csv": str(detail_csv),
        "summary_csv": str(summary_csv),
        "project_csv": str(project_csv),
        "partner_csv": str(partner_csv),
        "report_md": str(report_md),
    }
    result_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_NEGATIVE_PAYMENT_SEMANTICS_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
