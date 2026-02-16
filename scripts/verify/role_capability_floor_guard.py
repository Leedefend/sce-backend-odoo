#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SAMPLE_JSON = ROOT / "artifacts" / "scene_capability_contract_guard.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_guard.json"
ARTIFACT_JSON = ROOT / "artifacts" / "role_capability_floor_guard.json"
ARTIFACT_MD = ROOT / "artifacts" / "role_capability_floor_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[role_capability_floor_guard] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    sample = _load_json(SAMPLE_JSON)
    if not sample:
        print("[role_capability_floor_guard] FAIL")
        print(f"missing sample report: {SAMPLE_JSON.relative_to(ROOT).as_posix()}")
        print("hint: run make verify.capability.schema first")
        return 1

    role_samples = sample.get("role_samples") if isinstance(sample.get("role_samples"), dict) else {}
    required_roles = baseline.get("required_roles") if isinstance(baseline.get("required_roles"), dict) else {}
    checks = []
    errors = []
    for role, rule in sorted(required_roles.items()):
        rule = rule if isinstance(rule, dict) else {}
        min_caps = int(rule.get("min_capabilities") or 0)
        sample_row = role_samples.get(role) if isinstance(role_samples.get(role), dict) else {}
        actual = int(sample_row.get("capability_count") or 0)
        ok = actual >= min_caps
        checks.append(
            {
                "role": role,
                "ok": ok,
                "capability_count": actual,
                "min_capabilities": min_caps,
            }
        )
        if not ok:
            errors.append(f"{role}: capability_count {actual} < min_capabilities {min_caps}")

    report = {
        "ok": len(errors) <= int(baseline.get("max_errors", 0)),
        "baseline": baseline,
        "summary": {
            "required_role_count": len(required_roles),
            "sampled_role_count": len(role_samples),
            "error_count": len(errors),
        },
        "checks": checks,
        "errors": errors,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Role Capability Floor Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- required_role_count: {report['summary']['required_role_count']}",
        f"- sampled_role_count: {report['summary']['sampled_role_count']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        lines.append(
            f"- {item['role']}: {'PASS' if item['ok'] else 'FAIL'} "
            f"(capabilities={item['capability_count']}, min={item['min_capabilities']})"
        )
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    ARTIFACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(ARTIFACT_MD))
    if not report["ok"]:
        print("[role_capability_floor_guard] FAIL")
        return 1
    print("[role_capability_floor_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
