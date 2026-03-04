#!/usr/bin/env python3
"""Cross-report trend consistency guard for grouped governance artifacts."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BRIEF_JSON = ROOT / "artifacts" / "grouped_governance_brief_guard.json"
MATRIX_JSON = ROOT / "artifacts" / "grouped_governance_policy_matrix.json"
POLICY_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "grouped_governance_trend_consistency_guard_baseline.json"
REPORT_JSON = ROOT / "artifacts" / "grouped_governance_trend_consistency_guard.json"
REPORT_MD = ROOT / "artifacts" / "grouped_governance_trend_consistency_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except Exception:
            return None
    return None


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    policy = {
        "require_has_previous_aligned": True,
        "require_delta_typed_when_previous": True,
        "forbid_brief_failure_delta_positive": True,
        "forbid_brief_consistency_delta_negative": True,
        "forbid_matrix_policy_delta_negative": True,
    }
    baseline = _load_json(POLICY_BASELINE)
    if baseline:
        policy.update(baseline)

    brief = _load_json(BRIEF_JSON)
    matrix = _load_json(MATRIX_JSON)
    if not brief:
        errors.append(f"missing or invalid report: {BRIEF_JSON.relative_to(ROOT).as_posix()}")
    if not matrix:
        errors.append(f"missing or invalid report: {MATRIX_JSON.relative_to(ROOT).as_posix()}")

    brief_trend = brief.get("trend") if isinstance(brief.get("trend"), dict) else {}
    matrix_trend = matrix.get("trend") if isinstance(matrix.get("trend"), dict) else {}
    brief_delta = brief_trend.get("delta") if isinstance(brief_trend.get("delta"), dict) else {}
    matrix_delta = matrix_trend.get("delta") if isinstance(matrix_trend.get("delta"), dict) else {}

    has_previous_brief = bool(brief_trend.get("has_previous"))
    has_previous_matrix = bool(matrix_trend.get("has_previous"))
    has_previous_aligned = has_previous_brief == has_previous_matrix
    if bool(policy.get("require_has_previous_aligned", True)) and not has_previous_aligned:
        errors.append("trend.has_previous must be aligned between brief and policy_matrix")

    brief_cov_delta = _to_float(brief_delta.get("governance_coverage_ratio_delta"))
    brief_failure_delta = _to_int(brief_delta.get("governance_failure_count"))
    brief_consistency_delta = _to_int(brief_delta.get("grouped_e2e_max_consistency_score"))
    matrix_brief_policy_delta = _to_int(matrix_delta.get("grouped_governance_brief_policy_count"))
    matrix_drift_policy_delta = _to_int(matrix_delta.get("grouped_drift_summary_policy_count"))
    matrix_evidence_policy_delta = _to_int(matrix_delta.get("contract_evidence_grouped_governance_policy_count"))

    brief_delta_types_ok = (
        isinstance(brief_cov_delta, float)
        and isinstance(brief_failure_delta, int)
        and isinstance(brief_consistency_delta, int)
    )
    matrix_delta_types_ok = (
        isinstance(matrix_brief_policy_delta, int)
        and isinstance(matrix_drift_policy_delta, int)
        and isinstance(matrix_evidence_policy_delta, int)
    )

    if (has_previous_brief or has_previous_matrix) and bool(policy.get("require_delta_typed_when_previous", True)):
        if not brief_delta_types_ok:
            errors.append("brief trend delta types invalid when has_previous=true")
        if not matrix_delta_types_ok:
            errors.append("policy_matrix trend delta types invalid when has_previous=true")

    if bool(policy.get("forbid_brief_failure_delta_positive", True)) and isinstance(brief_failure_delta, int):
        if brief_failure_delta > 0:
            errors.append("brief governance_failure_count delta must be <= 0")
    if bool(policy.get("forbid_brief_consistency_delta_negative", True)) and isinstance(brief_consistency_delta, int):
        if brief_consistency_delta < 0:
            errors.append("brief grouped_e2e_max_consistency_score delta must be >= 0")
    if bool(policy.get("forbid_matrix_policy_delta_negative", True)):
        for key, value in (
            ("grouped_governance_brief_policy_count", matrix_brief_policy_delta),
            ("grouped_drift_summary_policy_count", matrix_drift_policy_delta),
            ("contract_evidence_grouped_governance_policy_count", matrix_evidence_policy_delta),
        ):
            if isinstance(value, int) and value < 0:
                errors.append(f"policy_matrix delta.{key} must be >= 0")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "has_previous_brief": has_previous_brief,
            "has_previous_matrix": has_previous_matrix,
            "has_previous_aligned": has_previous_aligned,
            "brief_delta_types_ok": brief_delta_types_ok,
            "matrix_delta_types_ok": matrix_delta_types_ok,
            "brief_delta_governance_coverage_ratio": brief_cov_delta,
            "brief_delta_governance_failure_count": brief_failure_delta,
            "brief_delta_grouped_e2e_max_consistency_score": brief_consistency_delta,
            "matrix_delta_grouped_governance_brief_policy_count": matrix_brief_policy_delta,
            "matrix_delta_grouped_drift_summary_policy_count": matrix_drift_policy_delta,
            "matrix_delta_contract_evidence_grouped_governance_policy_count": matrix_evidence_policy_delta,
        },
        "policy": policy,
        "errors": errors,
        "report": {
            "json": REPORT_JSON.relative_to(ROOT).as_posix(),
            "md": REPORT_MD.relative_to(ROOT).as_posix(),
        },
    }

    _write(REPORT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# Grouped Governance Trend Consistency Guard",
        "",
        f"- ok: {report['ok']}",
        f"- has_previous_aligned: {report['summary']['has_previous_aligned']}",
        f"- brief_delta_types_ok: {report['summary']['brief_delta_types_ok']}",
        f"- matrix_delta_types_ok: {report['summary']['matrix_delta_types_ok']}",
        (
            "- matrix_delta_grouped_governance_brief_policy_count: "
            f"{report['summary']['matrix_delta_grouped_governance_brief_policy_count']}"
        ),
        (
            "- matrix_delta_grouped_drift_summary_policy_count: "
            f"{report['summary']['matrix_delta_grouped_drift_summary_policy_count']}"
        ),
        (
            "- matrix_delta_contract_evidence_grouped_governance_policy_count: "
            f"{report['summary']['matrix_delta_contract_evidence_grouped_governance_policy_count']}"
        ),
        f"- report_json: `{report['report']['json']}`",
        f"- report_md: `{report['report']['md']}`",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend([f"- {line}" for line in errors])
    _write(REPORT_MD, "\n".join(lines) + "\n")

    print(str(REPORT_JSON.relative_to(ROOT)))
    print(str(REPORT_MD.relative_to(ROOT)))
    if errors:
        print("[grouped_governance_trend_consistency_guard] FAIL")
        return 1
    print("[grouped_governance_trend_consistency_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
