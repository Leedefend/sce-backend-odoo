#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEGACY_HANDLERS = ROOT / "addons" / "smart_core" / "handlers"
V2_REGISTRY = ROOT / "addons" / "smart_core" / "v2" / "intents" / "registry.py"

INTENT_PATTERN = re.compile(r'INTENT_TYPE\s*=\s*"([^"]+)"')
V2_INTENT_PATTERN = re.compile(r'intent_name\s*=\s*"([^"]+)"')


def collect_legacy_intents() -> set[str]:
    intents: set[str] = set()
    for path in LEGACY_HANDLERS.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        intents.update(INTENT_PATTERN.findall(text))
    return intents


def collect_v2_intents() -> set[str]:
    if not V2_REGISTRY.exists():
        return set()
    text = V2_REGISTRY.read_text(encoding="utf-8")
    return set(V2_INTENT_PATTERN.findall(text))


def build_report() -> dict:
    errors = []
    legacy = collect_legacy_intents()
    v2 = collect_v2_intents()
    if not V2_REGISTRY.exists():
        errors.append("missing_v2_registry")
    migrated = sorted(legacy.intersection(v2))
    missing = sorted(legacy - v2)
    v2_only = sorted(v2 - legacy)
    ratio = 0.0
    if legacy:
        ratio = round(len(migrated) / len(legacy), 4)
    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "legacy_intent_count": len(legacy),
        "v2_intent_count": len(v2),
        "migrated_count": len(migrated),
        "migration_ratio": ratio,
        "migrated": migrated,
        "missing_in_v2": missing,
        "v2_only": v2_only,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"migrated={report['migrated_count']}/{report['legacy_intent_count']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
