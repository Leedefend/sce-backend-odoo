#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    env = os.environ.copy()
    env["E2E_BASE_URL"] = str(env.get("E2E_BASE_URL", "http://localhost:8069"))
    env["DB_NAME"] = str(env.get("DB_NAME", "sc_test"))

    commands = [
        [sys.executable, "scripts/verify/native_business_admin_config_center_stage_gate.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_center_intent_parity_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_governance_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_audit_trace_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_home_block_runtime_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_home_block_clickpath_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_home_block_intent_parity_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_role_entry_runtime_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_role_entry_frontend_consumer_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_role_entry_frontend_filter_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_role_entry_intent_parity_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_role_entry_filter_snapshot_verify.py"],
        [sys.executable, "scripts/verify/native_business_admin_config_role_entry_clickpath_evidence_verify.py"],
    ]

    for command in commands:
        print("[config-center-acceptance-pack] RUN", " ".join(command))
        result = subprocess.run(command, env=env)
        if result.returncode != 0:
            print("[config-center-acceptance-pack] FAIL", " ".join(command))
            return int(result.returncode)

    print("[config-center-acceptance-pack] PASS all checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
