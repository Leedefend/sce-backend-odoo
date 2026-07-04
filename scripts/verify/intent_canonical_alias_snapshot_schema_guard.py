#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = ROOT / "artifacts" / "backend" / "intent_canonical_alias_snapshot.json"
ALLOWED_STATUS = {"canonical", "alias"}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(ARTIFACT)
    errors: list[str] = []

    if not payload:
        errors.append(f"missing or invalid artifact: {ARTIFACT.relative_to(ROOT).as_posix()}")
    else:
        if payload.get("source") != "docs.contract.exports.intent_catalog":
            errors.append("source must be docs.contract.exports.intent_catalog")
        for key in ("canonical_count", "alias_count"):
            if not isinstance(payload.get(key), int):
                errors.append(f"{key} must be int")

        rows = payload.get("rows")
        if not isinstance(rows, list):
            errors.append("rows must be list")
            rows = []
        seen_names: set[str] = set()
        canonical_count = 0
        alias_count = 0
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"rows[{idx}] must be object")
                continue
            name = str(row.get("name") or "").strip()
            status = str(row.get("status") or "").strip()
            canonical = str(row.get("canonical") or "").strip()
            if not name:
                errors.append(f"rows[{idx}].name must be non-empty string")
            if status not in ALLOWED_STATUS:
                errors.append(f"rows[{idx}].status must be canonical|alias")
            if not canonical:
                errors.append(f"rows[{idx}].canonical must be non-empty string")
            if name:
                if name in seen_names:
                    errors.append(f"duplicate row name: {name}")
                seen_names.add(name)
            if status == "canonical":
                canonical_count += 1
                if canonical != name:
                    errors.append(f"canonical row must point to itself: {name}")
            elif status == "alias":
                alias_count += 1
                if canonical == name:
                    errors.append(f"alias row must not point to itself: {name}")

        if isinstance(payload.get("canonical_count"), int) and payload["canonical_count"] != canonical_count:
            errors.append("canonical_count must match canonical rows")
        if isinstance(payload.get("alias_count"), int) and payload["alias_count"] != alias_count:
            errors.append("alias_count must match alias rows")
        if rows != sorted(rows, key=lambda row: (str(row.get("name") or ""), str(row.get("status") or ""))):
            errors.append("rows must be sorted by name,status")

    if errors:
        print("[intent_canonical_alias_snapshot_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[intent_canonical_alias_snapshot_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
