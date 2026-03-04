#!/usr/bin/env python3
"""Aggregate grouped governance signals into one auditable brief artifact."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INPUT_GOVERNANCE_COVERAGE = ROOT / "artifacts" / "contract_governance_coverage.json"
INPUT_GROUPED_DRIFT = ROOT / "artifacts" / "grouped_drift_summary_guard.json"
OUT_JSON = ROOT / "artifacts" / "grouped_governance_brief_guard.json"
OUT_MD = ROOT / "artifacts" / "grouped_governance_brief_guard.md"
OUT_PREV_JSON = ROOT / "artifacts" / "grouped_governance_brief_guard.prev.json"


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


def _coverage_ratio_to_float(raw: Any) -> float | None:
    if not isinstance(raw, str) or "/" not in raw:
        return None
    left, right = raw.split("/", 1)
    left_i = _to_int(left)
    right_i = _to_int(right)
    if left_i is None or right_i in (None, 0):
        return None
    return float(left_i) / float(right_i)


def _build_delta(cur: dict, prev: dict, keys: list[str]) -> dict:
    delta: dict[str, int | None] = {}
    for key in keys:
        cur_i = _to_int(cur.get(key))
        prev_i = _to_int(prev.get(key))
        if cur_i is None or prev_i is None:
            delta[key] = None
            continue
        delta[key] = cur_i - prev_i
    return delta


def main() -> int:
    prev = _load_json(OUT_JSON)
    governance = _load_json(INPUT_GOVERNANCE_COVERAGE)
    grouped_drift = _load_json(INPUT_GROUPED_DRIFT)

    issues: list[str] = []
    if not governance:
        issues.append(f"missing_or_invalid: {INPUT_GOVERNANCE_COVERAGE.as_posix()}")
    if not grouped_drift:
        issues.append(f"missing_or_invalid: {INPUT_GROUPED_DRIFT.as_posix()}")

    governance_ok = bool(governance.get("ok")) if governance else False
    grouped_drift_ok = bool(grouped_drift.get("ok")) if grouped_drift else False
    if governance and not governance_ok:
        issues.append("contract_governance_coverage_not_ok")
    if grouped_drift and not grouped_drift_ok:
        issues.append("grouped_drift_summary_not_ok")

    grouped_summary = grouped_drift.get("summary") if isinstance(grouped_drift.get("summary"), dict) else {}

    governance_files = governance.get("files") if isinstance(governance.get("files"), dict) else {}
    governance_failures = governance.get("failures") if isinstance(governance.get("failures"), list) else []
    total_file_count = len(governance_files)
    covered_file_count = sum(1 for item in governance_files.values() if isinstance(item, dict) and item.get("covered") is True)

    summary = {
        "ok": len(issues) == 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "contract_governance_coverage": INPUT_GOVERNANCE_COVERAGE.as_posix(),
            "grouped_drift_summary_guard": INPUT_GROUPED_DRIFT.as_posix(),
        },
        "checks": {
            "contract_governance_coverage_ok": governance_ok,
            "grouped_drift_summary_ok": grouped_drift_ok,
        },
        "summary": {
            "governance_coverage_ratio": governance.get("coverage_ratio"),
            "governance_covered_file_count": covered_file_count,
            "governance_total_file_count": total_file_count,
            "governance_failure_count": len(governance_failures),
            "grouped_e2e_case_count": grouped_summary.get("e2e_case_count"),
            "grouped_e2e_grouped_rows_case_count": grouped_summary.get("e2e_grouped_rows_case_count"),
            "grouped_e2e_max_consistency_score": grouped_summary.get("e2e_max_consistency_score"),
            "grouped_export_marker_hits": grouped_summary.get("export_marker_hits"),
            "grouped_export_marker_total": grouped_summary.get("export_marker_total"),
        },
        "issues": issues,
    }

    prev_summary = prev.get("summary") if isinstance(prev.get("summary"), dict) else {}
    delta = _build_delta(
        summary["summary"],
        prev_summary,
        [
            "governance_covered_file_count",
            "governance_total_file_count",
            "governance_failure_count",
            "grouped_e2e_case_count",
            "grouped_e2e_grouped_rows_case_count",
            "grouped_e2e_max_consistency_score",
            "grouped_export_marker_hits",
            "grouped_export_marker_total",
        ],
    )
    cur_cov = _coverage_ratio_to_float(summary["summary"].get("governance_coverage_ratio"))
    prev_cov = _coverage_ratio_to_float(prev_summary.get("governance_coverage_ratio"))
    coverage_delta = None if (cur_cov is None or prev_cov is None) else (cur_cov - prev_cov)

    trend = {
        "has_previous": bool(prev),
        "previous_generated_at": prev.get("generated_at") if isinstance(prev, dict) else None,
        "delta": {
            **delta,
            "governance_coverage_ratio_delta": coverage_delta,
        },
    }
    summary["trend"] = trend

    if trend["has_previous"]:
        if isinstance(coverage_delta, float) and coverage_delta < 0:
            issues.append("governance_coverage_ratio_regressed")
        if isinstance(delta.get("governance_failure_count"), int) and delta["governance_failure_count"] > 0:
            issues.append("governance_failure_count_increased")
        if (
            isinstance(delta.get("grouped_e2e_max_consistency_score"), int)
            and delta["grouped_e2e_max_consistency_score"] < 0
        ):
            issues.append("grouped_e2e_max_consistency_score_regressed")
        summary["ok"] = len(issues) == 0

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    if prev:
        OUT_PREV_JSON.write_text(json.dumps(prev, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Grouped Governance Brief Guard",
        "",
        f"- status: {'PASS' if summary['ok'] else 'FAIL'}",
        f"- generated_at: {summary['generated_at']}",
        f"- governance_coverage_ratio: {summary['summary']['governance_coverage_ratio']}",
        f"- governance_covered_file_count: {summary['summary']['governance_covered_file_count']}",
        f"- governance_total_file_count: {summary['summary']['governance_total_file_count']}",
        f"- governance_failure_count: {summary['summary']['governance_failure_count']}",
        f"- grouped_e2e_case_count: {summary['summary']['grouped_e2e_case_count']}",
        f"- grouped_e2e_grouped_rows_case_count: {summary['summary']['grouped_e2e_grouped_rows_case_count']}",
        f"- grouped_e2e_max_consistency_score: {summary['summary']['grouped_e2e_max_consistency_score']}",
        f"- grouped_export_marker_hits: {summary['summary']['grouped_export_marker_hits']}",
        f"- grouped_export_marker_total: {summary['summary']['grouped_export_marker_total']}",
        "",
        "## Check Status",
        "",
        f"- contract_governance_coverage_ok: {governance_ok}",
        f"- grouped_drift_summary_ok: {grouped_drift_ok}",
    ]
    if trend["has_previous"]:
        d = trend["delta"]
        lines.extend(
            [
                "",
                "## Trend",
                "",
                f"- previous_generated_at: {trend['previous_generated_at']}",
                f"- delta.governance_coverage_ratio: {d.get('governance_coverage_ratio_delta')}",
                f"- delta.governance_covered_file_count: {d.get('governance_covered_file_count')}",
                f"- delta.governance_total_file_count: {d.get('governance_total_file_count')}",
                f"- delta.governance_failure_count: {d.get('governance_failure_count')}",
                f"- delta.grouped_e2e_case_count: {d.get('grouped_e2e_case_count')}",
                f"- delta.grouped_e2e_grouped_rows_case_count: {d.get('grouped_e2e_grouped_rows_case_count')}",
                f"- delta.grouped_e2e_max_consistency_score: {d.get('grouped_e2e_max_consistency_score')}",
                f"- delta.grouped_export_marker_hits: {d.get('grouped_export_marker_hits')}",
                f"- delta.grouped_export_marker_total: {d.get('grouped_export_marker_total')}",
            ]
        )
    if issues:
        lines.extend(["", "## Issues", ""])
        lines.extend([f"- {item}" for item in issues])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON.relative_to(ROOT)))
    print(str(OUT_MD.relative_to(ROOT)))
    if not summary["ok"]:
        print("[grouped_governance_brief_guard] FAIL")
        return 1
    print("[grouped_governance_brief_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
