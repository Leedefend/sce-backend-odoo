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
        description="Validate intent.invoke cases map to existing intents in intent_catalog.json."
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

    catalog_intents = {
        str(item.get("intent") or "").strip()
        for item in intents
        if isinstance(item, dict) and str(item.get("intent") or "").strip()
    }
    if not catalog_intents:
        raise SystemExit("❌ intent catalog has no intent entries")

    unknown: list[str] = []
    for item in cases_payload:
        if not isinstance(item, dict):
            continue
        if str(item.get("op") or "").strip() != "intent.invoke":
            continue
        case = str(item.get("case") or "").strip() or "<unknown_case>"
        intent = str(item.get("intent") or "").strip()
        if intent and intent not in catalog_intents:
            unknown.append(f"{case}: unknown intent {intent}")

    if unknown:
        raise SystemExit("❌ intent cases not found in catalog:\n- " + "\n- ".join(sorted(unknown)))

    print("[verify.intent_cases.catalog_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
