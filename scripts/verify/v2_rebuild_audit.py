#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


REQUIRED_FILES = [
    "addons/smart_core/v2/kernel/context.py",
    "addons/smart_core/v2/kernel/spec.py",
    "addons/smart_core/v2/kernel/pipeline.py",
    "addons/smart_core/v2/dispatcher.py",
    "addons/smart_core/v2/modules/app/handlers/catalog.py",
    "addons/smart_core/v2/modules/app/handlers/nav.py",
    "addons/smart_core/v2/modules/app/handlers/open.py",
    "addons/smart_core/v2/modules/app/services/catalog_service.py",
    "addons/smart_core/v2/modules/app/builders/catalog_builder.py",
    "addons/smart_core/v2/modules/app/policies/navigation_policy.py",
    "addons/smart_core/v2/modules/app/policies/availability_policy.py",
    "addons/smart_core/v2/modules/app/reason_codes.py",
]


def run() -> dict:
    missing = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            missing.append(rel)
    errors = []
    if missing:
        errors.append(f"missing_required_files:{len(missing)}")
    status = "PASS" if not errors else "FAIL"
    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": status,
        "errors": errors,
        "missing": missing,
        "required_count": len(REQUIRED_FILES),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"status={report['status']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
