#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    base_url = str(os.getenv("E2E_BASE_URL", "http://localhost:8069") or "").strip()
    db_name = str(os.getenv("DB_NAME", "sc_test") or "").strip()

    env = os.environ.copy()
    env["E2E_BASE_URL"] = base_url
    env["DB_NAME"] = db_name

    commands = [
        [sys.executable, "scripts/verify/native_business_admin_config_center_runtime_clickpath_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_center_intent_runtime_verify.py"],
    ]

    for command in commands:
        print("[config-center-stage-gate] RUN", " ".join(command))
        result = subprocess.run(command, env=env)
        if result.returncode != 0:
            print("[config-center-stage-gate] FAIL", " ".join(command))
            return int(result.returncode)

    print("[config-center-stage-gate] PASS all checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
