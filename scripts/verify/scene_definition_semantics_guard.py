#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
SCAN_FILES = (
    ROOT / "addons/smart_construction_scene/scene_registry.py",
    *sorted((ROOT / "addons/smart_construction_scene/data").glob("*.xml")),
)

# Scene definitions are declarative shape/config only. Runtime availability/reason
# must be computed in capability/governance layer.
FORBIDDEN_PATTERNS = (
    re.compile(r"['\"]available['\"]\s*:"),
    re.compile(r"['\"]reason['\"]\s*:"),
)


def main() -> int:
    violations: list[str] = []
    for path in SCAN_FILES:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        lines = text.splitlines()
        for pattern in FORBIDDEN_PATTERNS:
            for idx, line in enumerate(lines, start=1):
                if pattern.search(line):
                    violations.append(f"{rel}:{idx}: forbidden scene-definition semantic key: {pattern.pattern}")

    if violations:
        print("[scene_definition_semantics_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[scene_definition_semantics_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
