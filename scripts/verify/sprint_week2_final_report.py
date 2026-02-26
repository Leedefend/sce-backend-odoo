#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_JSON = ROOT / "artifacts" / "backend" / "semantic_behavior_guard_report.json"
TREND_JSON = ROOT / "artifacts" / "backend" / "runtime_trend_report.json"
EXPLAIN_JSON = ROOT / "artifacts" / "backend" / "catalog_runtime_explain_report.json"
PRODUCT_V2_JSON = ROOT / "artifacts" / "backend" / "product_module_graph_v2.json"

REPORT_JSON = ROOT / "artifacts" / "backend" / "sprint_week2_final_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "sprint_week2_final_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    semantic = _load(SEMANTIC_JSON)
    trend = _load(TREND_JSON)
    explain = _load(EXPLAIN_JSON)
    product = _load(PRODUCT_V2_JSON)

    drift_count = int(((semantic.get("summary") or {}).get("drift_count")) or 0)
    trend_points = int(((trend.get("summary") or {}).get("scene_series_points")) or 0)
    unknown_source = int(((explain.get("summary") or {}).get("unknown_source_count")) or 0)
    product_cap_count = int(((product.get("summary") or {}).get("product_capability_count")) or 0)
    module_count = int(((product.get("summary") or {}).get("industry_module_count")) or 0)
    unassigned_cap = int(((product.get("summary") or {}).get("unassigned_capability_count")) or 0)

    checks = {
        "semantic_drift_guard_pass": drift_count == 0,
        "trend_data_ready_7d": trend_points >= 7,
        "catalog_runtime_unknown_source_eq_0": unknown_source == 0,
        "product_matrix_complete": product_cap_count == 16 and module_count == 8 and unassigned_cap == 0,
    }
    if not checks["semantic_drift_guard_pass"]:
        errors.append(f"semantic_drift_count={drift_count}")
    if not checks["trend_data_ready_7d"]:
        errors.append(f"scene_series_points={trend_points} (<7)")
    if not checks["catalog_runtime_unknown_source_eq_0"]:
        errors.append(f"unknown_source_count={unknown_source}")
    if not checks["product_matrix_complete"]:
        errors.append(
            f"product_matrix_mismatch(product_capability_count={product_cap_count}, industry_module_count={module_count}, unassigned_capability_count={unassigned_cap})"
        )

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "semantic_drift_count": drift_count,
            "trend_scene_series_points": trend_points,
            "catalog_runtime_unknown_source_count": unknown_source,
            "product_capability_count": product_cap_count,
            "industry_module_count": module_count,
            "product_unassigned_capability_count": unassigned_cap,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Sprint Week2 Final Report",
        "",
        f"- semantic_drift_count: {drift_count}",
        f"- trend_scene_series_points: {trend_points}",
        f"- catalog_runtime_unknown_source_count: {unknown_source}",
        f"- product_capability_count: {product_cap_count}",
        f"- industry_module_count: {module_count}",
        f"- product_unassigned_capability_count: {unassigned_cap}",
        f"- error_count: {len(errors)}",
        "",
        "## Checks",
        "",
    ]
    for k, v in checks.items():
        lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[sprint_week2_final_report] FAIL")
        return 2
    print("[sprint_week2_final_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

