#!/usr/bin/env python3
"""Enforce suggested_action import boundary.

Only the following files may import from `app/suggested_action/*` directly:
- `frontend/apps/web/src/app/suggestedAction.ts`
- files under `frontend/apps/web/src/app/suggested_action/`

All other callers must import from `app/suggestedAction` compatibility entrypoint.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "frontend/apps/web/src"
ENTRYPOINT = SRC_ROOT / "app/suggestedAction.ts"
INTERNAL_ROOT = SRC_ROOT / "app/suggested_action"
IMPORT_RE = re.compile(r"import\s+[^;]*?from\s+['\"]([^'\"]+)['\"]")


def _is_allowed_importer(file_path: Path) -> bool:
    if file_path == ENTRYPOINT:
        return True
    try:
        file_path.relative_to(INTERNAL_ROOT)
        return True
    except ValueError:
        return False


def main() -> int:
    if not SRC_ROOT.exists():
        print(f"[FAIL] missing source root: {SRC_ROOT}")
        return 1

    violations: list[tuple[Path, str]] = []

    for file_path in SRC_ROOT.rglob("*"):
        if file_path.suffix not in {".ts", ".vue"}:
            continue
        text = file_path.read_text(encoding="utf-8")
        for import_path in IMPORT_RE.findall(text):
            if "suggested_action/" not in import_path:
                continue
            if _is_allowed_importer(file_path):
                continue
            violations.append((file_path, import_path))

    if violations:
        print("[FAIL] suggested_action import boundary guard")
        for file_path, import_path in violations:
            rel = file_path.relative_to(ROOT)
            print(f"- {rel}: forbidden direct import -> {import_path}")
        print("Use app/suggestedAction entrypoint instead.")
        return 1

    print("[OK] suggested_action import boundary guard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
