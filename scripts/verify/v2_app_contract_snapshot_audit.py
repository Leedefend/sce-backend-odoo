#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "artifacts" / "v2" / "app_contract_snapshot_v1.json"
BUILDER = ROOT / "addons" / "smart_core" / "v2" / "modules" / "app" / "builders" / "catalog_builder.py"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    if not SNAPSHOT.exists():
        errors.append("missing snapshot: artifacts/v2/app_contract_snapshot_v1.json")
        return {
            "gate_version": "v1",
            "gate_profile": "full",
            "status": "FAIL",
            "errors": errors,
        }

    data = json.loads(_read_text(SNAPSHOT))
    if data.get("snapshot_id") != "app_contract_snapshot_v1":
        errors.append("invalid snapshot_id")

    schemas = data.get("schemas") if isinstance(data.get("schemas"), dict) else {}
    for name in ["app.catalog", "app.nav", "app.open"]:
        if name not in schemas:
            errors.append(f"missing schema {name}")

    builder_text = _read_text(BUILDER)
    required_tokens = [
        '"target_type"',
        '"delivery_mode"',
        '"is_clickable"',
        '"availability_status"',
        '"reason_code"',
        '"route"',
        '"active_match"',
    ]
    missing_tokens = [token for token in required_tokens if token not in builder_text]
    if missing_tokens:
        errors.append(f"builder missing tokens: {','.join(missing_tokens)}")

    catalog_schema = schemas.get("app.catalog", {})
    nav_schema = schemas.get("app.nav", {})
    open_schema = schemas.get("app.open", {})
    for schema_name, schema in [
        ("app.catalog", catalog_schema),
        ("app.nav", nav_schema),
    ]:
        fields = schema.get("required_item_fields") if isinstance(schema, dict) else None
        if not isinstance(fields, list) or not fields:
            errors.append(f"{schema_name} required_item_fields invalid")
    fields = open_schema.get("required_fields") if isinstance(open_schema, dict) else None
    if not isinstance(fields, list) or not fields:
        errors.append("app.open required_fields invalid")

    status = "PASS" if not errors else "FAIL"
    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": status,
        "errors": errors,
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
