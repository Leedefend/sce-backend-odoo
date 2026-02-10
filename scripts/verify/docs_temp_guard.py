#!/usr/bin/env python3
"""Block TEMP_* docs under docs/ops/releases/current/."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRENT_DIR = ROOT / "docs/ops/releases/current"


def main() -> int:
    offenders = sorted(p.relative_to(ROOT).as_posix() for p in CURRENT_DIR.rglob("TEMP_*.md") if p.is_file())
    if offenders:
        print("[FAIL] docs temp guard")
        for item in offenders:
            print(f"- forbidden in current/: {item}")
        return 2
    print("[OK] docs temp guard")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
