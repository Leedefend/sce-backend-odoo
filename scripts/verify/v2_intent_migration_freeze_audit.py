#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Set


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "addons" / "smart_core" / "v2" / "intents" / "registry.py"
SNAPSHOT = ROOT / "artifacts" / "v2" / "v2_intent_migration_freeze_v1.json"
INTENT_PATTERN = re.compile(r'intent_name\s*=\s*"([^"]+)"')


def _collect_v2_intents() -> Set[str]:
    if not REGISTRY.exists():
        return set()
    text = REGISTRY.read_text(encoding="utf-8")
    return set(INTENT_PATTERN.findall(text))


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    if not SNAPSHOT.exists():
        return {
            "gate_version": "v1",
            "gate_profile": "full",
            "status": "FAIL",
            "errors": ["missing_freeze_snapshot"],
        }

    freeze = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if freeze.get("snapshot_id") != "v2_intent_migration_freeze_v1":
        errors.append("invalid_snapshot_id")

    frozen_existing = set(str(item) for item in (freeze.get("frozen_existing_intents") or []))
    allow_new = set(str(item) for item in (freeze.get("allow_new_intents") or []))
    focus_intents = set(str(item) for item in (freeze.get("focus_intents") or []))

    current = _collect_v2_intents()

    if not frozen_existing:
        errors.append("empty_frozen_existing_intents")

    missing_focus = sorted(focus_intents - current)
    if missing_focus:
        errors.append(f"missing_focus_intents:{','.join(missing_focus)}")

    unexpected_new = sorted(current - frozen_existing - allow_new)
    if unexpected_new:
        errors.append(f"new_migrations_blocked:{','.join(unexpected_new)}")

    dropped_intents = sorted(frozen_existing - current)

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "stage_mode": str(freeze.get("stage_mode") or "dual_track_compare"),
        "focus_intents": sorted(focus_intents),
        "frozen_existing_count": len(frozen_existing),
        "current_count": len(current),
        "unexpected_new": unexpected_new,
        "dropped_intents": dropped_intents,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_audit()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
