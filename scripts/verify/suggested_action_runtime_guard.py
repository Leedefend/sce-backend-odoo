#!/usr/bin/env python3
"""Guard runtime rule sets for suggested_action."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TYPES_PATH = ROOT / "frontend/apps/web/src/app/suggested_action/types.ts"
RUNTIME_PATH = ROOT / "frontend/apps/web/src/app/suggested_action/runtime.ts"

UNION_RE = re.compile(r"\|\s*'([^']*)'")
SET_BLOCK_RE = re.compile(r"const (\w+) = new Set<[^>]+>\(\[(?P<body>.*?)\]\);", re.DOTALL)
SET_ITEM_RE = re.compile(r"'([a-z0-9_]+)'")

EXPECTED_SETS = {
    "ROUTE_ACTIONS": {"open_route", "open_url"},
    "RETRY_ACTIONS": {"refresh", "retry"},
}


def _fail(lines: list[str]) -> int:
    print("[FAIL] suggested_action runtime guard")
    for line in lines:
        print(f"- {line}")
    return 1


def _load_kinds() -> set[str]:
    text = TYPES_PATH.read_text(encoding="utf-8")
    kinds = set(UNION_RE.findall(text))
    kinds.discard("")
    return kinds


def _load_sets() -> dict[str, set[str]]:
    text = RUNTIME_PATH.read_text(encoding="utf-8")
    parsed: dict[str, set[str]] = {}
    for m in SET_BLOCK_RE.finditer(text):
        name = m.group(1)
        body = m.group("body")
        parsed[name] = set(SET_ITEM_RE.findall(body))
    return parsed


def main() -> int:
    if not TYPES_PATH.exists() or not RUNTIME_PATH.exists():
        missing = [str(p) for p in (TYPES_PATH, RUNTIME_PATH) if not p.exists()]
        return _fail([f"missing files: {', '.join(missing)}"])

    kinds = _load_kinds()
    sets = _load_sets()
    errors: list[str] = []

    for name in ("ROUTE_ACTIONS", "RETRY_ACTIONS", "COPY_ACTIONS", "DIRECT_ACTIONS"):
        if name not in sets:
            errors.append(f"missing set: {name}")

    for name, values in sets.items():
        unknown = sorted(values - kinds)
        if unknown:
            errors.append(f"{name} contains unknown kinds: {', '.join(unknown)}")

    for name, expected in EXPECTED_SETS.items():
        actual = sets.get(name, set())
        if actual != expected:
            errors.append(f"{name} mismatch: expected={sorted(expected)} actual={sorted(actual)}")

    copy_or_direct = sets.get("COPY_ACTIONS", set()) | sets.get("DIRECT_ACTIONS", set())
    overlap = sorted(sets.get("RETRY_ACTIONS", set()) & copy_or_direct)
    if overlap:
        errors.append(f"retry actions must not overlap direct/copy sets: {', '.join(overlap)}")

    if errors:
        return _fail(errors)

    print("[OK] suggested_action runtime guard")
    for name in sorted(sets.keys()):
        print(f"- {name}: {len(sets[name])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
