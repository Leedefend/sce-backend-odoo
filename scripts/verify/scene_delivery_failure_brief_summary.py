#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "artifacts" / "backend" / "scene_delivery_failure_brief.json"


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(REPORT_PATH)
    if not payload:
        print("[scene_delivery_failure_brief_summary] missing_or_invalid_report")
        print(f"- path={REPORT_PATH.relative_to(ROOT).as_posix()}")
        return 0

    status = str(payload.get("status") or "UNKNOWN")
    failed_reports = _as_list(payload.get("failed_reports"))
    blocker_failures = _as_list(payload.get("blocker_failures"))
    precheck_failures = _as_list(payload.get("precheck_failures"))
    multi_company_warnings = _as_list(payload.get("multi_company_warnings"))
    next_actions = _as_list(payload.get("multi_company_next_actions"))

    print("[scene_delivery_failure_brief_summary]")
    print(f"- status={status}")
    print(f"- failed_reports={len(failed_reports)}")
    print(f"- blocker_failures={len(blocker_failures)}")
    print(f"- precheck_failures={len(precheck_failures)}")
    print(f"- multi_company_warnings={len(multi_company_warnings)}")

    if multi_company_warnings:
        print("- warnings:")
        for item in multi_company_warnings:
            print(f"  - {item}")
    if next_actions:
        print("- next_actions:")
        for item in next_actions:
            print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

