#!/usr/bin/env python3
"""Audit full user-facing historical data for reconciliation readiness.

The narrower user_reconciliation_readiness_probe guards the core financial
ledgers. This probe scans every P1 daily-business visible model and checks
whether users can reconcile historical rows through stable business axes:
project, document/date, counterparty, type/category, amounts, and source entry.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from lxml import etree

from odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields import (  # noqa: E501
    LABEL_SOURCE_OVERRIDES,
    MODEL_LABEL_SOURCE_OVERRIDES,
    P1_ALIAS_LABELS,
)


def artifact_root() -> Path:
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    candidates = [Path(env_root)] if env_root else []
    candidates.append(Path("/mnt/artifacts/verify"))
    candidates.append(Path(f"/tmp/history_continuity/{env.cr.dbname}/verify"))  # noqa: F821
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return candidate
        except Exception:
            continue
    return Path(f"/tmp/history_continuity/{env.cr.dbname}/verify")  # noqa: F821


def existing_fields(model_name: str) -> set[str]:
    return set(env[model_name]._fields)  # noqa: F821


def first_existing(
    model_name: str,
    candidates: list[str] | tuple[str, ...],
    preferred: set[str] | None = None,
) -> str | None:
    fields = existing_fields(model_name)
    preferred = preferred or set()
    for field_name in candidates:
        if field_name in fields and field_name in preferred:
            return field_name
    for field_name in candidates:
        if field_name in fields:
            return field_name
    return None


def best_axis_field(
    model_name: str,
    candidates: list[str] | tuple[str, ...],
    domain: list[object],
    total: int,
    preferred: set[str] | None = None,
) -> tuple[str | None, int]:
    fields = existing_fields(model_name)
    preferred = preferred or set()
    existing = [field_name for field_name in candidates if field_name in fields]
    if not existing:
        return None, 0
    if not total:
        preferred_existing = [field_name for field_name in existing if field_name in preferred]
        return (preferred_existing or existing)[0], 0

    scored = []
    for field_name in existing:
        filled = non_empty_count(model_name, field_name, domain)
        grouped_rank = 1 if field_name in preferred else 0
        scored.append((grouped_rank, filled, -existing.index(field_name), field_name))
    grouped = [item for item in scored if item[0]]
    pool = grouped or scored
    _, filled, _, field_name = max(pool)
    return field_name, filled


def domain_for_model(model_name: str) -> list[object]:
    fields = existing_fields(model_name)
    if "source_origin" in fields:
        return [("source_origin", "=", "legacy")]
    if "legacy_record_id" in fields:
        return [("legacy_record_id", "!=", False)]
    if "legacy_source_id" in fields:
        return [("legacy_source_id", "!=", False)]
    if "legacy_source_model" in fields:
        return [("legacy_source_model", "!=", False)]
    return []


def non_empty_count(model_name: str, field_name: str, domain: list[object]) -> int:
    field = env[model_name]._fields.get(field_name)  # noqa: F821
    if field and field.compute and not field.store:
        return 0
    if field and field.type == "boolean":
        return env[model_name].sudo().search_count(domain)  # noqa: F821
    return env[model_name].sudo().search_count(domain + [(field_name, "!=", False)])  # noqa: F821


def amount_sum(model_name: str, field_name: str, domain: list[object]) -> float:
    field = env[model_name]._fields.get(field_name)  # noqa: F821
    if field and field.compute and not field.store:
        return 0.0
    Model = env[model_name].sudo()  # noqa: F821
    total = 0.0
    for group in Model.read_group(domain, [f"{field_name}:sum"], [], lazy=False):
        total += float(group.get(field_name) or 0.0)
    return total


def view_fields(model_name: str, view_type: str) -> dict[str, set[str]]:
    group_fields: set[str] = set()
    sum_fields: set[str] = set()
    visible_fields: set[str] = set()
    views = env["ir.ui.view"].sudo().search([("model", "=", model_name), ("type", "=", view_type)])  # noqa: F821
    for view in views:
        arch = view.arch_db or ""
        group_fields.update(re.findall(r"group_by'?\s*:\s*'([^']+)'", arch))
        try:
            root = etree.fromstring(arch.encode("utf-8")) if arch else None
        except Exception:
            root = None
        if root is None:
            continue
        for node in root.xpath(".//field[@name]"):
            name = node.get("name")
            if not name:
                continue
            visible_fields.add(name)
            if node.get("sum"):
                sum_fields.add(name)
    return {
        "group_fields": group_fields,
        "sum_fields": sum_fields,
        "visible_fields": visible_fields,
    }


AXES = {
    "project": ["project_id", "business_entity_id", "legacy_project_name", "project_name", "project_name_text"],
    "document": ["document_no", "name", "contract_no", "invoice_no"],
    "date": [
        "document_date",
        "request_date",
        "date_request",
        "date_claim",
        "date_payment",
        "date_receipt",
        "invoice_date",
        "operation_date",
        "settlement_date",
        "contract_date",
        "date_diary",
        "inbound_date",
        "outbound_date",
        "snapshot_date",
        "create_date",
        "created_time",
        "source_created_at",
    ],
    "party": [
        "partner_id",
        "supplier_id",
        "contractor_id",
        "subcontractor_id",
        "owner_id",
        "requester_id",
        "partner_name",
        "partner_name_text",
        "legacy_partner_name",
        "receipt_partner_name",
    ],
    "type": [
        "source_kind",
        "contract_type",
        "contract_family",
        "claim_type",
        "expense_type",
        "payment_family",
        "payment_method",
        "income_category",
        "receipt_type",
        "legacy_receipt_type",
        "legacy_receipt_subtype",
        "operation_type",
        "operation_strategy",
        "invoice_type",
        "tax_rate",
        "cost_category_name",
        "document_scope",
        "source_family",
        "state",
    ],
    "creator": ["source_created_by", "creator_name", "requester_id", "owner_id"],
    "created_at": ["source_created_at", "created_time", "create_date"],
}

AMOUNT_FIELDS = [
    "amount_total",
    "amount",
    "paid_amount",
    "planned_amount",
    "invoice_amount",
    "received_amount",
    "unreceived_amount",
    "unpaid_amount",
    "approved_amount",
    "deduction_amount",
    "tax_amount",
    "amount_no_tax",
    "invoice_amount_total",
    "daily_income",
    "daily_expense",
    "account_balance_total",
    "bank_balance_total",
    "bank_system_difference",
]


def best_label_source(model_name: str, candidates: list[str], domain: list[object], total: int) -> tuple[str | None, int]:
    fields = existing_fields(model_name)
    seen = []
    for candidate in candidates:
        if candidate in fields and candidate not in seen:
            seen.append(candidate)
    if not seen:
        return None, 0
    if not total:
        return seen[0], 0

    best_field = seen[0]
    best_filled = -1
    for field_name in seen:
        filled = non_empty_count(model_name, field_name, domain)
        if filled > best_filled:
            best_field = field_name
            best_filled = filled
    return best_field, max(best_filled, 0)


def label_source_coverage(model_name: str, labels: list[str], domain: list[object], total: int) -> list[dict[str, object]]:
    rows = []
    for label in labels:
        candidates = [
            name for name, field in env[model_name]._fields.items()  # noqa: F821
            if field.string == label and not name.startswith("p1_visible_")
        ]
        candidates += list(MODEL_LABEL_SOURCE_OVERRIDES.get(model_name, {}).get(label, ()))
        candidates += list(LABEL_SOURCE_OVERRIDES.get(label, ()))
        field_name, filled = best_label_source(model_name, candidates, domain, total)
        rows.append(
            {
                "label": label,
                "field": field_name,
                "filled": filled,
                "total": total,
                "ratio": round(filled / total, 4) if total else 1.0,
                "source_missing": field_name is None,
            }
        )
    return rows


results = []
blocking_gaps = []
warnings = []
empty_model_infos = []
low_volume_infos = []

for model_name, labels in sorted(P1_ALIAS_LABELS.items()):
    if model_name not in env:  # noqa: F821
        blocking_gaps.append({"model": model_name, "reason": "model_missing"})
        continue
    Model = env[model_name].sudo()  # noqa: F821
    domain = domain_for_model(model_name)
    total = Model.search_count(domain)
    fields = existing_fields(model_name)
    amount_field = first_existing(model_name, AMOUNT_FIELDS)
    amount_total = amount_sum(model_name, amount_field, domain) if amount_field and total else 0.0
    search = view_fields(model_name, "search")
    tree = view_fields(model_name, "tree")

    axes = {}
    missing_axes = []
    weak_axes = []
    for axis, candidates in AXES.items():
        field_name, filled = best_axis_field(model_name, candidates, domain, total, search["group_fields"])
        ratio = round(filled / total, 4) if total else 1.0
        axes[axis] = {
            "field": field_name,
            "filled": filled,
            "total": total,
            "ratio": ratio,
            "grouped": bool(field_name and field_name in search["group_fields"]),
            "visible": bool(field_name and field_name in tree["visible_fields"]),
        }
        if total >= 100 and axis in {"project", "document", "date", "type"} and not field_name:
            missing_axes.append(axis)
        if total >= 100 and field_name and ratio < 0.8 and axis in {"project", "document", "date", "type"}:
            weak_axes.append(axis)

    amount_visible = bool(amount_field and amount_field in tree["visible_fields"])
    amount_summed = bool(amount_field and amount_field in tree["sum_fields"])
    group_gap_axes = [
        axis
        for axis in ("project", "date", "party", "type")
        if axes[axis]["field"] and total >= 100 and not axes[axis]["grouped"]
    ]
    label_rows = label_source_coverage(model_name, labels, domain, total)
    label_source_missing = [row["label"] for row in label_rows if row["source_missing"]]
    low_label_coverage = [
        row for row in label_rows
        if total >= 100 and not row["source_missing"] and row["ratio"] < 0.2
    ]

    if total >= 100 and amount_field and not amount_summed:
        blocking_gaps.append({"model": model_name, "reason": "amount_not_summed", "field": amount_field, "total": total})
    for axis in missing_axes:
        blocking_gaps.append({"model": model_name, "reason": "axis_missing", "axis": axis, "total": total})
    if total >= 100 and group_gap_axes:
        warnings.append({"model": model_name, "reason": "group_axes_not_exposed", "axes": group_gap_axes, "total": total})
    if weak_axes:
        warnings.append({"model": model_name, "reason": "weak_axis_coverage", "axes": weak_axes, "total": total})
    if label_source_missing and total >= 100:
        warnings.append(
            {
                "model": model_name,
                "reason": "p1_label_source_missing",
                "labels": label_source_missing[:20],
                "count": len(label_source_missing),
                "total": total,
            }
        )
    elif label_source_missing and total > 0:
        low_volume_infos.append(
            {
                "model": model_name,
                "reason": "low_volume_p1_label_source_missing",
                "labels": label_source_missing[:20],
                "count": len(label_source_missing),
                "total": total,
            }
        )
    elif label_source_missing:
        empty_model_infos.append(
            {
                "model": model_name,
                "reason": "empty_model_p1_label_source_missing",
                "labels": label_source_missing[:20],
                "count": len(label_source_missing),
                "total": total,
            }
        )
    if low_label_coverage:
        warnings.append(
            {
                "model": model_name,
                "reason": "low_p1_label_coverage",
                "labels": [
                    {"label": row["label"], "field": row["field"], "ratio": row["ratio"]}
                    for row in low_label_coverage[:20]
                ],
                "count": len(low_label_coverage),
            }
        )

    results.append(
        {
            "model": model_name,
            "total": total,
            "domain": domain,
            "amount_field": amount_field,
            "amount_sum": amount_total,
            "amount_visible": amount_visible,
            "amount_summed": amount_summed,
            "axes": axes,
            "group_gap_axes": group_gap_axes,
            "label_source_missing_count": len(label_source_missing),
            "low_label_coverage_count": len(low_label_coverage),
            "label_coverage_sample": label_rows[:12],
        }
    )

payload = {
    "status": "FAIL" if blocking_gaps else "PASS",
    "database": env.cr.dbname,  # noqa: F821
    "mode": "user_data_reconciliation_full_scope_probe",
    "model_count": len(results),
    "blocking_gap_count": len(blocking_gaps),
    "warning_count": len(warnings),
    "empty_model_info_count": len(empty_model_infos),
    "low_volume_info_count": len(low_volume_infos),
    "blocking_gaps": blocking_gaps,
    "warnings": warnings[:120],
    "empty_model_infos": empty_model_infos[:120],
    "low_volume_infos": low_volume_infos[:120],
    "results": results,
}
output = artifact_root() / "user_data_reconciliation_full_scope_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("USER_DATA_RECONCILIATION_FULL_SCOPE_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

if blocking_gaps:
    raise SystemExit(1)
