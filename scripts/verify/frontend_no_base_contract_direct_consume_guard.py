#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_SRC = ROOT / "frontend" / "apps" / "web" / "src"

ALLOWED_MARKERS = {
    "scene_ready_contract_v1",
    "scene_governance_v1",
}

FORBIDDEN_PATTERNS = (
    "ui_base_contract",
    "base_contract",
    "baseContract",
)

SCAN_SUFFIXES = {".ts", ".tsx", ".js", ".vue"}


def _should_scan(path: Path) -> bool:
    return path.suffix in SCAN_SUFFIXES and path.is_file()


def main() -> int:
    if not FRONTEND_SRC.is_dir():
        print("[frontend_no_base_contract_direct_consume_guard] FAIL")
        print(f" - missing frontend source dir: {FRONTEND_SRC}")
        return 1

    violations: list[str] = []
    for file_path in FRONTEND_SRC.rglob("*"):
        if not _should_scan(file_path):
            continue
        text = file_path.read_text(encoding="utf-8")
        for marker in ALLOWED_MARKERS:
            text = text.replace(marker, "")
        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            for token in FORBIDDEN_PATTERNS:
                if token in line:
                    rel = file_path.relative_to(ROOT)
                    violations.append(f"{rel}:{idx}: forbidden direct base-contract token `{token}`")

    if violations:
        print("[frontend_no_base_contract_direct_consume_guard] FAIL")
        for item in violations[:80]:
            print(f" - {item}")
        if len(violations) > 80:
            print(f" - ... and {len(violations) - 80} more")
        return 1

    print("[frontend_no_base_contract_direct_consume_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

