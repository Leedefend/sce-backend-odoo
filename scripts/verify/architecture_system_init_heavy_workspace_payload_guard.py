#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
HANDLER = ROOT / "addons/smart_core/handlers/system_init.py"


def main() -> int:
    text = HANDLER.read_text(encoding="utf-8", errors="ignore") if HANDLER.is_file() else ""
    violations = []

    heavy_markers = [
        "_build_task_action_rows",
        "_build_payment_action_rows",
        "_build_risk_action_rows",
        "_build_project_action_rows",
    ]
    for marker in heavy_markers:
        if marker in text:
            violations.append(f"system_init handler should not directly own heavy workspace builder: {marker}")

    if violations:
        print("[verify.architecture.system_init_heavy_workspace_payload_guard] FAIL")
        for item in violations:
            print(item)
        return 1
    print("[verify.architecture.system_init_heavy_workspace_payload_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

