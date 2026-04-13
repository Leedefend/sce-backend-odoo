#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP_REASON_CODES = ROOT / "addons" / "smart_core" / "v2" / "modules" / "app" / "reason_codes.py"
APP_BUILDERS = ROOT / "addons" / "smart_core" / "v2" / "modules" / "app" / "builders" / "catalog_builder.py"
APP_POLICY = ROOT / "addons" / "smart_core" / "v2" / "modules" / "app" / "policies" / "availability_policy.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def run_audit() -> dict:
    missing = []
    for path in [APP_REASON_CODES, APP_BUILDERS, APP_POLICY]:
        if not path.exists():
            missing.append(str(path.relative_to(ROOT)))

    reason_text = _read(APP_REASON_CODES)
    builder_text = _read(APP_BUILDERS)
    policy_text = _read(APP_POLICY)

    required_tokens = [
        "APP_REASON_APP_KEY_MISSING",
        "APP_REASON_WORKSPACE_WORK_PARTIAL",
        "normalize_reason_code",
        "available",
        "degraded",
        "unavailable",
    ]
    token_hits = {token: (token in (reason_text + "\n" + builder_text + "\n" + policy_text)) for token in required_tokens}
    missing_tokens = [token for token, hit in token_hits.items() if not hit]
    errors = [f"missing_file:{item}" for item in missing] + [f"missing_token:{item}" for item in missing_tokens]

    status = "PASS"
    if errors:
        status = "FAIL"

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": status,
        "errors": errors,
        "missing_files": missing,
        "missing_tokens": missing_tokens,
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
