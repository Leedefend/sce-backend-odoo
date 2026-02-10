#!/usr/bin/env python3
"""Guard parser rule quality for suggested_action."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARSER_PATH = ROOT / "frontend/apps/web/src/app/suggested_action/parser.ts"

ALIAS_BLOCK_RE = re.compile(r"const SIMPLE_ALIASES:[^=]*=\s*\{(?P<body>.*?)\n\};", re.DOTALL)
ALIAS_LINE_RE = re.compile(r"^\s{2}([a-z0-9_]+):\s*'([a-z0-9_]+)',?$", re.MULTILINE)
PREFIX_BLOCK_RE = re.compile(r"const (QUERY_ONLY_PREFIXES|QUERY_HASH_PREFIXES):[^=]*=\s*\[(?P<body>.*?)\n\];", re.DOTALL)
PREFIX_ITEM_RE = re.compile(r"\{\s*prefix:\s*'([^']+)',\s*kind:\s*'([a-z0-9_]+)'\s*\}")


def _fail(lines: list[str]) -> int:
    print("[FAIL] suggested_action parser guard")
    for line in lines:
        print(f"- {line}")
    return 1


def _extract_block(pattern: re.Pattern[str], source: str, label: str) -> str:
    m = pattern.search(source)
    if not m:
        raise ValueError(f"missing block: {label}")
    return m.group("body")


def main() -> int:
    if not PARSER_PATH.exists():
        return _fail([f"missing parser file: {PARSER_PATH}"])

    source = PARSER_PATH.read_text(encoding="utf-8")
    errors: list[str] = []

    try:
      alias_body = _extract_block(ALIAS_BLOCK_RE, source, "SIMPLE_ALIASES")
    except ValueError as exc:
      return _fail([str(exc)])

    alias_pairs = ALIAS_LINE_RE.findall(alias_body)
    if not alias_pairs:
        errors.append("SIMPLE_ALIASES has no entries")

    alias_keys = [k for k, _ in alias_pairs]
    alias_key_set = set(alias_keys)
    if len(alias_keys) != len(alias_key_set):
        errors.append("SIMPLE_ALIASES contains duplicate alias keys")

    for key in alias_keys:
        if key != key.lower():
            errors.append(f"alias key must be lowercase: {key}")

    prefix_map: dict[str, set[str]] = {}
    for match in PREFIX_BLOCK_RE.finditer(source):
        label = match.group(1)
        body = match.group("body")
        entries = PREFIX_ITEM_RE.findall(body)
        if not entries:
            errors.append(f"{label} has no entries")
            continue
        prefixes = [prefix for prefix, _kind in entries]
        if len(prefixes) != len(set(prefixes)):
            errors.append(f"{label} contains duplicate prefixes")
        prefix_map[label] = set(prefixes)

    if "QUERY_ONLY_PREFIXES" not in prefix_map:
        errors.append("missing QUERY_ONLY_PREFIXES block")
    if "QUERY_HASH_PREFIXES" not in prefix_map:
        errors.append("missing QUERY_HASH_PREFIXES block")

    overlap = sorted(prefix_map.get("QUERY_ONLY_PREFIXES", set()) & prefix_map.get("QUERY_HASH_PREFIXES", set()))
    if overlap:
        errors.append(f"QUERY_ONLY_PREFIXES and QUERY_HASH_PREFIXES overlap: {', '.join(overlap)}")

    if errors:
        return _fail(errors)

    print("[OK] suggested_action parser guard")
    print(f"- alias_count: {len(alias_pairs)}")
    print(f"- query_only_prefix_count: {len(prefix_map.get('QUERY_ONLY_PREFIXES', set()))}")
    print(f"- query_hash_prefix_count: {len(prefix_map.get('QUERY_HASH_PREFIXES', set()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
