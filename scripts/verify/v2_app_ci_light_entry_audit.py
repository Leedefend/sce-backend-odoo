#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
MAKEFILE = ROOT / "Makefile"
USAGE_DOC = ROOT / "docs" / "ops" / "v2_app_governance_gate_usage_v1.md"
CI_DOC = ROOT / "docs" / "ops" / "v2_app_governance_ci_entry_v1.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def run_audit() -> Dict[str, object]:
    errors: List[str] = []
    make_text = _read(MAKEFILE)
    usage_text = _read(USAGE_DOC)
    ci_text = _read(CI_DOC)

    required_make = [
        "verify.v2.app.ci.light",
        "verify.v2.app.all",
        "v2_app_governance_output_schema_audit.py",
    ]
    for token in required_make:
        if token not in make_text:
            errors.append(f"missing make target token: {token}")

    if "verify.v2.app.ci.light" not in usage_text:
        errors.append("usage doc missing verify.v2.app.ci.light")
    if "v2_app_governance_output_schema_audit.py" not in usage_text:
        errors.append("usage doc missing schema guard command")

    required_ci_doc_tokens = [
        "verify.v2.app.ci.light",
        "verify.v2.app.all",
        "v2_app_verify_all.py",
        "v2_app_governance_output_schema_audit.py",
        "gate_version",
        "gate_profile",
    ]
    for token in required_ci_doc_tokens:
        if token not in ci_text:
            errors.append(f"ci doc missing token: {token}")

    return {
        "gate_version": "v1",
        "gate_profile": "ci_light",
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
