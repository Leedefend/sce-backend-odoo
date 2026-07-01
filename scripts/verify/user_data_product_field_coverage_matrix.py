#!/usr/bin/env python3
"""Build a user-data to product-field coverage matrix.

Run inside Odoo shell:
  DB_NAME=sc_demo make verify.user_data.product_field_coverage.matrix

The matrix answers a product-boundary question: for each historical user-visible
business label, is the current carrier a formal product field, a source-trace
field, a transition alias, or still missing?  The accepted baseline is zero
backlog: every user-visible label must resolve to a formal product carrier.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

from odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields import (  # noqa: E501
    LABEL_SOURCE_OVERRIDES,
    MODEL_LABEL_SOURCE_OVERRIDES,
    P1_ALIAS_LABELS,
)


TRANSITION_PREFIXES = ("p1_visible_", "legacy_visible_", "accepted_visible_", "user_acceptance_")
EXPLICIT_HISTORY_CARRIERS = {
    "legacy_attachment_ref",
    "legacy_line_attachment_ref",
    "legacy_attachment_name",
    "legacy_attachment_path",
    "creator_legacy_user_id",
    "legacy_residual_reason",
}
SOURCE_TRACE_PREFIXES = (
    "legacy_",
    "source_",
)
SOURCE_TRACE_FIELDS = {
    "create_uid",
    "create_date",
    "write_uid",
    "write_date",
    "old_id",
    "old_code",
}
MODEL_FORMAL_SOURCE_NAMED_FIELDS = {
    ("sc.legacy.user.profile", "legacy_created_at"),
}
SKIP_FIELD_TYPES = {"binary", "html", "one2many", "many2many"}


def _artifact_path() -> Path:
    raw = os.getenv("USER_DATA_PRODUCT_FIELD_COVERAGE_MATRIX_PATH")
    if raw:
        return Path(raw)
    return Path("/tmp/user_data_product_field_coverage_matrix.json")


def _text(value) -> str:
    return str(value or "").strip()


def _existing_fields(model_name: str) -> set[str]:
    return set(env[model_name]._fields)  # noqa: F821


def _domain_for_model(model_name: str) -> list[object]:
    fields = _existing_fields(model_name)
    if "source_origin" in fields:
        return [("source_origin", "=", "legacy")]
    if "legacy_record_id" in fields:
        return [("legacy_record_id", "!=", False)]
    if "legacy_source_id" in fields:
        return [("legacy_source_id", "!=", False)]
    if "legacy_source_model" in fields:
        return [("legacy_source_model", "!=", False)]
    if "legacy_fact_model" in fields:
        return [("legacy_fact_model", "!=", False)]
    return []


def _non_empty_count(model_name: str, field_name: str, domain: list[object]) -> int:
    field = env[model_name]._fields.get(field_name)  # noqa: F821
    if not field or field.type in SKIP_FIELD_TYPES:
        return 0
    if field.compute and not field.store:
        return 0
    if field.type == "boolean":
        return env[model_name].sudo().search_count(domain)  # noqa: F821
    return env[model_name].sudo().search_count(domain + [(field_name, "!=", False)])  # noqa: F821


def _candidate_fields(model_name: str, label: str) -> list[str]:
    fields = env[model_name]._fields  # noqa: F821
    candidates = [
        name
        for name, field in fields.items()
        if field.string == label and field.type not in SKIP_FIELD_TYPES
    ]
    candidates += list(MODEL_LABEL_SOURCE_OVERRIDES.get(model_name, {}).get(label, ()))
    candidates += list(LABEL_SOURCE_OVERRIDES.get(label, ()))
    seen: list[str] = []
    for name in candidates:
        if name in fields and name not in seen:
            seen.append(name)
    return seen


def _classify_field(model_name: str, field_name: str | None) -> str:
    if not field_name:
        return "missing"
    if (model_name, field_name) in MODEL_FORMAL_SOURCE_NAMED_FIELDS:
        return "formal_product"
    if field_name in EXPLICIT_HISTORY_CARRIERS:
        return "history_carrier"
    if field_name.startswith(TRANSITION_PREFIXES):
        return "transition_alias"
    if field_name in SOURCE_TRACE_FIELDS or field_name.startswith(SOURCE_TRACE_PREFIXES):
        return "source_trace"
    return "formal_product"


def _best_candidate(model_name: str, candidates: list[str], domain: list[object], total: int) -> tuple[str | None, int]:
    if not candidates:
        return None, 0
    if not total:
        return candidates[0], 0
    scored = []
    for index, field_name in enumerate(candidates):
        filled = _non_empty_count(model_name, field_name, domain)
        field_class = _classify_field(model_name, field_name)
        product_rank = 2 if field_class == "formal_product" else 1 if field_class == "source_trace" else 0
        scored.append((product_rank, filled, -index, field_name))
    product_rank, filled, _neg_index, field_name = max(scored)
    return field_name, filled


def _audit() -> dict[str, object]:
    rows = []
    by_model: dict[str, Counter] = {}
    totals = Counter()
    for model_name, labels in sorted(P1_ALIAS_LABELS.items()):
        if model_name not in env:  # noqa: F821
            rows.append(
                {
                    "model": model_name,
                    "label": None,
                    "field": None,
                    "field_class": "missing_model",
                    "filled": 0,
                    "total": 0,
                    "ratio": 0.0,
                }
            )
            totals["missing_model"] += 1
            continue
        domain = _domain_for_model(model_name)
        total = env[model_name].sudo().search_count(domain)  # noqa: F821
        by_model.setdefault(model_name, Counter())
        for label in labels:
            candidates = _candidate_fields(model_name, label)
            field_name, filled = _best_candidate(model_name, candidates, domain, total)
            field_class = _classify_field(model_name, field_name)
            ratio = round(filled / total, 4) if total else 1.0
            by_model[model_name][field_class] += 1
            totals[field_class] += 1
            rows.append(
                {
                    "model": model_name,
                    "label": label,
                    "field": field_name,
                    "field_class": field_class,
                    "filled": filled,
                    "total": total,
                    "ratio": ratio,
                    "candidate_fields": candidates[:12],
                }
            )
    backlog = [
        row
        for row in rows
        if row["field_class"] in {"missing", "transition_alias", "history_carrier", "source_trace"}
    ]
    return {
        "mode": "user_data_product_field_coverage_matrix",
        "database": env.cr.dbname,  # noqa: F821
        "policy": {
            "goal": "user-visible historical business data should be absorbed into formal product fields instead of remaining only in transition/history carriers",
            "classes": {
                "formal_product": "carrier is a stable product field",
                "source_trace": "carrier is a source/legacy trace field; usable for reconciliation but not yet productized",
                "transition_alias": "carrier is a p1/legacy/accepted/user_acceptance alias",
                "history_carrier": "carrier is an explicit history-only field",
                "missing": "no current carrier found for this user-visible label",
            },
        },
        "summary": {
            "label_count": sum(totals.values()),
            "by_field_class": dict(sorted(totals.items())),
            "models": len(by_model),
            "backlog_count": len(backlog),
        },
        "by_model": {
            model: dict(sorted(counter.items()))
            for model, counter in sorted(by_model.items())
        },
        "backlog": backlog,
        "rows": rows,
    }


def main() -> None:
    report = _audit()
    output = _artifact_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "[user_data_product_field_coverage_matrix] %s labels=%s formal=%s backlog=%s"
        % (
            "PASS" if report["summary"]["backlog_count"] == 0 else "FAIL",
            report["summary"]["label_count"],
            report["summary"]["by_field_class"].get("formal_product", 0),
            report["summary"]["backlog_count"],
        )
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if report["summary"]["backlog_count"]:
        print(json.dumps(report["backlog"][:20], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
