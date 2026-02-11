#!/usr/bin/env python3
"""Guard scene observability smoke scripts against structural drift."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY_ROOT = ROOT / "scripts" / "verify"

TARGETS = {
    "fe_portal_scene_governance_action_smoke.js": {
        "must_contain": [
            "require('./scene_observability_utils')",
            "probeModels(",
            "assertRequiredModels(",
        ],
        "must_not_contain": [
            "function isModelMissing(",
        ],
    },
    "fe_scene_auto_degrade_smoke.js": {
        "must_contain": [
            "require('./scene_observability_utils')",
            "probeModels(",
            "assertRequiredModels(",
        ],
        "must_not_contain": [
            "function isModelMissing(",
        ],
    },
    "fe_scene_auto_degrade_notify_smoke.js": {
        "must_contain": [
            "require('./scene_observability_utils')",
            "probeModels(",
            "assertRequiredModels(",
        ],
        "must_not_contain": [
            "function isModelMissing(",
        ],
    },
    "fe_scene_package_import_smoke.js": {
        "must_contain": [
            "require('./scene_observability_utils')",
            "probeModels(",
            "assertRequiredModels(",
        ],
        "must_not_contain": [
            "function isModelMissing(",
        ],
    },
}


def main() -> int:
    errors: list[str] = []
    for rel, rules in TARGETS.items():
        path = VERIFY_ROOT / rel
        if not path.exists():
            errors.append(f"missing file: scripts/verify/{rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in rules.get("must_contain", []):
            if token not in text:
                errors.append(f"{rel}: missing token `{token}`")
        for token in rules.get("must_not_contain", []):
            if token in text:
                errors.append(f"{rel}: forbidden token present `{token}`")

    if errors:
        print("[FAIL] scene observability structure guard")
        for err in errors:
            print(f"- {err}")
        return 1

    print("[OK] scene observability structure guard")
    print(f"- files_checked: {len(TARGETS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
