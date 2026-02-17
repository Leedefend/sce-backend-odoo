#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "scene_catalog_runtime_alignment": ROOT / "artifacts" / "scene_catalog_runtime_alignment_guard.json",
    "business_core_journey": ROOT / "artifacts" / "business_core_journey_guard.json",
    "role_capability_floor": ROOT / "artifacts" / "role_capability_floor_guard.json",
}
BASELINE_SNAPSHOT = ROOT / "scripts" / "verify" / "baselines" / "business_capability_baseline_snapshot.json"
OUT_JSON = ROOT / "artifacts" / "business_capability_baseline_report.json"
OUT_MD = ROOT / "artifacts" / "business_capability_baseline_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def main() -> int:
    baseline_snapshot = _load_json(BASELINE_SNAPSHOT)
    checks = []
    errors = []
    observed = {
        "catalog_runtime_ratio": 0.0,
        "required_intent_count": 0,
        "required_role_count": 0,
    }
    for name, path in INPUTS.items():
        payload = _load_json(path)
        if not payload:
            checks.append({"name": name, "ok": False, "error_count": 1})
            errors.append(f"missing or invalid artifact: {path.relative_to(ROOT).as_posix()}")
            continue
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        if name == "scene_catalog_runtime_alignment":
            observed["catalog_runtime_ratio"] = _safe_float(summary.get("catalog_runtime_ratio"), 0.0)
        elif name == "business_core_journey":
            observed["required_intent_count"] = _safe_int(summary.get("required_intent_count"), 0)
        elif name == "role_capability_floor":
            observed["required_role_count"] = _safe_int(summary.get("required_role_count"), 0)
        checks.append(
            {
                "name": name,
                "ok": bool(payload.get("ok")),
                "error_count": int(summary.get("error_count") or len(payload.get("errors") or [])),
            }
        )

    delta_vs_baseline = {
        "check_count": len(checks) - _safe_int(baseline_snapshot.get("check_count"), 0),
        "required_intent_count": observed["required_intent_count"] - _safe_int(baseline_snapshot.get("required_intent_count"), 0),
        "required_role_count": observed["required_role_count"] - _safe_int(baseline_snapshot.get("required_role_count"), 0),
        "catalog_runtime_ratio": round(
            observed["catalog_runtime_ratio"] - _safe_float(baseline_snapshot.get("catalog_runtime_ratio"), 0.0),
            6,
        ),
    }

    report = {
        "ok": (not errors) and all(item["ok"] for item in checks),
        "summary": {
            "check_count": len(checks),
            "failed_check_count": len([x for x in checks if not x.get("ok")]),
            "error_count": len(errors),
            "required_intent_count": observed["required_intent_count"],
            "required_role_count": observed["required_role_count"],
            "catalog_runtime_ratio": observed["catalog_runtime_ratio"],
        },
        "baseline_snapshot": baseline_snapshot,
        "delta_vs_baseline": delta_vs_baseline,
        "checks": checks,
        "errors": errors,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Business Capability Baseline Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- check_count: {report['summary']['check_count']}",
        f"- failed_check_count: {report['summary']['failed_check_count']}",
        f"- error_count: {report['summary']['error_count']}",
        f"- required_intent_count: {report['summary']['required_intent_count']}",
        f"- required_role_count: {report['summary']['required_role_count']}",
        f"- catalog_runtime_ratio: {report['summary']['catalog_runtime_ratio']}",
        f"- delta_vs_baseline.check_count: {delta_vs_baseline['check_count']}",
        f"- delta_vs_baseline.required_intent_count: {delta_vs_baseline['required_intent_count']}",
        f"- delta_vs_baseline.required_role_count: {delta_vs_baseline['required_role_count']}",
        f"- delta_vs_baseline.catalog_runtime_ratio: {delta_vs_baseline['catalog_runtime_ratio']}",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        lines.append(
            f"- {item['name']}: {'PASS' if item['ok'] else 'FAIL'} "
            f"(error_count={item['error_count']})"
        )
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if not report["ok"]:
        print("[business_capability_baseline_report] FAIL")
        return 1
    print("[business_capability_baseline_report] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
