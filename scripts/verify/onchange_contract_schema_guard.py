#!/usr/bin/env python3
"""Guard api.onchange returns a stable schema for patch/modifier/line updates."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'addons/smart_core/handlers/api_onchange.py'
FRONTEND = ROOT / 'frontend/apps/web/src/api/onchange.ts'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        backend = _read(BACKEND)
        frontend = _read(FRONTEND)
    except FileNotFoundError as exc:
        print('[FAIL] onchange_contract_schema_guard')
        print(f'- {exc}')
        return 1

    backend_markers = [
        'VERSION = "1.1.0"',
        '"schema_version": "v1"',
        '"line_patches": [],',
        'def _normalize_modifiers_patch(self, env_model, modifiers_raw: Any) -> Dict[str, Dict[str, Any]]:',
        'for marker in ("invisible", "readonly", "required", "domain"):',
        '"meta": {"model": model, "intent": self.INTENT_TYPE, "version": self.VERSION},',
    ]
    for marker in backend_markers:
        if marker not in backend:
            errors.append(f'backend missing marker: {marker}')

    frontend_markers = [
        'schema_version?: string;',
        'line_patches?: Array<Record<string, unknown>>;',
        "intent: 'api.onchange'",
    ]
    for marker in frontend_markers:
        if marker not in frontend:
            errors.append(f'frontend missing marker: {marker}')

    if errors:
        print('[FAIL] onchange_contract_schema_guard')
        for item in errors:
            print(f'- {item}')
        return 1

    print('[OK] onchange_contract_schema_guard')
    print(f'- backend: {BACKEND}')
    print(f'- frontend: {FRONTEND}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
