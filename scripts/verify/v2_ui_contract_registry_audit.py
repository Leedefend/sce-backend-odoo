#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from v2.handlers.ui.ui_contract import UIContractHandlerV2  # type: ignore
    from v2.intents.registry import build_default_registry  # type: ignore
    from v2.intents.schemas.ui_contract_schema import UIContractRequestSchemaV2  # type: ignore

    registry = build_default_registry()
    try:
        entry = registry.get("ui.contract")
    except KeyError:
        entry = None
        errors.append("ui_contract_not_registered")

    if entry is not None:
        if str(getattr(entry, "canonical_intent", "")) != "ui.contract":
            errors.append("canonical_intent_mismatch")
        if str(getattr(entry, "intent_class", "")) != "ui":
            errors.append("intent_class_mismatch")

        tags = tuple(getattr(entry, "tags", ()) or ())
        for expected_tag in ("ui", "contract", "schema", "view"):
            if expected_tag not in tags:
                errors.append(f"missing_tag:{expected_tag}")

        if "UIContractRequestSchemaV2" not in str(getattr(entry, "request_schema", "")):
            errors.append("request_schema_path_mismatch")

        if entry.handler_factory is not UIContractHandlerV2:
            errors.append("handler_factory_mismatch")

    try:
        schema_result = UIContractRequestSchemaV2.validate(
            {"model": "res.partner", "view_type": "form"},
            {"trace_id": "ui-reg-1629"},
        )
        if bool(schema_result.get("schema_validated")) is not True:
            errors.append("schema_validate_marker_missing")
    except Exception as exc:  # pragma: no cover
        errors.append(f"schema_validate_failed:{exc}")

    proc = subprocess.run(
        ["python3", "scripts/verify/v2_intent_comparison_audit.py", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        errors.append("comparison_audit_command_failed")
        comparison = {}
    else:
        try:
            comparison = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            comparison = {}
            errors.append("comparison_audit_invalid_json")

    migrated = comparison.get("migrated") if isinstance(comparison.get("migrated"), list) else []
    if "ui.contract" not in migrated:
        errors.append("comparison_missing_migrated_ui_contract")

    migrated_count = int(comparison.get("migrated_count") or 0)
    if migrated_count <= 0:
        errors.append("comparison_migrated_count_invalid")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
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
