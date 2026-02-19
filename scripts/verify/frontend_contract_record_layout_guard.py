#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "frontend/apps/web/src/app/contractRecordRuntime.ts"
REQUIRED_TOKENS = [
    "function extractFieldOrder(contract: ActionContract)",
    "const direct = contract.views?.form?.layout || [];",
    "const fallback = Array.isArray(contract.views?.form?.fields)",
    "Object.keys(fields)",
    "const merged = normalizeUniqueFields([...normalized, ...fallback, ...Object.keys(fields)]);",
]


def main() -> int:
    if not TARGET.is_file():
        print("[frontend_contract_record_layout_guard] FAIL")
        print(f"missing target file: {TARGET.relative_to(ROOT).as_posix()}")
        return 1

    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    missing = [token for token in REQUIRED_TOKENS if token not in text]
    if missing:
        print("[frontend_contract_record_layout_guard] FAIL")
        for token in missing:
            print(f"{TARGET.relative_to(ROOT).as_posix()}: missing token `{token}`")
        return 1

    print("[frontend_contract_record_layout_guard] PASS")
    print("scanned_files=1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
