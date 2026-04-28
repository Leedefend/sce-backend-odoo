# -*- coding: utf-8 -*-
"""Build three-layer reconciliation matrix for legacy account income/expense."""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path


METRICS = [
    "opening_balance",
    "income_amount",
    "expense_amount",
    "cumulative_receipt_amount",
    "cumulative_expense_amount",
    "account_transfer_amount",
    "current_account_balance",
    "line_count",
]

MONEY_METRICS = [item for item in METRICS if item != "line_count"]


def repo_root() -> Path:
    env_root = os.getenv("MIGRATION_REPO_ROOT")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    candidates.extend([Path("/mnt"), Path.cwd()])
    for candidate in candidates:
        if (candidate / "addons/smart_construction_core").exists():
            return candidate
    return Path.cwd()


def rounded(value: float) -> float:
    return round(float(value or 0.0), 2)


def empty_totals() -> dict[str, float]:
    return {metric: 0.0 for metric in METRICS}


def add_metric(target: dict[str, float], metric: str, value: float) -> None:
    target[metric] = target.get(metric, 0.0) + float(value or 0.0)


def freeze_totals(totals: dict[str, float]) -> dict[str, float | int]:
    frozen: dict[str, float | int] = {}
    for metric in METRICS:
        value = totals.get(metric, 0.0)
        frozen[metric] = int(value) if metric == "line_count" else rounded(value)
    return frozen


def serialize_rows(rows: list[dict[str, object]], limit: int | None = None) -> list[dict[str, object]]:
    result = rows if limit is None else rows[:limit]
    return result


def write_json(path: Path, payload: dict[str, object]) -> None:
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        payload["artifact_fallback"] = str(fallback)
        fallback.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def format_money(value: object) -> str:
    return f"{float(value or 0.0):,.2f}"


def write_report(path: Path, payload: dict[str, object]) -> None:
    totals = payload["totals"]
    deltas = payload["deltas"]
    lines = [
        "# 账户收支统计三层对账矩阵",
        "",
        "## 总览",
        "",
        "| 口径 | 行数 | 收入金额 | 支出金额 | 累计收款 | 累计支出 | 账户往来 | 当前账户余额 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    labels = {
        "legacy_exact": "legacy_exact",
        "new_official": "new_official",
        "new_continuity": "new_continuity",
    }
    for key in ("legacy_exact", "new_official", "new_continuity"):
        item = totals[key]
        lines.append(
            "| {label} | {rows} | {income} | {expense} | {receipt} | {cum_expense} | {transfer} | {balance} |".format(
                label=labels[key],
                rows=item["account_rows"],
                income=format_money(item["income_amount"]),
                expense=format_money(item["expense_amount"]),
                receipt=format_money(item["cumulative_receipt_amount"]),
                cum_expense=format_money(item["cumulative_expense_amount"]),
                transfer=format_money(item["account_transfer_amount"]),
                balance=format_money(item["current_account_balance"]),
            )
        )
    lines.extend(
        [
            "",
            "## 差异",
            "",
            "| 差异 | 收入金额 | 支出金额 | 累计收款 | 累计支出 | 账户往来 | 当前账户余额 |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for key in ("new_official_minus_legacy_exact", "new_continuity_minus_new_official"):
        item = deltas[key]
        lines.append(
            "| {label} | {income} | {expense} | {receipt} | {cum_expense} | {transfer} | {balance} |".format(
                label=key,
                income=format_money(item["income_amount"]),
                expense=format_money(item["expense_amount"]),
                receipt=format_money(item["cumulative_receipt_amount"]),
                cum_expense=format_money(item["cumulative_expense_amount"]),
                transfer=format_money(item["account_transfer_amount"]),
                balance=format_money(item["current_account_balance"]),
            )
        )
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- legacy_exact：仅统计正式账户，且要求来源明细账户原编号与正式账户原编号精确一致。",
            "- new_official：统计正式账户的新系统投影，包含账号/账户名兜底绑定。",
            "- new_continuity：统计新系统完整投影，包含 Batch-AD 补充的历史来源账户。",
            "",
        ]
    )
    data = "\n".join(lines)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")
    except PermissionError:
        fallback = Path("/tmp") / path.name
        payload["artifacts"]["report_fallback"] = str(fallback)
        fallback.write_text(data, encoding="utf-8")


REPO_ROOT = repo_root()
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "legacy_account_income_expense_reconciliation_matrix_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "legacy_account_income_expense_reconciliation_matrix_v1.md"

Account = env["sc.legacy.account.master"].sudo().with_context(active_test=False)  # noqa: F821
Line = env["sc.legacy.account.transaction.line"].sudo().with_context(active_test=False)  # noqa: F821
Summary = env["sc.account.income.expense.summary"].sudo().with_context(active_test=False)  # noqa: F821

official_accounts = Account.search(
    [
        ("active", "=", True),
        ("fixed_account", "=", False),
        ("source_table", "!=", "legacy_account_transaction_source"),
    ]
)
supplemental_accounts = Account.search(
    [
        ("active", "=", True),
        ("fixed_account", "=", False),
        ("source_table", "=", "legacy_account_transaction_source"),
    ]
)


def account_summary_row(summary) -> dict[str, object]:
    return {
        "legacy_account_id": summary.legacy_account_id or "",
        "account_name": summary.account_name or "",
        "account_no": summary.account_no or "",
        "account_type": summary.account_type or "未分类账户",
        "opening_balance": rounded(summary.opening_balance),
        "income_amount": rounded(summary.income_amount),
        "expense_amount": rounded(summary.expense_amount),
        "cumulative_receipt_amount": rounded(summary.cumulative_receipt_amount),
        "cumulative_expense_amount": rounded(summary.cumulative_expense_amount),
        "account_transfer_amount": rounded(summary.account_transfer_amount),
        "current_account_balance": rounded(summary.current_account_balance),
        "line_count": int(summary.line_count or 0),
    }


