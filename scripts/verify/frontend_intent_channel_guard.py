#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
WEB_SRC = ROOT / "frontend/apps/web/src"
ALLOWLIST = {"/api/v1/intent"}
API_PATH_RE = re.compile(r"['\"](/api/[a-zA-Z0-9_./-]+)['\"]")


def _iter_files():
    if not WEB_SRC.is_dir():
        return
    for ext in ("*.ts", "*.tsx", "*.js", "*.jsx", "*.vue"):
        for path in WEB_SRC.rglob(ext):
            yield path


def main() -> int:
    violations: list[str] = []
    found_paths: set[str] = set()

    for path in _iter_files():
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in API_PATH_RE.finditer(text):
            api_path = str(match.group(1) or "").strip()
            if not api_path:
                continue
            found_paths.add(api_path)
            if api_path not in ALLOWLIST:
                violations.append(f"{rel}: forbidden api path in web app source: {api_path}")

    if violations:
        print("[frontend_intent_channel_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[frontend_intent_channel_guard] PASS")
    print(f"allowed_paths={sorted(found_paths) if found_paths else []}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
