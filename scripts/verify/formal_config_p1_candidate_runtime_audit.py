#!/usr/bin/env python3
"""Runtime audit for formal candidates behind config-contract P1 aliases.

Run inside ``odoo shell`` after the static contract audit has written
``/tmp/formal_config_p1_alias_contract_audit.json``.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path


INPUT_PATH = Path(os.environ.get("FORMAL_CONFIG_P1_ALIAS_AUDIT_INPUT_PATH") or "/tmp/formal_config_p1_alias_contract_audit.json")
OUT_JSON = Path(os.environ.get("FORMAL_CONFIG_P1_CANDIDATE_RUNTIME_AUDIT_PATH") or "/tmp/formal_config_p1_candidate_runtime_audit.json")
BUDGET_PATH = Path(os.environ.get("FORMAL_CONFIG_P1_CANDIDATE_RUNTIME_BUDGET_PATH") or "/tmp/formal_config_p1_candidate_runtime_budget_v1.json")
TRANSITION_PREFIXES = ("p1_visible_", "legacy_visible_", "accepted_visible_", "user_acceptance_")
GENERIC_LEGACY_VISIBLE_PREFIX = "legacy_visible_"


def _is_stable_formal_candidate(field_name: str) -> bool:
    if field_name.startswith("p1_visible_"):
        return False
    if field_name.startswith(GENERIC_LEGACY_VISIBLE_PREFIX):
        return False
    if field_name.startswith(("accepted_visible_", "user_acceptance_")):
        return False
    return True


def _field_type(model_fields, field_name: str) -> str:
    field = model_fields.get(field_name)
    return getattr(field, "type", "") if field else ""


def _field_string(model_fields, field_name: str) -> str:
    field = model_fields.get(field_name)
    return getattr(field, "string", "") if field else ""


def _label_string_candidates(model_fields, label: str) -> list[str]:
    if not label:
        return []
    return sorted(
        field_name
        for field_name, field in model_fields.items()
        if getattr(field, "string", "") == label and not field_name.startswith("p1_visible_")
    )


def _dedupe(values) -> list[str]:
    return list(dict.fromkeys([str(value) for value in values if value]))


def _row_runtime(row: dict[str, object]) -> dict[str, object]:
    model_name = str(row.get("model") or "")
    field_name = str(row.get("field") or "")
    label = str(row.get("label") or "")
    configured_candidates = _dedupe(row.get("formal_candidates") or [])
    if model_name not in env:  # noqa: F821
        return {
            **row,
            "model_exists": False,
            "alias_field_exists": False,
            "label_string_candidates": [],
            "runtime_candidates": configured_candidates,
            "existing_runtime_candidates": [],
            "stable_formal_candidates": [],
            "transition_existing_candidates": [],
            "candidate_field_types": {},
            "candidate_field_strings": {},
        }

    model_fields = env[model_name]._fields  # noqa: F821
    label_candidates = _label_string_candidates(model_fields, label)
    runtime_candidates = _dedupe(configured_candidates + label_candidates)
    existing = [candidate for candidate in runtime_candidates if candidate in model_fields]
    stable = [candidate for candidate in existing if _is_stable_formal_candidate(candidate)]
    transition = [candidate for candidate in existing if candidate not in stable]
    return {
        **row,
        "model_exists": True,
        "alias_field_exists": field_name in model_fields,
        "label_string_candidates": label_candidates,
        "runtime_candidates": runtime_candidates,
        "existing_runtime_candidates": existing,
        "stable_formal_candidates": stable,
        "transition_existing_candidates": transition,
        "candidate_field_types": {candidate: _field_type(model_fields, candidate) for candidate in existing},
        "candidate_field_strings": {candidate: _field_string(model_fields, candidate) for candidate in existing},
    }


def _summary(rows: list[dict[str, object]]) -> dict[str, object]:
    missing_model = [row for row in rows if not row["model_exists"]]
    missing_alias = [row for row in rows if row["model_exists"] and not row["alias_field_exists"]]
    without_existing = [row for row in rows if not row["existing_runtime_candidates"]]
    without_stable = [row for row in rows if not row["stable_formal_candidates"]]
    transition_only = [
        row
        for row in rows
        if row["transition_existing_candidates"] and not row["stable_formal_candidates"]
    ]
    return {
        "total_hits": len(rows),
        "model_missing_hits": len(missing_model),
        "alias_field_missing_hits": len(missing_alias),
        "with_existing_runtime_candidate_hits": sum(1 for row in rows if row["existing_runtime_candidates"]),
        "without_existing_runtime_candidate_hits": len(without_existing),
        "with_stable_formal_candidate_hits": sum(1 for row in rows if row["stable_formal_candidates"]),
        "without_stable_formal_candidate_hits": len(without_stable),
        "transition_candidate_only_hits": len(transition_only),
        "without_stable_formal_candidate_by_model": dict(sorted(Counter(row["model"] for row in without_stable).items())),
        "without_existing_runtime_candidate_by_model": dict(sorted(Counter(row["model"] for row in without_existing).items())),
    }


def _failures(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    failures = []
    missing_model = [row for row in rows if not row["model_exists"]]
    missing_alias = [row for row in rows if row["model_exists"] and not row["alias_field_exists"]]
    if missing_model:
        failures.append({"kind": "config_contract_model_missing_at_runtime", "count": len(missing_model), "sample": missing_model[:20]})
    if missing_alias:
        failures.append({"kind": "config_contract_p1_alias_field_missing_at_runtime", "count": len(missing_alias), "sample": missing_alias[:20]})
    return failures


def _budget_failures(summary: dict[str, object]) -> list[dict[str, object]]:
    if not BUDGET_PATH.exists():
        return []
    budget = json.loads(BUDGET_PATH.read_text(encoding="utf-8"))
    failures = []
    for key, limit in sorted((budget.get("max") or {}).items()):
        actual = summary.get(key)
        if isinstance(actual, int) and isinstance(limit, int) and actual > limit:
            failures.append({
                "kind": "formal_config_p1_candidate_runtime_budget_exceeded",
                "metric": key,
                "actual": actual,
                "max": limit,
            })
    return failures


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError("missing static audit input: %s" % INPUT_PATH)
    static_report = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    rows = [_row_runtime(row) for row in static_report.get("rows") or []]
    summary = _summary(rows)
    failures = _failures(rows) + _budget_failures(summary)
    report = {
        "mode": "formal_config_p1_candidate_runtime_audit",
        "boundary": {
            "input": INPUT_PATH.as_posix(),
            "budget": BUDGET_PATH.as_posix() if BUDGET_PATH.exists() else "",
            "policy": "a static mapping is only a promotion candidate after the target model and field exist at runtime; p1/legacy/accepted/user_acceptance prefixes remain transition candidates, not stable model-view fields",
        },
        "summary": summary,
        "failures": failures,
        "rows": rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = "FAIL" if report["failures"] else "PASS"
    print(
        "[formal_config_p1_candidate_runtime_audit] %s total=%s missing_model=%s missing_alias=%s without_existing_candidate=%s without_stable_candidate=%s"
        % (
            status,
            report["summary"]["total_hits"],
            report["summary"]["model_missing_hits"],
            report["summary"]["alias_field_missing_hits"],
            report["summary"]["without_existing_runtime_candidate_hits"],
            report["summary"]["without_stable_formal_candidate_hits"],
        )
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if report["failures"]:
        print(json.dumps({"failures": report["failures"]}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


main()
