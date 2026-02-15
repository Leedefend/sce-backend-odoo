#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import os
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (
    ROOT / "addons",
    ROOT / "frontend",
    ROOT / "scripts",
)
PATTERN = re.compile(r"/api/scenes/my")
ALLOWLIST = {
    "addons/smart_construction_core/controllers/scene_controller.py",
    "addons/smart_construction_core/static/src/config/role_entry_map.js",
    "addons/smart_construction_core/static/src/js/sc_sidebar.js",
    "scripts/e2e/e2e_scene_smoke.py",
    "scripts/verify/marketplace_smoke.py",
    "scripts/verify/scene_admin_smoke.py",
}


def _iter_files():
    allowed_suffix = {".py", ".js", ".ts", ".tsx", ".jsx", ".vue", ".md", ".sh"}
    skip_dirs = {
        ".git",
        ".idea",
        ".vscode",
        "__pycache__",
        "node_modules",
        "dist",
        "artifacts",
        ".pnpm-store",
    }
    for base in SCAN_ROOTS:
        if not base.is_dir():
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            root_path = Path(root)
            for name in files:
                path = root_path / name
                if path.suffix.lower() in allowed_suffix:
                    yield path


def main() -> int:
    hits: set[str] = set()
    violations: list[str] = []

    for path in _iter_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel == "scripts/verify/legacy_scene_endpoint_guard.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PATTERN.search(text):
            hits.add(rel)
            if rel not in ALLOWLIST:
                violations.append(f"{rel}: unexpected /api/scenes/my usage")

    missing_allowlist = sorted(ALLOWLIST - hits)
    if missing_allowlist:
        violations.extend(
            f"{rel}: allowlist entry missing actual usage (clean up allowlist)" for rel in missing_allowlist
        )

    if violations:
        print("[legacy_scene_endpoint_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[legacy_scene_endpoint_guard] PASS")
    print(f"allowlisted_hits={sorted(hits)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
