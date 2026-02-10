#!/usr/bin/env python3
"""Export suggested_action parser catalog for audit visibility."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARSER_PATH = ROOT / "frontend/apps/web/src/app/suggested_action/parser.ts"
OUT_PATH = ROOT / "artifacts/codex/suggested_action_catalog.json"

ALIAS_PAIR_RE = re.compile(r"^\s{2}([a-z0-9_]+):\s*'([a-z0-9_]+)',?$", re.MULTILINE)
PREFIX_KIND_RE = re.compile(r"\{\s*prefix:\s*'([^']+)',\s*kind:\s*'([^']+)'\s*\}")


def _slice_object(source: str, marker: str) -> str:
    start = source.find(marker)
    if start < 0:
        raise ValueError(f"missing marker: {marker}")
    tail = source[start:]
    open_brace = tail.find("{")
    close_brace = tail.find("};")
    if open_brace < 0 or close_brace < 0 or close_brace <= open_brace:
        raise ValueError(f"invalid object shape: {marker}")
    return tail[open_brace : close_brace + 1]


def _slice_array(source: str, marker: str) -> str:
    start = source.find(marker)
    if start < 0:
        raise ValueError(f"missing marker: {marker}")
    tail = source[start:]
    open_bracket = tail.find("[")
    close_bracket = tail.find("];")
    if open_bracket < 0 or close_bracket < 0 or close_bracket <= open_bracket:
        raise ValueError(f"invalid array shape: {marker}")
    return tail[open_bracket : close_bracket + 1]


def main() -> int:
    if not PARSER_PATH.exists():
        print(f"[FAIL] missing parser: {PARSER_PATH}")
        return 1

    source = PARSER_PATH.read_text(encoding="utf-8")
    try:
        alias_object = _slice_object(source, "const SIMPLE_ALIASES:")
        query_only_array = _slice_array(source, "const QUERY_ONLY_PREFIXES")
        query_hash_array = _slice_array(source, "const QUERY_HASH_PREFIXES")
    except ValueError as exc:
        print(f"[FAIL] {exc}")
        return 1

    alias_pairs = sorted(ALIAS_PAIR_RE.findall(alias_object))
    query_only = sorted(PREFIX_KIND_RE.findall(query_only_array))
    query_hash = sorted(PREFIX_KIND_RE.findall(query_hash_array))

    payload = {
        "source": str(PARSER_PATH.relative_to(ROOT)),
        "summary": {
            "alias_count": len(alias_pairs),
            "query_only_rule_count": len(query_only),
            "query_hash_rule_count": len(query_hash),
        },
        "aliases": [{"alias": alias, "kind": kind} for alias, kind in alias_pairs],
        "query_only_rules": [{"prefix": prefix, "kind": kind} for prefix, kind in query_only],
        "query_hash_rules": [{"prefix": prefix, "kind": kind} for prefix, kind in query_hash],
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    print("[OK] suggested_action catalog exported")
    print(f"- out: {OUT_PATH}")
    print(f"- alias_count: {len(alias_pairs)}")
    print(f"- query_only_rule_count: {len(query_only)}")
    print(f"- query_hash_rule_count: {len(query_hash)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
