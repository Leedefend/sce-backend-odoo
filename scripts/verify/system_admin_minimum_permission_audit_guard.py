#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "role_capability_floor_prod_like.json"
ROLE_FLOOR_JSON = ROOT / "artifacts" / "backend" / "role_capability_floor_prod_like.json"
WRITE_INTENT_AUDIT_MD = ROOT / "docs" / "ops" / "audit" / "write_intent_permission_audit.md"
OUT_JSON = ROOT / "artifacts" / "backend" / "system_admin_minimum_permission_audit_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "system_admin_minimum_permission_audit_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_risk_counts(markdown: str) -> tuple[int, int]:
    high_match = re.search(r"high_risk_count:\s*(\d+)", markdown)
    medium_match = re.search(r"medium_risk_count:\s*(\d+)", markdown)
    high = int(high_match.group(1)) if high_match else -1
    medium = int(medium_match.group(1)) if medium_match else -1
    return high, medium


def main() -> int:
    errors: list[str] = []
    summary: dict = {
        "baseline_fixture_count": 0,
        "baseline_has_admin_fixture": False,
        "runtime_has_admin_role": False,
        "write_intent_high_risk_count": -1,
        "write_intent_medium_risk_count": -1,
    }

    baseline = _load_json(BASELINE_JSON)
    fixtures = baseline.get("fixtures") if isinstance(baseline.get("fixtures"), list) else []
    summary["baseline_fixture_count"] = len(fixtures)
    admin_fixture_found = False
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            continue
        role = str(fixture.get("role") or "").strip().lower()
        login = str(fixture.get("login") or "").strip().lower()
        if role == "admin" or login == "admin":
            admin_fixture_found = True
            break
    summary["baseline_has_admin_fixture"] = admin_fixture_found
    if admin_fixture_found:
        errors.append("prod-like fixture baseline must not include admin account")

    floor = _load_json(ROLE_FLOOR_JSON)
    roles = floor.get("roles") if isinstance(floor.get("roles"), list) else []
    runtime_admin_found = False
    for row in roles:
        if not isinstance(row, dict):
            continue
        role = str(row.get("role") or "").strip().lower()
        login = str(row.get("login") or "").strip().lower()
        if role == "admin" or login == "admin":
            runtime_admin_found = True
            break
    summary["runtime_has_admin_role"] = runtime_admin_found
    if runtime_admin_found:
        errors.append("runtime role floor should not rely on admin fixture")

    if not WRITE_INTENT_AUDIT_MD.is_file():
        errors.append(f"missing write-intent audit: {WRITE_INTENT_AUDIT_MD.as_posix()}")
    else:
        text = WRITE_INTENT_AUDIT_MD.read_text(encoding="utf-8")
        high_count, medium_count = _extract_risk_counts(text)
        summary["write_intent_high_risk_count"] = high_count
        summary["write_intent_medium_risk_count"] = medium_count
        if high_count < 0 or medium_count < 0:
            errors.append("unable to parse risk counters from write-intent audit")
        if high_count > 0:
            errors.append(f"write-intent audit has high-risk findings: {high_count}")
        if medium_count > 0:
            errors.append(f"write-intent audit has medium-risk findings: {medium_count}")

    report = {
        "ok": len(errors) == 0,
        "summary": summary,
        "errors": errors,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# System Admin Minimum Permission Audit Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- baseline_fixture_count: {summary['baseline_fixture_count']}",
        f"- baseline_has_admin_fixture: {summary['baseline_has_admin_fixture']}",
        f"- runtime_has_admin_role: {summary['runtime_has_admin_role']}",
        f"- write_intent_high_risk_count: {summary['write_intent_high_risk_count']}",
        f"- write_intent_medium_risk_count: {summary['write_intent_medium_risk_count']}",
        f"- error_count: {len(errors)}",
    ]
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if errors:
        print("[system_admin_minimum_permission_audit_guard] FAIL")
        return 1
    print("[system_admin_minimum_permission_audit_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

