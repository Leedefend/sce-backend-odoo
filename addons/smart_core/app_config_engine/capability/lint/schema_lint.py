# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from ..schema.capability_schema import validate_capability_row


def run_schema_lint(rows: Iterable[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    seen_keys: set[str] = set()
    for index, row in enumerate(rows):
        identity = row.get("identity") if isinstance(row, dict) else {}
        key = str((identity or {}).get("key") or "").strip()
        if key:
            if key in seen_keys:
                errors.append(f"row[{index}] duplicate identity.key={key}")
            seen_keys.add(key)
        for item in validate_capability_row(row):
            errors.append(f"row[{index}] {item}")
    return errors
