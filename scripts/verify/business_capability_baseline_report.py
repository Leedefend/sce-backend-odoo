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


def main() -> int:
    checks = []
    errors = []
    for name, path in INPUTS.items():
        payload = _load_json(path)
        if not payload:
            checks.append({"name": name, "ok": False, "error_count": 1})
            errors.append(f"missing or invalid artifact: {path.relative_to(ROOT).as_posix()}")
            continue
        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        checks.append(
            {
                "name": name,
                "ok": bool(payload.get("ok")),
                "error_count": int(summary.get("error_count") or len(payload.get("errors") or [])),
            }
        )

    report = {
        "ok": (not errors) and all(item["ok"] for item in checks),
        "summary": {
            "check_count": len(checks),
            "failed_check_count": len([x for x in checks if not x.get("ok")]),
            "error_count": len(errors),
        },
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
