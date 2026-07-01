#!/usr/bin/env python3
"""Audit the boundary between industry handling capability and user data fill.

Run inside Odoo shell:
  DB_NAME=sc_demo make verify.industry_module.handling_capability_boundary

Policy:
- smart_construction_core must define the formal product fields and handling
  surface needed to continue business work.
- smart_construction_custom may fill those fields from historical user data and
  may keep source/history traces, but history fields must not be the product
  capability.
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
SOURCE_TRACE_PREFIXES = ("legacy_", "source_")
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
SYSTEM_OR_TRACE_LABEL_TOKENS = (
    "状态",
    "推送结果",
    "录入",
    "登记人",
    "登记时间",
    "创建",
    "修改",
)


def _artifact_path() -> Path:
    raw = os.getenv("INDUSTRY_MODULE_HANDLING_CAPABILITY_BOUNDARY_AUDIT_PATH")
    return Path(raw or "/tmp/industry_module_handling_capability_boundary_audit.json")


def _fields(model_name: str):
    return env[model_name]._fields  # noqa: F821


def _domain_for_model(model_name: str) -> list[object]:
    names = set(_fields(model_name))
    if "source_origin" in names:
        return [("source_origin", "=", "legacy")]
    if "legacy_record_id" in names:
        return [("legacy_record_id", "!=", False)]
    if "legacy_source_id" in names:
        return [("legacy_source_id", "!=", False)]
    if "legacy_source_model" in names:
        return [("legacy_source_model", "!=", False)]
    if "legacy_fact_model" in names:
        return [("legacy_fact_model", "!=", False)]
    return []


def _non_empty_count(model_name: str, field_name: str, domain: list[object]) -> int:
    field = _fields(model_name).get(field_name)
    if not field or field.type in SKIP_FIELD_TYPES:
        return 0
    if field.compute and not field.store:
        return 0
    if field.type == "boolean":
        return env[model_name].sudo().search_count(domain)  # noqa: F821
    return env[model_name].sudo().search_count(domain + [(field_name, "!=", False)])  # noqa: F821


def _candidate_fields(model_name: str, label: str) -> list[str]:
    fields = _fields(model_name)
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


def _carrier_class(model_name: str, field_name: str | None) -> str:
    if not field_name:
        return "missing"
    if (model_name, field_name) in MODEL_FORMAL_SOURCE_NAMED_FIELDS:
        return "formal_candidate"
    if field_name in EXPLICIT_HISTORY_CARRIERS:
        return "history_carrier"
    if field_name.startswith(TRANSITION_PREFIXES):
        return "user_history_transition_field"
    if field_name in SOURCE_TRACE_FIELDS or field_name.startswith(SOURCE_TRACE_PREFIXES):
        return "source_trace_only"
    return "formal_candidate"


def _field_module(field) -> str:
    return str(getattr(field, "_module", "") or getattr(field, "module", "") or "")


def _field_editability(field) -> str:
    if not field:
        return "missing"
    if field.compute and not getattr(field, "inverse", None):
        return "derived_readonly"
    if getattr(field, "readonly", False):
        return "readonly"
    return "editable"


def _is_system_or_trace_label(label: str) -> bool:
    return any(token in label for token in SYSTEM_OR_TRACE_LABEL_TOKENS)


def _capability_class(model_name: str, label: str, field_name: str | None) -> str:
    carrier = _carrier_class(model_name, field_name)
    if carrier != "formal_candidate":
        return carrier
    field = _fields(model_name).get(field_name)
    module = _field_module(field)
    editability = _field_editability(field)
    if module == "smart_construction_custom":
        return "user_module_formal_field"
    if editability == "editable":
        return "industry_editable_product_field"
    if _is_system_or_trace_label(label):
        return "industry_operational_metadata"
    return "industry_derived_product_field"


def _best_candidate(model_name: str, label: str, candidates: list[str], domain: list[object], total: int) -> tuple[str | None, int]:
    if not candidates:
        return None, 0
    scored = []
    for index, field_name in enumerate(candidates):
        field = _fields(model_name).get(field_name)
        filled = _non_empty_count(model_name, field_name, domain) if total else 0
        capability = _capability_class(model_name, label, field_name)
        rank = {
            "industry_editable_product_field": 6,
            "industry_derived_product_field": 5,
            "industry_operational_metadata": 4,
            "user_module_formal_field": 3,
            "source_trace_only": 2,
            "user_history_transition_field": 1,
            "history_carrier": 0,
            "missing": 0,
        }.get(capability, 0)
        module_rank = 1 if _field_module(field) == "smart_construction_core" else 0
        scored.append((rank, module_rank, filled, -index, field_name))
    _rank, _module_rank, filled, _neg_index, field_name = max(scored)
    return field_name, filled


def _audit() -> dict[str, object]:
    rows = []
    by_model: dict[str, Counter] = {}
    totals = Counter()
    for model_name, labels in sorted(P1_ALIAS_LABELS.items()):
        if model_name not in env:  # noqa: F821
            totals["missing_model"] += len(labels)
            rows.extend(
                {
                    "model": model_name,
                    "label": label,
                    "field": None,
                    "capability_class": "missing_model",
                    "field_module": "",
                    "field_editability": "missing",
                    "filled": 0,
                    "total": 0,
                    "candidate_fields": [],
                }
                for label in labels
            )
            continue
        domain = _domain_for_model(model_name)
        total = env[model_name].sudo().search_count(domain)  # noqa: F821
        by_model.setdefault(model_name, Counter())
        for label in labels:
            candidates = _candidate_fields(model_name, label)
            field_name, filled = _best_candidate(model_name, label, candidates, domain, total)
            field = _fields(model_name).get(field_name) if field_name else None
            capability = _capability_class(model_name, label, field_name)
            totals[capability] += 1
            by_model[model_name][capability] += 1
            rows.append(
                {
                    "model": model_name,
                    "label": label,
                    "field": field_name,
                    "capability_class": capability,
                    "field_module": _field_module(field) if field else "",
                    "field_editability": _field_editability(field),
                    "filled": filled,
                    "total": total,
                    "ratio": round(filled / total, 4) if total else 1.0,
                    "candidate_fields": candidates[:12],
                }
            )
    action_required_classes = {
        "missing",
        "missing_model",
        "history_carrier",
        "user_history_transition_field",
        "user_module_formal_field",
        "source_trace_only",
    }
    action_required = [row for row in rows if row["capability_class"] in action_required_classes]
    return {
        "mode": "industry_module_handling_capability_boundary_audit",
        "database": env.cr.dbname,  # noqa: F821
        "policy": {
            "industry_module": "defines formal product fields, forms, editability, workflow and downstream handling",
            "user_module": "fills historical user data into formal fields and keeps source/history traces only",
            "action_required": sorted(action_required_classes),
        },
        "summary": {
            "label_count": len(rows),
            "by_capability_class": dict(sorted(totals.items())),
            "models": len(by_model),
            "action_required_count": len(action_required),
        },
        "by_model": {
            model: dict(sorted(counter.items()))
            for model, counter in sorted(by_model.items())
        },
        "action_required": action_required,
        "rows": rows,
    }


def main() -> None:
    report = _audit()
    output = _artifact_path()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "[industry_module_handling_capability_boundary_audit] %s labels=%s industry_editable=%s action_required=%s"
        % (
            "PASS" if report["summary"]["action_required_count"] == 0 else "FAIL",
            report["summary"]["label_count"],
            report["summary"]["by_capability_class"].get("industry_editable_product_field", 0),
            report["summary"]["action_required_count"],
        )
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if report["summary"]["action_required_count"]:
        print(json.dumps(report["action_required"][:20], ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
