#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_JSON = ROOT / "artifacts" / "contract" / "phase11_1_contract_evidence.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "contract_evidence_schema_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[contract_evidence_schema_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1
    payload = _load_json(EVIDENCE_JSON)
    if not payload:
        print("[contract_evidence_schema_guard] FAIL")
        print(f"missing or invalid evidence: {EVIDENCE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    required_sections = [
        str(item).strip()
        for item in (baseline.get("required_sections") if isinstance(baseline.get("required_sections"), list) else [])
        if str(item).strip()
    ]
    required_section_keys = baseline.get("required_section_keys") if isinstance(baseline.get("required_section_keys"), dict) else {}
    errors: list[str] = []

    for section in required_sections:
        if not isinstance(payload.get(section), dict):
            errors.append(f"missing section object: {section}")
            continue
        section_payload = payload.get(section) if isinstance(payload.get(section), dict) else {}
        keys = required_section_keys.get(section) if isinstance(required_section_keys.get(section), list) else []
        for key in keys:
            key = str(key).strip()
            if key and key not in section_payload:
                errors.append(f"section {section} missing key: {key}")

    top_codes = (
        payload.get("intent_catalog", {}).get("top_observed_reason_codes")
        if isinstance(payload.get("intent_catalog"), dict)
        else []
    )
    if not isinstance(top_codes, list):
        errors.append("intent_catalog.top_observed_reason_codes must be list")
        top_codes = []
    else:
        for idx, row in enumerate(top_codes):
            if not isinstance(row, dict):
                errors.append(f"top_observed_reason_codes[{idx}] must be object")
                continue
            if "reason_code" not in row:
                errors.append(f"top_observed_reason_codes[{idx}] missing key: reason_code")
            if "count" not in row:
                errors.append(f"top_observed_reason_codes[{idx}] missing key: count")

    if errors:
        print("[contract_evidence_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[contract_evidence_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
