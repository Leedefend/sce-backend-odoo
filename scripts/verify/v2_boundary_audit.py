#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
V2_ROOT = ROOT / "addons" / "smart_core" / "v2"


REQUIRED_SYMBOLS = {
    "addons/smart_core/v2/intents/registry.py": ["class IntentRegistry", "def build_default_registry"],
    "addons/smart_core/v2/dispatcher.py": ["class IntentDispatcher", "def dispatch_intent"],
    "addons/smart_core/v2/handlers/base.py": ["class BaseIntentHandlerV2"],
    "addons/smart_core/v2/validators/base.py": ["class BaseIntentValidatorV2"],
    "addons/smart_core/v2/policies/permission_policy.py": ["class PermissionPolicyV2"],
    "addons/smart_core/v2/parsers/base.py": ["class BaseParserV2"],
    "addons/smart_core/v2/orchestrators/base.py": ["class BaseOrchestratorV2"],
    "addons/smart_core/v2/contracts/envelope.py": ["def make_envelope"],
    "addons/smart_core/v2/contracts/result.py": ["class IntentExecutionResultV2"],
}

FORBIDDEN_IMPORT_TOKENS = ["from odoo", "import odoo"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def run_audit() -> dict:
    missing_files = []
    missing_symbols = []
    forbidden_import_hits = []

    for rel_path, symbols in REQUIRED_SYMBOLS.items():
        path = ROOT / rel_path
        if not path.exists():
            missing_files.append(rel_path)
            continue
        text = read_text(path)
        for symbol in symbols:
            if symbol not in text:
                missing_symbols.append({"file": rel_path, "symbol": symbol})

    for file_path in V2_ROOT.rglob("*.py"):
        rel = str(file_path.relative_to(ROOT))
        text = read_text(file_path)
        for token in FORBIDDEN_IMPORT_TOKENS:
            if token in text:
                forbidden_import_hits.append({"file": rel, "token": token})

    errors = []
    if missing_files:
        errors.append(f"missing_files:{len(missing_files)}")
    if missing_symbols:
        errors.append(f"missing_symbols:{len(missing_symbols)}")
    if forbidden_import_hits:
        errors.append(f"forbidden_import_hits:{len(forbidden_import_hits)}")

    status = "PASS" if not errors else "FAIL"

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": status,
        "errors": errors,
        "missing_files": missing_files,
        "missing_symbols": missing_symbols,
        "forbidden_import_hits": forbidden_import_hits,
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
