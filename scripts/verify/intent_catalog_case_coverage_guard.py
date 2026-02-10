#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"❌ failed to parse JSON: {path}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure intent.invoke cases are covered by intent_catalog examples."
    )
    parser.add_argument("--cases-file", default="docs/contract/cases.yml")
    parser.add_argument("--catalog", default="docs/contract/exports/intent_catalog.json")
    args = parser.parse_args()

    cases_file = Path(args.cases_file)
    catalog_file = Path(args.catalog)
    if not cases_file.exists():
        raise SystemExit(f"❌ missing cases file: {cases_file}")
    if not catalog_file.exists():
        raise SystemExit(f"❌ missing intent catalog file: {catalog_file}")

    cases_payload = _load_json(cases_file)
    catalog_payload = _load_json(catalog_file)

    if not isinstance(cases_payload, list):
        raise SystemExit("❌ cases file must be a JSON array")
    intents = catalog_payload.get("intents") if isinstance(catalog_payload, dict) else None
    if not isinstance(intents, list):
        raise SystemExit("❌ intent catalog must contain intents[]")

    expected_pairs: set[tuple[str, str]] = set()
    for item in cases_payload:
        if not isinstance(item, dict):
            continue
        if str(item.get("op") or "").strip() != "intent.invoke":
            continue
        case = str(item.get("case") or "").strip()
        intent = str(item.get("intent") or "").strip()
        if case and intent:
            expected_pairs.add((intent, case))

    actual_pairs: set[tuple[str, str]] = set()
    for item in intents:
        if not isinstance(item, dict):
            continue
        intent_name = str(item.get("intent") or "").strip()
        if not intent_name:
            continue
        for ex in item.get("examples") or []:
            if not isinstance(ex, dict):
                continue
            case = str(ex.get("case") or "").strip()
            if case and case != "__inferred__":
                actual_pairs.add((intent_name, case))

    missing = sorted(expected_pairs - actual_pairs)
    if missing:
        formatted = [f"{intent}:{case}" for intent, case in missing]
        raise SystemExit(
            "❌ missing intent case coverage in catalog examples:\n- " + "\n- ".join(formatted)
        )

    print("[verify.intent_catalog.case_coverage_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
