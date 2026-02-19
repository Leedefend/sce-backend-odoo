#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    ROOT / "frontend/apps/web/src/views/ActionView.vue",
    ROOT / "frontend/apps/web/src/views/RecordView.vue",
    ROOT / "frontend/apps/web/src/views/MenuView.vue",
    ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue",
    ROOT / "frontend/apps/web/src/components/view/ViewRelationalRenderer.vue",
]
FORBIDDEN = "...route.query"


def main() -> int:
    violations: list[str] = []
    scanned = 0
    for path in TARGETS:
        if not path.is_file():
            violations.append(f"missing target file: {path.relative_to(ROOT).as_posix()}")
            continue
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        if FORBIDDEN in text:
            violations.append(f"{path.relative_to(ROOT).as_posix()}: forbidden token `{FORBIDDEN}`")

    if violations:
        print("[frontend_contract_query_context_guard] FAIL")
        for line in violations:
            print(line)
        return 1

    print("[frontend_contract_query_context_guard] PASS")
    print(f"scanned_files={scanned}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
