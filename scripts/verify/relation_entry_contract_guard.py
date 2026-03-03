#!/usr/bin/env python3
"""Guard relation-entry contract path remains backend-driven and frontend-consumed."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = ROOT / "addons/smart_core/app_config_engine/services/assemblers/page_assembler.py"
FRONTEND_PATH = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def _fail(lines: list[str]) -> int:
    print("[FAIL] relation_entry contract guard")
    for line in lines:
        print(f"- {line}")
    return 1


def main() -> int:
    try:
        backend = _read(BACKEND_PATH)
        frontend = _read(FRONTEND_PATH)
    except FileNotFoundError as exc:
        return _fail([str(exc)])

    errors: list[str] = []

    backend_required = [
        "def _build_relation_entry_for_field(",
        "def _extract_dictionary_type_from_domain(",
        '"create_mode": create_mode',
        '"default_vals": default_vals',
        '"reason_code": reason_code',
    ]
    for marker in backend_required:
        if marker not in backend:
            errors.append(f"backend missing marker: {marker}")

    frontend_required = [
        "const createModeRaw = String(row.create_mode || '').trim().toLowerCase();",
        "const defaultVals = row.default_vals",
        "function relationCreateMode(",
        "function relationDomain(",
        "function normalizeRouteDefault(value: unknown)",
        "if (key.startsWith('default_')) {",
        "relationCreateMode(node.name, node.descriptor) === 'page' ? '+ 新建并维护...' : '+ 快速新建...'",
        "acc[`default_${key}`] = value;",
    ]
    for marker in frontend_required:
        if marker not in frontend:
            errors.append(f"frontend missing marker: {marker}")

    frontend_forbidden = [
        "function inferDictionaryType(",
        "findActionNodeByModel(",
    ]
    for marker in frontend_forbidden:
        if marker in frontend:
            errors.append(f"frontend still contains forbidden inference marker: {marker}")

    if errors:
        return _fail(errors)

    print("[OK] relation_entry contract guard")
    print(f"- backend: {BACKEND_PATH}")
    print(f"- frontend: {FRONTEND_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
