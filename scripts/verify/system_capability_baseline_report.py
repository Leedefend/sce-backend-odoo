#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "scripts" / "verify" / "baselines" / "system_capability_baseline_v1.json"
OUT_JSON = ROOT / "artifacts" / "backend" / "system_capability_baseline_report.json"
OUT_MD = ROOT / "artifacts" / "backend" / "system_capability_baseline_report.md"
MODULE_MAP = ROOT / "docs" / "product" / "delivery" / "v1" / "module_scene_capability_map.md"
BUSINESS_BASELINE = ROOT / "scripts" / "verify" / "baselines" / "business_capability_baseline_snapshot.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def extract_md_int(text: str, key: str) -> int:
    match = re.search(rf"^- {re.escape(key)}:\s*`?([0-9]+)`?\s*$", text, re.MULTILINE)
    return int(match.group(1)) if match else 0


def make_target_exists(makefile: str, target: str) -> bool:
    return re.search(rf"^{re.escape(target)}\s*:", makefile, re.MULTILINE) is not None


def main() -> int:
    baseline = load_json(BASELINE)
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    if not baseline:
        print(f"missing or invalid baseline: {rel(BASELINE)}")
        return 1

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    module_text = MODULE_MAP.read_text(encoding="utf-8") if MODULE_MAP.is_file() else ""
    business_snapshot = load_json(BUSINESS_BASELINE)

    required_docs = [ROOT / item for item in baseline.get("required_docs", [])]
    for path in required_docs:
        ok = path.is_file()
        checks.append({"name": f"doc:{rel(path)}", "ok": ok})
        if not ok:
            errors.append(f"missing required doc: {rel(path)}")

    for target in baseline.get("required_make_targets", []):
        ok = make_target_exists(makefile, str(target))
        checks.append({"name": f"make:{target}", "ok": ok})
        if not ok:
            errors.append(f"missing required make target: {target}")

    module_count = extract_md_int(module_text, "module_count")
    scene_count = extract_md_int(module_text, "delivery_scope_scene_count")
    minimum = baseline.get("minimum_acceptance") if isinstance(baseline.get("minimum_acceptance"), dict) else {}
    module_min = safe_int(minimum.get("module_count_min"), 0)
    module_max = safe_int(minimum.get("module_count_max"), 9999)
    scene_min = safe_int(minimum.get("delivery_scope_scene_count_min"), 0)

    module_ok = module_min <= module_count <= module_max
    scene_ok = scene_count >= scene_min
    checks.append({"name": "metric:module_count", "ok": module_ok, "observed": module_count})
    checks.append({"name": "metric:delivery_scope_scene_count", "ok": scene_ok, "observed": scene_count})
    if not module_ok:
        errors.append(f"module_count out of baseline range: {module_count} not in [{module_min}, {module_max}]")
    if not scene_ok:
        errors.append(f"delivery_scope_scene_count below baseline: {scene_count} < {scene_min}")

    intent_min = safe_int(minimum.get("business_required_intent_count_min"), 0)
    role_min = safe_int(minimum.get("business_required_role_count_min"), 0)
    intent_count = safe_int(business_snapshot.get("required_intent_count"), 0)
    role_count = safe_int(business_snapshot.get("required_role_count"), 0)
    intent_ok = intent_count >= intent_min
    role_ok = role_count >= role_min
    checks.append({"name": "metric:business_required_intent_count", "ok": intent_ok, "observed": intent_count})
    checks.append({"name": "metric:business_required_role_count", "ok": role_ok, "observed": role_count})
    if not intent_ok:
        errors.append(f"business_required_intent_count below baseline: {intent_count} < {intent_min}")
    if not role_ok:
        errors.append(f"business_required_role_count below baseline: {role_count} < {role_min}")

    report = {
        "ok": not errors,
        "version": baseline.get("version"),
        "scope": baseline.get("scope"),
        "summary": {
            "check_count": len(checks),
            "failed_check_count": len([item for item in checks if not item.get("ok")]),
            "module_count": module_count,
            "delivery_scope_scene_count": scene_count,
            "business_required_intent_count": intent_count,
            "business_required_role_count": role_count
        },
        "checks": sorted(checks, key=lambda item: str(item.get("name") or "")),
        "errors": errors,
        "baseline": baseline
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# System Capability Baseline Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- version: {report['version']}",
        f"- check_count: {report['summary']['check_count']}",
        f"- failed_check_count: {report['summary']['failed_check_count']}",
        f"- module_count: {module_count}",
        f"- delivery_scope_scene_count: {scene_count}",
        f"- business_required_intent_count: {intent_count}",
        f"- business_required_role_count: {role_count}",
        "",
        "## Checks",
        ""
    ]
    for item in report["checks"]:
        suffix = f" observed={item['observed']}" if "observed" in item else ""
        lines.append(f"- {item['name']}: {'PASS' if item['ok'] else 'FAIL'}{suffix}")
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend([f"- {item}" for item in errors])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(OUT_JSON))
    print(str(OUT_MD))
    print("[system_capability_baseline_report] " + ("PASS" if report["ok"] else "FAIL"))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
