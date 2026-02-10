#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def _as_str(value) -> str:
    return str(value or "").strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate docs/contract/cases.yml integrity for contract snapshot export."
    )
    parser.add_argument("--cases-file", default="docs/contract/cases.yml")
    args = parser.parse_args()

    path = Path(args.cases_file)
    if not path.exists():
        raise SystemExit(f"❌ missing cases file: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"❌ invalid cases JSON: {exc}")

    if not isinstance(payload, list):
        raise SystemExit("❌ cases file must be a JSON array")

    seen: set[str] = set()
    duplicated: set[str] = set()
    invalid: list[str] = []

    for idx, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            invalid.append(f"#{idx}: case item must be object")
            continue

        case_name = _as_str(item.get("case"))
        user = _as_str(item.get("user"))
        op = _as_str(item.get("op"))

        if not case_name:
            invalid.append(f"#{idx}: missing case")
            continue
        if case_name in seen:
            duplicated.add(case_name)
        seen.add(case_name)

        if not user:
            invalid.append(f"{case_name}: missing user")
        if not op:
            invalid.append(f"{case_name}: missing op")

        if op == "intent.invoke":
            intent = _as_str(item.get("intent"))
            if not intent:
                invalid.append(f"{case_name}: missing intent for op=intent.invoke")
            if "intent_params" in item and not isinstance(item.get("intent_params"), dict):
                invalid.append(f"{case_name}: intent_params must be object")

    if duplicated:
        invalid.append("duplicate case names: " + ", ".join(sorted(duplicated)))

    if invalid:
        raise SystemExit("❌ invalid cases integrity:\n- " + "\n- ".join(invalid))

    print("[verify.intent_cases.integrity_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
