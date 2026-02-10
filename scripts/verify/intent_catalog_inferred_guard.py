#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail if intent catalog still contains inferred examples.")
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
        inferred = item.get("inferred_example")
        if isinstance(inferred, dict) and inferred:
            offenders.append(intent)

    if offenders:
        names = ", ".join(sorted(set(offenders)))
        raise SystemExit(f"❌ inferred intent examples detected: {names}")

    print("[verify.intent_catalog.inferred_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
