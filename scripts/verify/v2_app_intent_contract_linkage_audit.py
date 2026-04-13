#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "addons" / "smart_core" / "v2" / "intents" / "registry.py"
SNAPSHOT = ROOT / "artifacts" / "v2" / "app_contract_snapshot_v1.json"

INTENT_EXPECTATIONS = {
    "app.catalog": "v2.app.catalog.response.v1",
    "app.nav": "v2.app.nav.response.v1",
    "app.open": "v2.app.open.response.v1",
}
SNAPSHOT_SCHEMAS = {
    "app.catalog",
    "app.nav",
    "app.open",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    if not REGISTRY.exists():
        errors.append("missing registry.py")
    if not SNAPSHOT.exists():
        errors.append("missing app_contract_snapshot_v1.json")

    registry_text = _read(REGISTRY)
    snapshot_text = _read(SNAPSHOT)

    for intent_name, response_contract in INTENT_EXPECTATIONS.items():
        if intent_name not in registry_text:
            errors.append(f"registry missing intent: {intent_name}")
        if response_contract not in registry_text:
            errors.append(f"registry missing response_contract: {response_contract}")

    snapshot_json = json.loads(snapshot_text) if snapshot_text else {}
    schemas = snapshot_json.get("schemas") if isinstance(snapshot_json.get("schemas"), dict) else {}
    for schema_name in SNAPSHOT_SCHEMAS:
        if schema_name not in schemas:
            errors.append(f"snapshot missing schema: {schema_name}")

    status = "PASS" if not errors else "FAIL"
    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": status,
        "errors": errors,
        "intent_count": len(INTENT_EXPECTATIONS),
        "schema_count": len(schemas) if isinstance(schemas, dict) else 0,
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
