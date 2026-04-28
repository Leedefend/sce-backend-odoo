# -*- coding: utf-8 -*-
"""Compare legacy global AR/AP CSV with new sc.ar.ap.company.summary."""

from __future__ import annotations

import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


REPO_ROOT = Path("/mnt") if (Path("/mnt") / "addons/smart_construction_core").exists() else Path.cwd()
ARTIFACT_ROOT = Path("/artifacts/migration")
LEGACY_CSV_CANDIDATES = [
    ARTIFACT_ROOT / "legacy_ar_ap_company_collation_probe_rows_v1.csv",
    Path("/mnt/artifacts/migration/legacy_ar_ap_company_collation_probe_rows_v1.csv"),
    REPO_ROOT / "artifacts/migration/legacy_ar_ap_company_collation_probe_rows_v1.csv",
]
OUTPUT_JSON = ARTIFACT_ROOT / "legacy_ar_ap_company_reconciliation_matrix_v1.json"
OUTPUT_CSV = ARTIFACT_ROOT / "legacy_ar_ap_company_reconciliation_top_diff_v1.csv"
OUTPUT_MD = ARTIFACT_ROOT / "legacy_ar_ap_company_reconciliation_matrix_v1.md"

FIELDS = [
    "income_contract_amount",
    "output_invoice_amount",
    "receipt_amount",
    "receivable_unpaid_amount",
    "invoiced_unreceived_amount",
    "received_uninvoiced_amount",
    "payable_contract_amount",
    "paid_amount",
    "input_invoice_amount",
    "payable_unpaid_amount",
    "paid_uninvoiced_amount",
    "output_tax_amount",
    "input_tax_amount",
    "deduction_tax_amount",
    "actual_available_balance",
    "self_funding_income_amount",
    "self_funding_refund_amount",
    "self_funding_unreturned_amount",
    "output_surcharge_amount",
    "input_surcharge_amount",
    "deduction_surcharge_amount",
]


def decimal_value(value: object) -> Decimal:
    try:
        return Decimal(str(value or "0").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def find_legacy_csv() -> Path:
    for path in LEGACY_CSV_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "legacy CSV missing; run scripts/migration/legacy_ar_ap_company_collation_probe.py first"
    )


def load_legacy_rows(path: Path) -> dict[str, dict[str, object]]:
    rows = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            legacy_id = (row.get("legacy_project_id") or "").strip()
            if not legacy_id:
                continue
            rows[legacy_id] = row
    return rows


def load_new_rows() -> dict[str, dict[str, object]]:
    rows = {}
    records = env["sc.ar.ap.company.summary"].sudo().search([])  # noqa: F821
    for record in records:
        legacy_id = (record.project_id.legacy_project_id or "").strip()
        if not legacy_id:
            continue
        rows[legacy_id] = {
            "project_name": record.project_name or "",
            **{field: getattr(record, field) for field in FIELDS},
        }
    return rows


def totals(rows: dict[str, dict[str, object]]) -> dict[str, str]:
    result = {}
    for field in FIELDS:
        result[field] = money(sum((decimal_value(row.get(field)) for row in rows.values()), Decimal("0")))
    return result


