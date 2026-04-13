#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "addons" / "smart_core" / "v2" / "modules" / "app" / "builders" / "catalog_builder.py"
SERVICE = ROOT / "addons" / "smart_core" / "v2" / "modules" / "app" / "services" / "catalog_service.py"
REASON_CODES = ROOT / "addons" / "smart_core" / "v2" / "modules" / "app" / "reason_codes.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _has_all(text: str, tokens: List[str]) -> List[str]:
    return [token for token in tokens if token not in text]


def run_audit() -> Dict[str, object]:
    missing_files: List[str] = []
    for path in [BUILDER, SERVICE, REASON_CODES]:
        if not path.exists():
            missing_files.append(str(path.relative_to(ROOT)))

    builder_text = _read(BUILDER)
    service_text = _read(SERVICE)
    reason_text = _read(REASON_CODES)

    required_builder_tokens = [
        '"target_type"',
        '"delivery_mode"',
        '"is_clickable"',
        '"availability_status"',
        '"reason_code"',
        '"route"',
        '"active_match"',
        "normalize_reason_code",
        "build_app_catalog_contract",
        "build_app_nav_contract",
        "build_app_open_contract",
    ]
    required_service_tokens = [
        '"target_type"',
        '"delivery_mode"',
        '"is_clickable"',
        '"availability_status"',
        '"reason_code"',
        "self._status",
        "classify",
    ]
    required_reason_tokens = [
        "APP_REASON_CODE_SET",
        "APP_REASON_APP_KEY_MISSING",
        "APP_REASON_WORKSPACE_WORK_PARTIAL",
    ]

    missing_builder_tokens = _has_all(builder_text, required_builder_tokens)
    missing_service_tokens = _has_all(service_text, required_service_tokens)
    missing_reason_tokens = _has_all(reason_text, required_reason_tokens)

    errors = (
        [f"missing_file:{item}" for item in missing_files]
        + [f"missing_builder_token:{item}" for item in missing_builder_tokens]
        + [f"missing_service_token:{item}" for item in missing_service_tokens]
        + [f"missing_reason_token:{item}" for item in missing_reason_tokens]
    )

    status = "PASS"
    if errors:
        status = "FAIL"

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": status,
        "errors": errors,
        "missing_files": missing_files,
        "missing_builder_tokens": missing_builder_tokens,
        "missing_service_tokens": missing_service_tokens,
        "missing_reason_tokens": missing_reason_tokens,
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
