#!/usr/bin/env python3
"""Guard relation read-visibility contract stays closed-loop (backend -> frontend)."""

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
    print("[FAIL] relation_read_closure_guard")
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
        "def _safe_can_read(model_name):",
        'check_access_rights("read", raise_exception=False)',
        '"can_read": _safe_can_read(relation)',
        'reason_code = "RELATION_READ_FORBIDDEN"',
        '"can_read": can_read',
        "def _apply_access_policy(self, data, model_name=\"\"):",
        'mode = "block"',
        'mode = "degrade"',
        'reason_code = "RELATION_READ_FORBIDDEN_CORE"',
        'data["access_policy"] = {',
    ]
    for marker in backend_required:
        if marker not in backend:
            errors.append(f"backend missing marker: {marker}")

    frontend_required = [
        "canRead: row.can_read !== false,",
        "if (entry && entry.canRead === false) {",
        "const contractAccessPolicy = computed<ContractAccessPolicy>(() => {",
        "if (policy.mode === 'block') {",
        "throw new ContractAccessPolicyError(",
    ]
    for marker in frontend_required:
        if marker not in frontend:
            errors.append(f"frontend missing marker: {marker}")

    # Both query paths must enforce relation_entry.can_read guard.
    if frontend.count("if (entry && entry.canRead === false) {") < 2:
        errors.append("frontend missing canRead guard in one of relation query paths")

    # Frontend must not re-introduce hardcoded model-level ACL inference.
    frontend_forbidden = [
        "function canReadRelationModel(",
    ]
    for marker in frontend_forbidden:
        if marker in frontend:
            errors.append(f"frontend contains forbidden hardcoded ACL inference: {marker}")

    if errors:
        return _fail(errors)

    print("[OK] relation_read_closure_guard")
    print(f"- backend: {BACKEND_PATH}")
    print(f"- frontend: {FRONTEND_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
