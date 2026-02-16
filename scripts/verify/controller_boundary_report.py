#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "delegate": ROOT / "artifacts" / "controller_delegate_guard.json",
    "allowlist_routes": ROOT / "artifacts" / "controller_allowlist_routes_guard.json",
    "route_policy": ROOT / "artifacts" / "controller_route_policy_guard.json",
}
OUT_JSON = ROOT / "artifacts" / "controller_boundary_guard_report.json"
OUT_MD = ROOT / "artifacts" / "controller_boundary_guard_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    items: dict[str, dict] = {}
    errors: list[str] = []
    for name, path in INPUTS.items():
        payload = _load_json(path)
        if not payload:
            errors.append(f"missing or invalid artifact: {path.relative_to(ROOT).as_posix()}")
            continue
        items[name] = payload

    checks = []
    for name in ("delegate", "allowlist_routes", "route_policy"):
        payload = items.get(name) or {}
        checks.append(
            {
                "name": name,
                "ok": bool(payload.get("ok")),
                "violation_count": int((payload.get("summary") or {}).get("violation_count") or 0),
            }
        )

    report = {
        "ok": (not errors) and all(item["ok"] for item in checks),
        "errors": errors,
        "checks": checks,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Controller Boundary Guard Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- check_count: {len(checks)}",
        f"- error_count: {len(errors)}",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        lines.append(
            f"- {item['name']}: {'PASS' if item['ok'] else 'FAIL'} "
            f"(violations={item['violation_count']})"
        )
    if errors:
        lines.extend(["", "## Errors", ""])
        for item in errors:
            lines.append(f"- {item}")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON))
    print(str(OUT_MD))
    if not report["ok"]:
        print("[controller_boundary_report] FAIL")
        return 1
    print("[controller_boundary_report] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
