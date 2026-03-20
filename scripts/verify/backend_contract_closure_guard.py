#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]

CHECKS: list[tuple[Path, list[str]]] = [
    (
        ROOT / "addons" / "smart_core" / "handlers" / "system_init.py",
        [
            "_build_minimal_intent_surface",
            '"intent_catalog_ref"',
            '"meta.intent_catalog"',
        ],
    ),
    (
        ROOT / "addons" / "smart_core" / "handlers" / "meta_intent_catalog.py",
        [
            '"intent_catalog"',
            "collect_catalog",
        ],
    ),
    (
        ROOT / "addons" / "smart_core" / "utils" / "contract_governance.py",
        [
            '"delivery_level"',
            '"target_scene_key"',
            '"entry_kind"',
        ],
    ),
    (
        ROOT / "addons" / "smart_core" / "core" / "scene_governance_payload_builder.py",
        [
            '"surface_mapping"',
            '"scene_metrics"',
            '"scene_registry_count"',
        ],
    ),
    (
        ROOT / "addons" / "smart_core" / "core" / "workspace_home_contract_builder.py",
        [
            '"blocks"',
            '"type": "hero"',
            '"type": "metric"',
            '"type": "risk"',
            '"type": "ops"',
        ],
    ),
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    for path, tokens in CHECKS:
        if not path.exists():
            errors.append(f"missing file: {path}")
            continue
        text = _read(path)
        for token in tokens:
            if token not in text:
                errors.append(f"{path.relative_to(ROOT)} missing token: {token}")

    if errors:
        for row in errors:
            print(f"[backend_contract_closure_guard] {row}")
        print("[backend_contract_closure_guard] FAIL")
        return 2

    print("[backend_contract_closure_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

