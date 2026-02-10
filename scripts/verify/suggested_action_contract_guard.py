#!/usr/bin/env python3
"""Guard suggested action contract coverage between type union and UI presentation maps."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TYPES_PATH = ROOT / "frontend/apps/web/src/app/suggested_action/types.ts"
PRESENTATION_PATH = ROOT / "frontend/apps/web/src/app/suggested_action/presentation.ts"
PARSER_PATH = ROOT / "frontend/apps/web/src/app/suggested_action/parser.ts"

UNION_RE = re.compile(r"\|\s*'([^']*)'")
MAP_RE = re.compile(r"^\s{2}([a-z0-9_]+):\s*'([^']*)',?$", re.MULTILINE)
ALIAS_VALUE_RE = re.compile(r"^\s{2}[a-z0-9_]+:\s*'([a-z0-9_]+)',?$", re.MULTILINE)


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def _parse_kinds(types_text: str) -> set[str]:
    values = set(UNION_RE.findall(types_text))
    values.discard("")
    return values


def _parse_map_keys(presentation_text: str, const_name: str) -> set[str]:
    marker = f"const {const_name}:"
    start = presentation_text.find(marker)
    if start < 0:
        raise ValueError(f"missing constant: {const_name}")
    tail = presentation_text[start:]
    open_brace = tail.find("{")
    close_brace = tail.find("};")
    if open_brace < 0 or close_brace < 0 or close_brace <= open_brace:
        raise ValueError(f"invalid object shape: {const_name}")
    body = tail[open_brace:close_brace]
    return {match[0] for match in MAP_RE.findall(body)}


def _parse_map_values(presentation_text: str, const_name: str) -> dict[str, str]:
    marker = f"const {const_name}:"
    start = presentation_text.find(marker)
    if start < 0:
        raise ValueError(f"missing constant: {const_name}")
    tail = presentation_text[start:]
    open_brace = tail.find("{")
    close_brace = tail.find("};")
    if open_brace < 0 or close_brace < 0 or close_brace <= open_brace:
        raise ValueError(f"invalid object shape: {const_name}")
    body = tail[open_brace:close_brace]
    return {key: value for key, value in MAP_RE.findall(body)}


def _parse_alias_values(parser_text: str) -> set[str]:
    marker = "const SIMPLE_ALIASES:"
    start = parser_text.find(marker)
    if start < 0:
        raise ValueError("missing constant: SIMPLE_ALIASES")
    tail = parser_text[start:]
    open_brace = tail.find("{")
    close_brace = tail.find("};")
    if open_brace < 0 or close_brace < 0 or close_brace <= open_brace:
        raise ValueError("invalid object shape: SIMPLE_ALIASES")
    body = tail[open_brace:close_brace]
    return set(ALIAS_VALUE_RE.findall(body))


def _fail(lines: list[str]) -> int:
    print("[FAIL] suggested_action contract guard")
    for line in lines:
        print(f"- {line}")
    return 1


def main() -> int:
    try:
        kinds = _parse_kinds(_read(TYPES_PATH))
        presentation_text = _read(PRESENTATION_PATH)
        parser_text = _read(PARSER_PATH)
        labels = _parse_map_keys(presentation_text, "LABELS")
        hints = _parse_map_keys(presentation_text, "HINTS")
        label_values = _parse_map_values(presentation_text, "LABELS")
        hint_values = _parse_map_values(presentation_text, "HINTS")
        alias_values = _parse_alias_values(parser_text)
    except (FileNotFoundError, ValueError) as exc:
        return _fail([str(exc)])

    errors: list[str] = []
    missing_labels = sorted(kinds - labels)
    missing_hints = sorted(kinds - hints)
    unknown_labels = sorted(labels - kinds)
    unknown_hints = sorted(hints - kinds)
    unknown_alias_values = sorted(alias_values - kinds)
    blank_labels = sorted([key for key, value in label_values.items() if not value.strip()])
    blank_hints = sorted([key for key, value in hint_values.items() if not value.strip()])

    if missing_labels:
        errors.append(f"missing labels for: {', '.join(missing_labels)}")
    if missing_hints:
        errors.append(f"missing hints for: {', '.join(missing_hints)}")
    if unknown_labels:
        errors.append(f"labels contain unknown kinds: {', '.join(unknown_labels)}")
    if unknown_hints:
        errors.append(f"hints contain unknown kinds: {', '.join(unknown_hints)}")
    if unknown_alias_values:
        errors.append(f"alias map contains unknown kinds: {', '.join(unknown_alias_values)}")
    if blank_labels:
        errors.append(f"labels must not be blank: {', '.join(blank_labels)}")
    if blank_hints:
        errors.append(f"hints must not be blank: {', '.join(blank_hints)}")

    if errors:
        return _fail(errors)

    print("[OK] suggested_action contract guard")
    print(f"- kinds: {len(kinds)}")
    print(f"- labels: {len(labels)}")
    print(f"- hints: {len(hints)}")
    print(f"- alias_values: {len(alias_values)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
