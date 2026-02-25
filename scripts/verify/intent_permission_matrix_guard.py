#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "intent_permission_matrix.json"
ALLOWED_ACL_MODES = {"record_rule", "explicit_check"}


def main() -> int:
    if not REPORT_JSON.is_file():
        print(f"[intent_permission_matrix_guard] FAIL missing report: {REPORT_JSON}")
        return 2
    try:
        payload = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[intent_permission_matrix_guard] FAIL invalid json: {exc}")
        return 2

    rows = payload.get("rows") if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        print("[intent_permission_matrix_guard] FAIL report rows missing")
        return 2

    failures: list[str] = []
    write_count = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        if not bool(row.get("is_write")):
            continue
        write_count += 1
        intent = str(row.get("intent") or "")
        groups = [str(x).strip() for x in (row.get("required_groups") or []) if str(x).strip()]
        acl_mode = str(row.get("acl_mode") or "").strip()
        if not groups:
            failures.append(f"{intent}: required_groups empty")
        if acl_mode not in ALLOWED_ACL_MODES:
            failures.append(f"{intent}: invalid acl_mode '{acl_mode}'")

    print(
        f"[intent_permission_matrix_guard] write_intents={write_count} failures={len(failures)}"
    )
    if failures:
        for item in failures:
            print(f"- {item}")
        print("[intent_permission_matrix_guard] FAIL")
        return 2
    print("[intent_permission_matrix_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
