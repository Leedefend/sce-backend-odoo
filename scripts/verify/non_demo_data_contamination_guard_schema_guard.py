#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "non_demo_data_contamination_guard.json"
REPORT_MD = ROOT / "artifacts" / "backend" / "non_demo_data_contamination_guard.md"
STATUSES = {"PASS", "FAIL", "SKIP"}
MODES = {"default", "forced", "demo-db-default-skip"}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(REPORT_JSON)
    errors: list[str] = []

    if not payload:
        errors.append(f"missing or invalid json: {REPORT_JSON.relative_to(ROOT).as_posix()}")
    else:
        if not isinstance(payload.get("ok"), bool):
            errors.append("ok must be bool")
        if payload.get("status") not in STATUSES:
            errors.append("status must be PASS|FAIL|SKIP")
        if not isinstance(payload.get("db_name"), str):
            errors.append("db_name must be string")
        if payload.get("mode") not in MODES:
            errors.append("mode must be default|forced|demo-db-default-skip")
        if not isinstance(payload.get("require_no_demo_data"), bool):
            errors.append("require_no_demo_data must be bool")
        if not isinstance(payload.get("errors"), list):
            errors.append("errors must be list")
        elif not all(isinstance(item, str) for item in payload["errors"]):
            errors.append("errors entries must be strings")
        if not isinstance(payload.get("demo_db_auto_skip"), bool):
            errors.append("demo_db_auto_skip must be bool")

        rules = payload.get("rules")
        if not isinstance(rules, dict):
            errors.append("rules must be object")
        else:
            for key in ("forbidden_config", "forbidden_xmlid_modules", "demo_name_tokens"):
                value = rules.get(key)
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    errors.append(f"rules.{key} must be string list")
            if not isinstance(rules.get("forbidden_module"), str):
                errors.append("rules.forbidden_module must be string")

        if payload.get("status") == "FAIL" and payload.get("ok") is not False:
            errors.append("FAIL report must set ok=false")
        if payload.get("status") in {"PASS", "SKIP"} and payload.get("ok") is not True:
            errors.append("PASS/SKIP report must set ok=true")
        if payload.get("status") == "SKIP" and payload.get("demo_db_auto_skip") is not True:
            errors.append("SKIP report must set demo_db_auto_skip=true")

    if not REPORT_MD.is_file():
        errors.append(f"missing markdown report: {REPORT_MD.relative_to(ROOT).as_posix()}")
    else:
        md_text = REPORT_MD.read_text(encoding="utf-8")
        for token in ("# Non-Demo Data Contamination Guard", "- status:", "- error_count:", "## Errors"):
            if token not in md_text:
                errors.append(f"markdown report missing token: {token}")

    if errors:
        print("[non_demo_data_contamination_guard_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[non_demo_data_contamination_guard_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
