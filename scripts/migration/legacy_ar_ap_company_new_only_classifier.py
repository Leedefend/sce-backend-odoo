# -*- coding: utf-8 -*-
"""Classify new-system AR/AP company rows that are absent from the legacy export."""

from __future__ import annotations

import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


REPO_ROOT = Path("/mnt") if (Path("/mnt") / "addons/smart_construction_core").exists() else Path.cwd()
ARTIFACT_ROOT = Path("/artifacts/migration")
LEGACY_CSV_CANDIDATES = [
    ARTIFACT_ROOT / "legacy_ar_ap_company_collation_probe_rows_v1.csv",
    Path("/mnt/artifacts/migration/legacy_ar_ap_company_collation_probe_rows_v1.csv"),
    REPO_ROOT / "artifacts/migration/legacy_ar_ap_company_collation_probe_rows_v1.csv",
]
OUTPUT_JSON = ARTIFACT_ROOT / "legacy_ar_ap_company_new_only_classifier_v1.json"
OUTPUT_CSV = ARTIFACT_ROOT / "legacy_ar_ap_company_new_only_classifier_v1.csv"
OUTPUT_MD = ARTIFACT_ROOT / "legacy_ar_ap_company_new_only_classifier_v1.md"

FACT_GROUPS = [
    ("income_contract", "收入合同", ["income_contract_amount"]),
    ("output_invoice", "销项发票", ["output_invoice_amount", "output_tax_amount", "output_surcharge_amount"]),
    ("receipt", "收款", ["receipt_amount"]),
    ("payable_contract", "支出合同", ["payable_contract_amount"]),
    ("supplier_pricing", "供应商计价方式", []),
    ("input_invoice", "进项发票", ["input_invoice_amount", "input_tax_amount", "input_surcharge_amount"]),
    ("payment", "付款", ["paid_amount"]),
    ("tax_deduction", "抵扣税费", ["deduction_tax_amount", "deduction_surcharge_amount"]),
    ("self_funding", "自筹资金", ["self_funding_income_amount", "self_funding_refund_amount"]),
    ("project_balance", "项目余额", ["actual_available_balance"]),
]

FIELDS = sorted({field for _, _, fields in FACT_GROUPS for field in fields})


def decimal_value(value: object) -> Decimal:
    try:
        return Decimal(str(value or "0").strip() or "0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def is_nonzero(value: object) -> bool:
    return decimal_value(value) != Decimal("0")


def find_legacy_csv() -> Path:
    for path in LEGACY_CSV_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "legacy CSV missing; run scripts/migration/legacy_ar_ap_company_collation_probe.py first"
    )


def load_legacy_ids(path: Path) -> set[str]:
    legacy_ids = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            legacy_id = (row.get("legacy_project_id") or "").strip()
            if legacy_id:
                legacy_ids.add(legacy_id)
    return legacy_ids


def classify_record(record) -> tuple[list[str], list[str]]:  # noqa: ANN001
    codes = []
    labels = []
    for code, label, fields in FACT_GROUPS:
        has_numeric_fact = any(is_nonzero(getattr(record, field)) for field in fields)
        has_pricing_fact = code == "supplier_pricing" and bool((record.payable_pricing_method_text or "").strip())
        if has_numeric_fact or has_pricing_fact:
            codes.append(code)
            labels.append(label)
    return codes, labels


def load_new_only_rows(legacy_ids: set[str]) -> tuple[list[dict[str, object]], dict[str, int]]:
    rows = []
    counts = {
        "new_project_count": 0,
        "new_project_with_legacy_id_count": 0,
        "new_project_without_legacy_id_count": 0,
    }
    records = env["sc.ar.ap.company.summary"].sudo().search([])  # noqa: F821
    for record in records:
        counts["new_project_count"] += 1
        legacy_id = (record.project_id.legacy_project_id or "").strip()
        if legacy_id:
            counts["new_project_with_legacy_id_count"] += 1
        else:
            counts["new_project_without_legacy_id_count"] += 1
        if not legacy_id or legacy_id in legacy_ids:
            continue
        codes, labels = classify_record(record)
        amount_total = sum((abs(decimal_value(getattr(record, field))) for field in FIELDS), Decimal("0"))
        rows.append(
            {
                "legacy_project_id": legacy_id,
                "project_name": record.project_name or "",
                "source_codes": ",".join(codes) or "unclassified",
                "source_labels": "、".join(labels) or "未分类",
                "source_count": len(codes),
                "impact_score": money(amount_total),
                **{field: money(decimal_value(getattr(record, field))) for field in FIELDS},
            }
        )
    return sorted(rows, key=lambda row: (decimal_value(row["impact_score"]) * Decimal("-1"), row["project_name"])), counts


