#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

COMMANDS = [
    ["python3", "scripts/verify/scene_governance_asset_export.py"],
    ["python3", "scripts/verify/backend_scene_authority_guard.py"],
    ["python3", "scripts/verify/backend_scene_canonical_entry_guard.py"],
    ["python3", "scripts/verify/backend_scene_menu_mapping_guard.py"],
    ["python3", "scripts/verify/backend_task_family_compat_gap_guard.py"],
    ["python3", "scripts/verify/backend_scene_provider_completeness_guard.py"],
    ["python3", "scripts/verify/scene_governance_export_consistency_guard.py"],
    ["python3", "scripts/verify/scene_governance_baseline_drift_guard.py"],
    ["python3", "scripts/verify/scene_governance_guard_export_parity_guard.py"],
    ["python3", "scripts/verify/scene_governance_family_priority_score.py"],
]


def main() -> int:
    for command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode != 0:
            print("[scene_governance_suite] FAIL")
            print(f"- failed_command: {' '.join(command)}")
            return result.returncode
    print("[scene_governance_suite] PASS")
    print(f"command_count={len(COMMANDS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
