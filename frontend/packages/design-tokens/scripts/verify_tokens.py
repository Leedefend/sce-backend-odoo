#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_WEB = ROOT / "dist" / "web"
DIST_SHARED = ROOT / "dist" / "shared"

UNRESOLVED_PATTERN = re.compile(r"\{[a-zA-Z0-9_.]+\}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def verify_no_unresolved_tokens() -> list[str]:
    errors: list[str] = []
    css_files = [DIST_WEB / "tokens.css", DIST_WEB / "tokens.light.css", DIST_WEB / "tokens.dark.css"]
    for f in css_files:
        if not f.is_file():
            errors.append(f"missing artifact: {f}")
            continue
        text = _read(f)
        if UNRESOLVED_PATTERN.search(text):
            errors.append(f"unresolved placeholder in {f}")

    ts_file = DIST_SHARED / "tokens.ts"
    if not ts_file.is_file():
        errors.append(f"missing artifact: {ts_file}")
    else:
        text = _read(ts_file)
        if UNRESOLVED_PATTERN.search(text):
            errors.append(f"unresolved placeholder in {ts_file}")
    return errors


def verify_variant_keys() -> list[str]:
    errors: list[str] = []
    ts_file = DIST_SHARED / "tokens.ts"
    if not ts_file.is_file():
        return [f"missing artifact: {ts_file}"]

    text = _read(ts_file)
    if "tokenVariants" not in text:
        return ["tokens.ts missing tokenVariants export"]

    required_markers = [
        '"light"',
        '"dark"',
        '"mobile_light"',
        '"mini_light"',
    ]
    for marker in required_markers:
        if marker not in text:
            errors.append(f"tokens.ts missing variant marker: {marker}")
    return errors


def main() -> None:
    errors = []
    errors.extend(verify_no_unresolved_tokens())
    errors.extend(verify_variant_keys())

    if errors:
        print("[design-tokens verify] FAIL")
        for e in errors:
            print("-", e)
        raise SystemExit(1)
    print("[design-tokens verify] PASS")


if __name__ == "__main__":
    main()