def summarize(rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, str]]:
    group_counts = Counter()
    group_amounts = Counter()
    combination_counts = Counter()
    unclassified_count = 0
    for row in rows:
        codes = [code for code in str(row["source_codes"]).split(",") if code and code != "unclassified"]
        combination_counts[row["source_labels"]] += 1
        if not codes:
            unclassified_count += 1
        for code in codes:
            group_counts[code] += 1
            for group_code, _, fields in FACT_GROUPS:
                if group_code == code:
                    group_amounts[code] += sum((abs(decimal_value(row[field])) for field in fields), Decimal("0"))
                    break
    group_summary = []
    for code, label, _ in FACT_GROUPS:
        group_summary.append(
            {
                "source_code": code,
                "source_label": label,
                "project_count": group_counts[code],
                "impact_score": money(group_amounts[code]),
            }
        )
    group_summary.append(
        {
            "source_code": "unclassified",
            "source_label": "未分类",
            "project_count": unclassified_count,
            "impact_score": "0.00",
        }
    )
    top_combinations = {
        label: str(count) for label, count in combination_counts.most_common(20)
    }
    return group_summary, top_combinations


def write_text(path: Path, content: str, payload: dict[str, object], key: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        payload["artifacts"][f"{key}_fallback"] = str(fallback)
        fallback.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    write_text(path, content, payload, "json")


def write_csv(path: Path, rows: list[dict[str, object]], payload: dict[str, object]) -> None:
    if not rows:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        target = path
    except PermissionError:
        target = Path("/tmp") / path.name
        payload["artifacts"]["csv_fallback"] = str(target)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# 应收应付报表 New Only 项目来源分类 Batch-AN",
        "",
        "## 批次定位",
        "",
        "- Layer Target：Migration Evidence / Source Classification",
        "- Module：`scripts/migration`, `docs/migration_alignment`",
        "- 目标：解释新系统 `sc.ar.ap.company.summary` 中不在旧库常用过程输出范围内的项目来源。",
        "",
        "## 行覆盖",
        "",
        f"- 旧库项目数：`{payload['row_counts']['legacy_project_count']}`",
        f"- 新系统项目数：`{payload['row_counts']['new_project_count']}`",
        f"- 新系统带旧库项目 ID：`{payload['row_counts']['new_project_with_legacy_id_count']}`",
        f"- 新系统未带旧库项目 ID：`{payload['row_counts']['new_project_without_legacy_id_count']}`",
        f"- New Only 项目数：`{payload['row_counts']['new_only_project_count']}`",
        "",
        "## 来源分组",
        "",
        "| 来源 | 项目数 | 影响分 |",
        "| --- | ---: | ---: |",
    ]
    for item in payload["group_summary"]:
        lines.append(f"| {item['source_label']} | `{item['project_count']}` | `{item['impact_score']}` |")
    lines.extend(
        [
            "",
            "## Top 项目",
            "",
            "| 项目 | 来源 | 影响分 |",
            "| --- | --- | ---: |",
        ]
    )
    for row in payload["top_rows"][:20]:
        lines.append(f"| {row['project_name']} | {row['source_labels']} | `{row['impact_score']}` |")
    lines.extend(
        [
            "",
            "## 判断",
            "",
            payload["decision_note"],
            "",
        ]
    )
    return "\n".join(lines)


legacy_csv = find_legacy_csv()
legacy_ids = load_legacy_ids(legacy_csv)
new_only_rows, row_counts = load_new_only_rows(legacy_ids)
group_summary, top_combinations = summarize(new_only_rows)
unclassified_count = next(
    (item["project_count"] for item in group_summary if item["source_code"] == "unclassified"),
    0,
)
decision_note = (
    f"New Only 项目中 {len(new_only_rows) - unclassified_count} 个可由新系统事实字段解释，"
    f"{unclassified_count} 个零金额/无计价文本项目需继续追踪视图进入原因；"
    "随后应决定是否保留全量事实口径，或新增旧库常用过程口径筛选入口。"
    if new_only_rows
    else "没有 New Only 项目，新旧项目覆盖已闭合。"
)
payload = {
    "mode": "legacy_ar_ap_company_new_only_classifier",
    "database": env.cr.dbname,  # noqa: F821
    "legacy_csv": str(legacy_csv),
    "row_counts": {
        "legacy_project_count": len(legacy_ids),
        **row_counts,
        "new_only_project_count": len(new_only_rows),
    },
    "group_summary": group_summary,
    "top_combinations": top_combinations,
    "top_rows": new_only_rows[:50],
    "artifacts": {
        "json": str(OUTPUT_JSON),
        "csv": str(OUTPUT_CSV),
        "report": str(OUTPUT_MD),
    },
    "decision": "legacy_ar_ap_company_new_only_classified",
    "decision_note": decision_note,
}
write_csv(OUTPUT_CSV, new_only_rows, payload)
write_text(OUTPUT_MD, build_markdown(payload), payload, "report")
write_json(OUTPUT_JSON, payload)
print("LEGACY_AR_AP_COMPANY_NEW_ONLY_CLASSIFIER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
