#!/usr/bin/env python3
"""Guard onchange roundtrip is wired end-to-end (backend handler + frontend consumer)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'addons/smart_core/handlers/api_onchange.py'
FRONTEND_API = ROOT / 'frontend/apps/web/src/api/onchange.ts'
FORM_PAGE = ROOT / 'frontend/apps/web/src/pages/ContractFormPage.vue'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        backend = _read(BACKEND)
        api = _read(FRONTEND_API)
        form = _read(FORM_PAGE)
    except FileNotFoundError as exc:
        print('[FAIL] onchange_roundtrip_guard')
        print(f'- {exc}')
        return 1

    backend_markers = [
        'class ApiOnchangeHandler(BaseIntentHandler):',
        'INTENT_TYPE = "api.onchange"',
        'env_model.onchange(values, changed_fields, field_onchange)',
        '"patch": patch',
        '"modifiers_patch": modifiers_patch',
    ]
    for marker in backend_markers:
        if marker not in backend:
            errors.append(f'backend missing marker: {marker}')

    api_markers = [
        'export async function triggerOnchange(',
        "intent: 'api.onchange'",
        'changed_fields: params.changed_fields',
    ]
    for marker in api_markers:
        if marker not in api:
            errors.append(f'frontend api missing marker: {marker}')

    form_markers = [
        "import { triggerOnchange } from '../api/onchange';",
        'function markFieldChanged(name: string) {',
        'function scheduleOnchange() {',
        'async function runOnchangeRoundtrip() {',
        'const response = await triggerOnchange({',
        'const patch = response?.patch;',
    ]
    for marker in form_markers:
        if marker not in form:
            errors.append(f'form missing marker: {marker}')

    if errors:
        print('[FAIL] onchange_roundtrip_guard')
        for line in errors:
            print(f'- {line}')
        return 1

    print('[OK] onchange_roundtrip_guard')
    print(f'- backend: {BACKEND}')
    print(f'- frontend_api: {FRONTEND_API}')
    print(f'- form: {FORM_PAGE}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
