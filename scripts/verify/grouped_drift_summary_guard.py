#!/usr/bin/env python3
"""Aggregate grouped drift signals and emit an auditable summary report."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
FE_TREE_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "fe_tree_grouped_signature.json"
E2E_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "e2e_grouped_rows_signature.json"
EVIDENCE_EXPORT = ROOT / "scripts" / "contract" / "export_evidence.py"
POLICY_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "grouped_drift_summary_guard_baseline.json"
REPORT_JSON = ROOT / "artifacts" / "grouped_drift_summary_guard.json"
REPORT_MD = ROOT / "artifacts" / "grouped_drift_summary_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_md(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    policy = {
        "require_group_key": True,
        "require_page_has_prev": True,
        "require_page_has_next": True,
        "require_page_window": True,
        "require_window_range_consistency_bool": True,
        "min_e2e_case_count": 1,
        "min_e2e_max_consistency_score_when_grouped_rows": 4,
        "min_export_marker_hits": 3,
    }
    policy_payload = _load_json(POLICY_BASELINE)
    if policy_payload:
        policy.update(policy_payload)

    fe_tree = _load_json(FE_TREE_BASELINE)
    e2e = _load_json(E2E_BASELINE)
    export_text = EVIDENCE_EXPORT.read_text(encoding="utf-8", errors="ignore") if EVIDENCE_EXPORT.is_file() else ""

    if not fe_tree:
        errors.append(f"missing or invalid baseline: {FE_TREE_BASELINE.relative_to(ROOT).as_posix()}")
    if not e2e:
        errors.append(f"missing or invalid baseline: {E2E_BASELINE.relative_to(ROOT).as_posix()}")
    if not export_text:
        errors.append(f"missing evidence export script: {EVIDENCE_EXPORT.relative_to(ROOT).as_posix()}")

    grouped_fields = fe_tree.get("grouped_contract_fields") if isinstance(fe_tree.get("grouped_contract_fields"), dict) else {}
    grouped_field_checks = {
        "group_key": bool(grouped_fields.get("group_key")),
        "page_has_prev": bool(grouped_fields.get("page_has_prev")),
        "page_has_next": bool(grouped_fields.get("page_has_next")),
        "page_window": bool(grouped_fields.get("page_window")),
    }

    if bool(policy.get("require_group_key", True)) and not grouped_field_checks["group_key"]:
        errors.append("fe_tree grouped_contract_fields.group_key must be true")
    if bool(policy.get("require_page_has_prev", True)) and not grouped_field_checks["page_has_prev"]:
        errors.append("fe_tree grouped_contract_fields.page_has_prev must be true")
    if bool(policy.get("require_page_has_next", True)) and not grouped_field_checks["page_has_next"]:
        errors.append("fe_tree grouped_contract_fields.page_has_next must be true")
    if bool(policy.get("require_page_window", True)) and not grouped_field_checks["page_window"]:
        errors.append("fe_tree grouped_contract_fields.page_window must be true")

    semantic = fe_tree.get("grouped_pagination_semantic_summary") if isinstance(fe_tree.get("grouped_pagination_semantic_summary"), dict) else {}
    consistency = semantic.get("consistency") if isinstance(semantic.get("consistency"), dict) else {}
    window_range_consistency_is_bool = isinstance(consistency.get("first_group_page_window_matches_range"), bool)
    if bool(policy.get("require_window_range_consistency_bool", True)) and not window_range_consistency_is_bool:
        errors.append("fe_tree consistency.first_group_page_window_matches_range must be bool")

    grouped_cases = e2e.get("grouped_cases") if isinstance(e2e.get("grouped_cases"), list) else []
    if len(grouped_cases) < int(policy.get("min_e2e_case_count", 1) or 1):
        errors.append(
            "e2e grouped_cases size must be >= "
            f"{int(policy.get('min_e2e_case_count', 1) or 1)}"
        )

    max_consistency_score = 0
    grouped_rows_case_count = 0
    for idx, row in enumerate(grouped_cases):
        if not isinstance(row, dict):
            errors.append(f"e2e grouped_cases[{idx}] must be object")
            continue
        score = row.get("consistency_score")
        if not isinstance(score, int):
            errors.append(f"e2e grouped_cases[{idx}].consistency_score must be int")
            continue
        max_consistency_score = max(max_consistency_score, score)
        if row.get("has_grouped_rows") is True:
            grouped_rows_case_count += 1

    min_score_when_grouped_rows = int(policy.get("min_e2e_max_consistency_score_when_grouped_rows", 4) or 4)
    if grouped_rows_case_count > 0 and max_consistency_score < min_score_when_grouped_rows:
        errors.append(
            "e2e grouped rows present but max consistency_score < "
            f"{min_score_when_grouped_rows}"
        )

    export_markers = [
        '"grouped_pagination_contract": {',
        '"supports_page_window":',
        '"window_range_consistency":',
        '"consistency_score":',
        '"consistency_ok":',
    ]
    export_marker_hits = sum(1 for marker in export_markers if marker in export_text)
    min_export_marker_hits = int(policy.get("min_export_marker_hits", 3) or 3)
    if export_marker_hits < min_export_marker_hits:
        errors.append(f"export_evidence markers hit {export_marker_hits} < {min_export_marker_hits}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "fe_tree_group_fields": sorted(grouped_fields.keys()),
            "grouped_field_checks": grouped_field_checks,
            "window_range_consistency_is_bool": window_range_consistency_is_bool,
            "e2e_case_count": len(grouped_cases),
            "e2e_grouped_rows_case_count": grouped_rows_case_count,
            "e2e_max_consistency_score": max_consistency_score,
            "export_marker_hits": export_marker_hits,
            "export_marker_total": len(export_markers),
        },
        "policy": policy,
        "errors": errors,
        "report": {
            "json": REPORT_JSON.relative_to(ROOT).as_posix(),
            "md": REPORT_MD.relative_to(ROOT).as_posix(),
        },
    }

    _write_json(REPORT_JSON, report)
    md_lines = [
        "# Grouped Drift Summary Guard",
        "",
        f"- ok: {report['ok']}",
        f"- e2e_case_count: {report['summary']['e2e_case_count']}",
        f"- e2e_grouped_rows_case_count: {report['summary']['e2e_grouped_rows_case_count']}",
        f"- e2e_max_consistency_score: {report['summary']['e2e_max_consistency_score']}",
        f"- export_marker_hits: {report['summary']['export_marker_hits']} / {report['summary']['export_marker_total']}",
        f"- json: `{report['report']['json']}`",
        f"- md: `{report['report']['md']}`",
    ]
    if errors:
        md_lines.extend(["", "## Errors", *[f"- {line}" for line in errors]])
    _write_md(REPORT_MD, md_lines)

    print(str(REPORT_JSON.relative_to(ROOT)))
    print(str(REPORT_MD.relative_to(ROOT)))
    if errors:
        print("[grouped_drift_summary_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_drift_summary_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
