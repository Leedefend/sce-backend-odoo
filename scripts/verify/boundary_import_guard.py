#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]

# key: source module root, value: forbidden addon module names
POLICY = {
    "addons/smart_core": {
        "smart_construction_portal",
        "smart_construction_demo",
        "smart_construction_seed",
        "smart_construction_custom",
    },
    "addons/smart_construction_core": {
        "smart_construction_portal",
        "smart_construction_demo",
        "smart_construction_seed",
        "smart_construction_custom",
    },
    "addons/smart_construction_scene": {
        "smart_construction_portal",
        "smart_construction_demo",
        "smart_construction_seed",
        "smart_construction_custom",
    },
}

IMPORT_RE = re.compile(
    r"(?:from\s+odoo\.addons\.(?P<from_mod>[a-zA-Z0-9_]+)\s+import)"
    r"|(?:import\s+odoo\.addons\.(?P<import_mod>[a-zA-Z0-9_]+))"
)


def _iter_py_files(base: Path):
    for path in base.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if "/tests/" in rel or "/docs/" in rel or "/migrations/" in rel:
            continue
        yield path


def main() -> int:
    violations: list[str] = []
    for src_root, forbidden in POLICY.items():
        base = ROOT / src_root
        if not base.is_dir():
            continue
        for file_path in _iter_py_files(base):
            rel = file_path.relative_to(ROOT).as_posix()
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            for m in IMPORT_RE.finditer(text):
                mod = m.group("from_mod") or m.group("import_mod")
                if mod in forbidden:
                    violations.append(f"{rel}: forbidden import -> odoo.addons.{mod}")

    if violations:
        print("[boundary_import_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[boundary_import_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
