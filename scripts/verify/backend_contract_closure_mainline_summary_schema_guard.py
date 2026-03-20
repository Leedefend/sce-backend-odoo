#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
SUMMARY_JSON = ROOT / "artifacts" / "backend" / "backend_contract_closure_mainline_summary.json"


def main() -> int:
    if not SUMMARY_JSON.is_file():
        print("[backend_contract_closure_mainline_summary_schema_guard] FAIL")
        print(f"missing summary: {SUMMARY_JSON.relative_to(ROOT).as_posix()}")
        return 2

    try:
        payload = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        print("[backend_contract_closure_mainline_summary_schema_guard] FAIL")
        print(f"invalid json: {exc}")
        return 2

    errors: list[str] = []
    if not isinstance(payload, dict):
        errors.append("summary root must be object")
    else:
        if not isinstance(payload.get("ok"), bool):
            errors.append("ok must be bool")
        if not isinstance(payload.get("generated_at"), str):
            errors.append("generated_at must be string")

        checks = payload.get("checks")
        if not isinstance(checks, dict):
            errors.append("checks must be object")
        else:
            for key in (
                "closure_structure_guard",
                "closure_snapshot_guard",
                "intent_alias_snapshot_guard",
            ):
                value = checks.get(key)
                if value not in {"PASS", "FAIL", "SKIP"}:
                    errors.append(f"checks.{key} must be PASS|FAIL|SKIP")

        overall = payload.get("overall")
        if not isinstance(overall, dict):
            errors.append("overall must be object")
        else:
            if overall.get("status") not in {"PASS", "FAIL"}:
                errors.append("overall.status must be PASS|FAIL")
            if not isinstance(overall.get("policy"), str):
                errors.append("overall.policy must be string")

    if errors:
        print("[backend_contract_closure_mainline_summary_schema_guard] FAIL")
        for row in errors:
            print(row)
        return 2

    print("[backend_contract_closure_mainline_summary_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