def summarize_summary_records(records) -> tuple[dict[str, object], dict[str, dict[str, object]], list[dict[str, object]]]:
    total = empty_totals()
    rows: list[dict[str, object]] = []
    by_type: dict[str, dict[str, float]] = defaultdict(empty_totals)
    for summary in records:
        row = account_summary_row(summary)
        rows.append(row)
        account_type = str(row["account_type"] or "未分类账户")
        for metric in METRICS:
            add_metric(total, metric, float(row[metric] or 0.0))
            add_metric(by_type[account_type], metric, float(row[metric] or 0.0))
    return (
        {"account_rows": len(rows), **freeze_totals(total)},
        {account_type: freeze_totals(values) for account_type, values in sorted(by_type.items())},
        sorted(rows, key=lambda item: (str(item["account_type"]), str(item["account_name"]), str(item["legacy_account_id"]))),
    )


def summarize_legacy_exact() -> tuple[dict[str, object], dict[str, dict[str, object]], list[dict[str, object]]]:
    total = empty_totals()
    by_type: dict[str, dict[str, float]] = defaultdict(empty_totals)
    rows: list[dict[str, object]] = []
    for account in official_accounts:
        account_type = account.account_type or "未分类账户"
        lines = Line.search(
            [
                ("active", "=", True),
                ("account_id", "=", account.id),
                ("account_legacy_id", "=", account.legacy_account_id),
            ]
        )
        values = empty_totals()
        values["opening_balance"] = float(account.opening_balance or 0.0)
        for line in lines:
            if line.metric_bucket == "account_transfer" and line.direction == "income":
                add_metric(values, "income_amount", line.amount)
            elif line.metric_bucket == "account_transfer" and line.direction == "expense":
                add_metric(values, "expense_amount", line.amount)
            elif line.metric_bucket == "cumulative" and line.direction == "income":
                add_metric(values, "cumulative_receipt_amount", line.amount)
            elif line.metric_bucket == "cumulative" and line.direction == "expense":
                add_metric(values, "cumulative_expense_amount", line.amount)
        values["account_transfer_amount"] = values["income_amount"] - values["expense_amount"]
        values["current_account_balance"] = (
            values["opening_balance"]
            + values["income_amount"]
            - values["expense_amount"]
            + values["cumulative_receipt_amount"]
            - values["cumulative_expense_amount"]
        )
        values["line_count"] = len(lines)
        row = {
            "legacy_account_id": account.legacy_account_id or "",
            "account_name": account.name or "",
            "account_no": account.account_no or "",
            "account_type": account_type,
            **freeze_totals(values),
        }
        rows.append(row)
        for metric in METRICS:
            add_metric(total, metric, float(values[metric] or 0.0))
            add_metric(by_type[account_type], metric, float(values[metric] or 0.0))
    return (
        {"account_rows": len(rows), **freeze_totals(total)},
        {account_type: freeze_totals(values) for account_type, values in sorted(by_type.items())},
        sorted(rows, key=lambda item: (str(item["account_type"]), str(item["account_name"]), str(item["legacy_account_id"]))),
    )


def delta(left: dict[str, object], right: dict[str, object]) -> dict[str, float | int]:
    result: dict[str, float | int] = {"account_rows": int(left["account_rows"]) - int(right["account_rows"])}
    for metric in MONEY_METRICS:
        result[metric] = rounded(float(left.get(metric, 0.0) or 0.0) - float(right.get(metric, 0.0) or 0.0))
    result["line_count"] = int(left.get("line_count", 0) or 0) - int(right.get("line_count", 0) or 0)
    return result


legacy_total, legacy_by_type, legacy_rows = summarize_legacy_exact()
official_summary_records = Summary.search(
    [
        ("row_level", "=", "account"),
        ("account_id", "in", official_accounts.ids),
    ]
)
continuity_summary_records = Summary.search([("row_level", "=", "account")])
official_total, official_by_type, official_rows = summarize_summary_records(official_summary_records)
continuity_total, continuity_by_type, continuity_rows = summarize_summary_records(continuity_summary_records)

payload = {
    "mode": "legacy_account_income_expense_reconciliation_matrix",
    "database": env.cr.dbname,  # noqa: F821
    "layers": {
        "legacy_exact": "official accounts with source account legacy id exact match",
        "new_official": "official account projection with account id/no/name fallback binding",
        "new_continuity": "full projection including supplemental legacy transaction accounts",
    },
    "account_counts": {
        "official_accounts": len(official_accounts),
        "supplemental_accounts": len(supplemental_accounts),
    },
    "totals": {
        "legacy_exact": legacy_total,
        "new_official": official_total,
        "new_continuity": continuity_total,
    },
    "deltas": {
        "new_official_minus_legacy_exact": delta(official_total, legacy_total),
        "new_continuity_minus_new_official": delta(continuity_total, official_total),
    },
    "by_account_type": {
        "legacy_exact": legacy_by_type,
        "new_official": official_by_type,
        "new_continuity": continuity_by_type,
    },
    "sample_accounts": {
        "legacy_exact": serialize_rows(legacy_rows, 30),
        "new_official": serialize_rows(official_rows, 30),
        "new_continuity": serialize_rows(continuity_rows, 30),
    },
    "artifacts": {
        "json": str(OUTPUT_JSON),
        "report": str(OUTPUT_REPORT),
    },
    "decision": "account_income_expense_reconciliation_matrix_ready",
}

write_json(OUTPUT_JSON, payload)
write_report(OUTPUT_REPORT, payload)
print("LEGACY_ACCOUNT_INCOME_EXPENSE_RECONCILIATION_MATRIX=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
