#!/usr/bin/env python3
"""Guard suggestedAction entrypoint usage in frontend.

Rule:
- Direct imports from `app/suggestedAction` are only allowed in:
  - `frontend/apps/web/src/composables/useSuggestedAction.ts`
- Views/components/pages should consume suggested action APIs via composables.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = ROOT / "frontend/apps/web/src"
IMPORT_RE = re.compile(r"import\s+[^;]*?from\s+['\"]([^'\"]+)['\"]")
TARGET = "app/suggestedAction"

ALLOWED = {
    SRC_ROOT / "composables/useSuggestedAction.ts",
}


def main() -> int:
    if not SRC_ROOT.exists():
        print(f"[FAIL] source root missing: {SRC_ROOT}")
        return 1

    violations: list[Path] = []
    for path in SRC_ROOT.rglob("*.ts"):
        text = path.read_text(encoding="utf-8")
        imports = IMPORT_RE.findall(text)
        if not any(TARGET in item for item in imports):
            continue
        if path in ALLOWED:
            continue
        violations.append(path)

    if violations:
        print("[FAIL] suggested_action usage guard")
        for path in sorted(violations):
            print(f"- forbidden direct import in {path.relative_to(ROOT)}")
        print("Use composables/useSuggestedAction.ts instead.")
        return 1

    print("[OK] suggested_action usage guard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
