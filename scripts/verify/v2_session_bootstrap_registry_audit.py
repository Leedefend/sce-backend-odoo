#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]


REGISTRY_FILE = ROOT / "addons" / "smart_core" / "v2" / "intents" / "registry.py"
HANDLER_FILE = ROOT / "addons" / "smart_core" / "v2" / "handlers" / "system" / "session_bootstrap.py"
SCHEMA_FILE = ROOT / "addons" / "smart_core" / "v2" / "intents" / "schemas" / "session_bootstrap_schema.py"


def _load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load module: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_audit() -> Dict[str, object]:
    errors: List[str] = []

    if not REGISTRY_FILE.exists():
        errors.append("missing_registry_file")
        return {
            "gate_version": "v1",
            "gate_profile": "full",
            "status": "FAIL",
            "errors": errors,
        }

    registry_text = REGISTRY_FILE.read_text(encoding="utf-8")
    required_tokens = [
        'intent_name="session.bootstrap"',
        'canonical_intent="session.bootstrap"',
        "SessionBootstrapHandlerV2",
        'request_schema="addons.smart_core.v2.intents.schemas.session_bootstrap_schema.SessionBootstrapRequestSchemaV2"',
        'response_contract="v2.session.bootstrap.response.v1"',
        'capability_code="session.bootstrap"',
        'permission_mode="authenticated"',
        "idempotent=True",
        'version="v1"',
        "tags=(\"stage1\", \"registry_closure\", \"bootstrap\")",
    ]
    for token in required_tokens:
        if token not in registry_text:
            errors.append(f"missing_token:{token}")

    if not HANDLER_FILE.exists():
        errors.append("missing_handler_file")
    else:
        handler_text = HANDLER_FILE.read_text(encoding="utf-8")
        for token in ["class SessionBootstrapHandlerV2", 'intent_name = "session.bootstrap"']:
            if token not in handler_text:
                errors.append(f"missing_handler_token:{token}")

    if not SCHEMA_FILE.exists():
        errors.append("missing_schema_file")
    else:
        schema_text = SCHEMA_FILE.read_text(encoding="utf-8")
        for token in ["class SessionBootstrapRequestSchemaV2", "def validate("]:
            if token not in schema_text:
                errors.append(f"missing_schema_token:{token}")

    try:
        schema_module = _load_module_from_path("v2_session_bootstrap_schema", SCHEMA_FILE)
        schema_cls = getattr(schema_module, "SessionBootstrapRequestSchemaV2")
        normalized = schema_cls.validate({"app_key": "workspace"})
        if not isinstance(normalized, dict) or "app_key" not in normalized:
            errors.append("schema_validate_invalid_output")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"request_schema_unresolvable:{exc}")

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
