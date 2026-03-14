#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
LOCATOR = ROOT / "addons/smart_scene/core/provider_locator.py"
SCAN_PATHS = [ROOT / "addons"]


def _fail(errors: list[str]) -> int:
    print("[verify.scene.provider_locator.removed.guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _scan_references() -> list[str]:
    errors: list[str] = []
    for base in SCAN_PATHS:
        for path in base.rglob("*.py"):
            if path.resolve() == LOCATOR.resolve():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if "provider_locator.py" in text:
                errors.append(f"forbidden provider_locator reference: {path.relative_to(ROOT).as_posix()}")
    return errors


def main() -> int:
    errors: list[str] = []
    if LOCATOR.exists():
        errors.append(f"provider_locator must be removed: {LOCATOR.relative_to(ROOT).as_posix()}")
    errors.extend(_scan_references())
    if errors:
        return _fail(errors)
    print("[verify.scene.provider_locator.removed.guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
