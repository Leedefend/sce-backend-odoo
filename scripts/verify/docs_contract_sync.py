#!/usr/bin/env python3
"""Lightweight docs contract sync guard."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "docs/contract/README.md"
REQUIRED_EXPORTS = [
    "docs/contract/exports/intent_catalog.json",
    "docs/contract/exports/scene_catalog.json",
]


def main() -> int:
    if not README.exists():
        print("[FAIL] docs contract sync")
        print("- missing docs/contract/README.md")
        return 2

    text = README.read_text(encoding="utf-8", errors="ignore")
    errors = []
    for rel in REQUIRED_EXPORTS:
        if rel not in text:
            errors.append(f"README missing link: {rel}")
        if not (ROOT / rel).exists():
            errors.append(f"missing export file: {rel}")

    if errors:
        print("[FAIL] docs contract sync")
        for e in errors:
            print(f"- {e}")
        return 2

    print("[OK] docs contract sync")
    for rel in REQUIRED_EXPORTS:
        print(f"- {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
