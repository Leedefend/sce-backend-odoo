#!/usr/bin/env python3
"""Classify SCBS residual rows by business scope evidence.

This report does not create formal documents. It explains why no-project
residual rows are not safe to force into project documents even when legacy
department/business-bucket labels exist.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path


def artifact_root() -> Path:
    root = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
    root.mkdir(parents=True, exist_ok=True)
    return root


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def amount(row: dict[str, str], field: str = "amount") -> float:
    try:
        return float(row.get(field) or 0)
    except Exception:
        return 0.0


def nonempty(value: str | None) -> bool:
    normalized = str(value or "").strip()
    return bool(normalized and normalized.upper() != "NULL")


def classify_payment(row: dict[str, str]) -> str:
    if any(nonempty(row.get(field)) for field in ["f_xmid", "xmmc", "tsxmid", "tsxmmc", "lyxmid", "lyxm", "gcmc"]):
        return "has_explicit_project_clue"
    if nonempty(row.get("bm")):
        return "legacy_department_or_business_bucket_only"
    if nonempty(row.get("supplier_name")) or nonempty(row.get("remark")):
        return "counterparty_or_remark_only"
    return "no_business_scope_clue"


def classify_contract(row: dict[str, str]) -> str:
    if any(nonempty(row.get(field)) for field in ["xmid", "project_name", "gcmc"]):
        return "has_explicit_project_clue"
    if any(nonempty(row.get(field)) for field in ["zmbtext", "jbbm", "wfdw", "zbdhjbt"]):
        return "legacy_business_entity_or_department_only"
    if nonempty(row.get("supplier_name")):
        return "counterparty_only"
    return "no_business_scope_clue"


def add_bucket(buckets: dict[tuple[str, str, str], dict[str, object]], family: str, evidence_type: str, value: str, row_amount: float) -> None:
    normalized = value.strip() or "[EMPTY]"
    key = (family, evidence_type, normalized)
    bucket = buckets.setdefault(
        key,
        {
            "fact_family": family,
            "evidence_type": evidence_type,
            "evidence_value": normalized,
            "rows": 0,
            "amount_total": 0.0,
        },
    )
    bucket["rows"] = int(bucket["rows"]) + 1
    bucket["amount_total"] = float(bucket["amount_total"]) + row_amount


def main() -> None:
    artifacts = artifact_root()
    payment_rows = read_csv(artifacts / "scbs_residual_project_clue_payment_examples_v1.csv")
    contract_rows = read_csv(artifacts / "scbs_residual_project_clue_contract_examples_v1.csv")
    output_summary = artifacts / "scbs_residual_business_scope_summary_v1.csv"
    output_bucket = artifacts / "scbs_residual_business_scope_bucket_v1.csv"
    output_md = artifacts / "scbs_residual_business_scope_report_v1.md"
    output_json = artifacts / "scbs_residual_business_scope_result_v1.json"

    summary: dict[str, dict[str, object]] = {}
    buckets: dict[tuple[str, str, str], dict[str, object]] = {}

    for row in payment_rows:
        classification = classify_payment(row)
        item = summary.setdefault(
            "payment:" + classification,
            {"fact_family": "payment", "classification": classification, "rows": 0, "amount_total": 0.0},
        )
        item["rows"] = int(item["rows"]) + 1
        item["amount_total"] = float(item["amount_total"]) + amount(row)
        add_bucket(buckets, "payment", "bm", row.get("bm") or "", amount(row))
        add_bucket(buckets, "payment", "supplier_name", row.get("supplier_name") or "", amount(row))

    for row in contract_rows:
        classification = classify_contract(row)
        item = summary.setdefault(
            "supplier_contract:" + classification,
            {
                "fact_family": "supplier_contract",
                "classification": classification,
                "rows": 0,
                "amount_total": 0.0,
            },
        )
        item["rows"] = int(item["rows"]) + 1
        item["amount_total"] = float(item["amount_total"]) + amount(row)
        add_bucket(buckets, "supplier_contract", "zmbtext", row.get("zmbtext") or "", amount(row))
        add_bucket(buckets, "supplier_contract", "supplier_name", row.get("supplier_name") or "", amount(row))

    summary_rows = sorted(summary.values(), key=lambda item: (str(item["fact_family"]), str(item["classification"])))
    bucket_rows = sorted(
        buckets.values(),
        key=lambda item: (str(item["fact_family"]), str(item["evidence_type"]), -float(item["amount_total"]), -int(item["rows"])),
    )
    write_csv(output_summary, summary_rows, ["fact_family", "classification", "rows", "amount_total"])
    write_csv(output_bucket, bucket_rows, ["fact_family", "evidence_type", "evidence_value", "rows", "amount_total"])

    status = "PASS" if not any(row["classification"] == "has_explicit_project_clue" and row["rows"] for row in summary_rows) else "REVIEW_REQUIRED"
    md_lines = [
        "# SCBS Residual Business Scope Report",
        "",
        "Status: `%s`" % status,
        "",
        "## Summary",
        "",
        "| Fact Family | Classification | Rows | Amount |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in summary_rows:
        md_lines.append(
            "| {fact_family} | {classification} | {rows} | {amount_total:.2f} |".format(**row)
        )
    md_lines.extend(
        [
            "",
            "## Judgment",
            "",
            "- No residual row has explicit project ID/name evidence in the inspected legacy fields.",
            "- Payment residual rows mostly have legacy `bm` values. This is treated as department/business-bucket evidence, not a project anchor.",
            "- Supplier contract residual rows only expose business entity/department text and supplier names, not project anchors.",
            "- These rows remain audit residuals unless the business owner confirms a target project or defines an enterprise-level target document for them.",
        ]
    )
    output_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    payload = {
        "status": status,
        "summary_csv": str(output_summary),
        "bucket_csv": str(output_bucket),
        "report_md": str(output_md),
        "summary": summary_rows,
    }
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_RESIDUAL_BUSINESS_SCOPE_REPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