def build_differences(
    legacy_rows: dict[str, dict[str, object]], new_rows: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
    differences = []
    for legacy_id in sorted(set(legacy_rows) | set(new_rows)):
        legacy = legacy_rows.get(legacy_id, {})
        new = new_rows.get(legacy_id, {})
        item = {
            "legacy_project_id": legacy_id,
            "legacy_project_name": legacy.get("project_name", ""),
            "new_project_name": new.get("project_name", ""),
            "reason": "matched",
        }
        if not legacy:
            item["reason"] = "new_only"
        elif not new:
            item["reason"] = "legacy_only"
        impact = Decimal("0")
        for field in FIELDS:
            legacy_value = decimal_value(legacy.get(field))
            new_value = decimal_value(new.get(field))
            diff = new_value - legacy_value
            item[f"legacy_{field}"] = money(legacy_value)
            item[f"new_{field}"] = money(new_value)
            item[f"diff_{field}"] = money(diff)
            impact += abs(diff)
        item["impact_score"] = money(impact)
        if impact or item["reason"] != "matched":
            differences.append(item)
    return sorted(differences, key=lambda row: (decimal_value(row["impact_score"]) * Decimal("-1"), row["legacy_project_id"]))


def write_json(path: Path, payload: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        payload["artifacts"]["json_fallback"] = str(fallback)
        fallback.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], payload: dict[str, object]) -> None:
    if not rows:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        target = path
    except PermissionError:
        target = Path("/tmp") / path.name
        payload["artifacts"]["top_diff_csv_fallback"] = str(target)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "# 应收应付报表新旧差异矩阵 Batch-AM",
        "",
        "## 批次定位",
        "",
        "- Layer Target：Migration Evidence / Reconciliation Matrix",
        "- Module：`scripts/migration`, `docs/migration_alignment`",
        "- 目标：按 `legacy_project_id` 对齐旧库全局应收应付结果与新系统 `sc.ar.ap.company.summary`。",
        "",
        "## 行覆盖",
        "",
        f"- 旧库行数：`{payload['row_counts']['legacy_rows']}`",
        f"- 新系统行数：`{payload['row_counts']['new_rows']}`",
        f"- 匹配项目：`{payload['row_counts']['matched_rows']}`",
        f"- 仅旧库：`{payload['row_counts']['legacy_only_rows']}`",
        f"- 仅新系统：`{payload['row_counts']['new_only_rows']}`",
        "",
        "## 汇总差异",
        "",
        "| 字段 | 旧库 | 新系统 | 差异 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for field, diff in payload["total_differences"].items():
        lines.append(
            f"| `{field}` | `{payload['legacy_totals'][field]}` | `{payload['new_totals'][field]}` | `{diff}` |"
        )
    lines.extend(
        [
            "",
            "## Top 差异项目",
            "",
            "| 项目 | 原因 | 影响分 |",
            "| --- | --- | ---: |",
        ]
    )
    for row in payload["top_differences"][:10]:
        project_name = row.get("new_project_name") or row.get("legacy_project_name") or row["legacy_project_id"]
        lines.append(f"| {project_name} | `{row['reason']}` | `{row['impact_score']}` |")
    lines.extend(
        [
            "",
            "## 判断",
            "",
            payload["decision_note"],
            "",
        ]
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines), encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        payload["artifacts"]["report_fallback"] = str(fallback)
        fallback.write_text("\n".join(lines), encoding="utf-8")


legacy_csv = find_legacy_csv()
legacy_rows = load_legacy_rows(legacy_csv)
new_rows = load_new_rows()
legacy_totals = totals(legacy_rows)
new_totals = totals(new_rows)
total_differences = {
    field: money(decimal_value(new_totals[field]) - decimal_value(legacy_totals[field])) for field in FIELDS
}
differences = build_differences(legacy_rows, new_rows)

row_counts = {
    "legacy_rows": len(legacy_rows),
    "new_rows": len(new_rows),
    "matched_rows": len(set(legacy_rows) & set(new_rows)),
    "legacy_only_rows": len(set(legacy_rows) - set(new_rows)),
    "new_only_rows": len(set(new_rows) - set(legacy_rows)),
}
decision_note = (
    "行覆盖未闭合，需优先解释 legacy_only/new_only 项目来源。"
    if row_counts["legacy_only_rows"] or row_counts["new_only_rows"]
    else "行覆盖已按 legacy_project_id 闭合；下一步应按 Top 差异项目逐项解释口径差异。"
)
payload = {
    "mode": "legacy_ar_ap_company_reconciliation_matrix",
    "database": env.cr.dbname,  # noqa: F821
    "legacy_csv": str(legacy_csv),
    "row_counts": row_counts,
    "legacy_totals": legacy_totals,
    "new_totals": new_totals,
    "total_differences": total_differences,
    "top_differences": differences[:30],
    "artifacts": {
        "json": str(OUTPUT_JSON),
        "report": str(OUTPUT_MD),
        "top_diff_csv": str(OUTPUT_CSV),
    },
    "decision": "legacy_ar_ap_company_reconciliation_ready",
    "decision_note": decision_note,
}
write_csv(OUTPUT_CSV, differences[:100], payload)
write_md(OUTPUT_MD, payload)
write_json(OUTPUT_JSON, payload)
print("LEGACY_AR_AP_COMPANY_RECONCILIATION_MATRIX=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
