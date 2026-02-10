#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail if any intent examples have no response data/error key coverage."
    )
    parser.add_argument("--catalog", default="docs/contract/exports/intent_catalog.json")
    args = parser.parse_args()

    path = Path(args.catalog)
    if not path.exists():
        raise SystemExit(f"❌ missing catalog: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    intents = payload.get("intents") if isinstance(payload, dict) else None
    if not isinstance(intents, list):
        raise SystemExit("❌ invalid catalog shape: intents must be a list")

    offenders: list[str] = []
    for item in intents:
        if not isinstance(item, dict):
            continue
        intent = str(item.get("intent") or "").strip() or "<unknown>"
        examples = item.get("examples") if isinstance(item.get("examples"), list) else []
        if not examples:
            offenders.append(intent)
            continue
        has_covered_example = False
        for ex in examples:
            if not isinstance(ex, dict):
                continue
            data_keys = ex.get("response_data_keys") if isinstance(ex.get("response_data_keys"), list) else []
            err_keys = ex.get("response_error_keys") if isinstance(ex.get("response_error_keys"), list) else []
            if data_keys or err_keys:
                has_covered_example = True
                break
        if not has_covered_example:
            offenders.append(intent)

    if offenders:
        names = ", ".join(sorted(set(offenders)))
        raise SystemExit(f"❌ empty contract example coverage detected: {names}")

    print("[verify.intent_catalog.example_shape_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
