#!/usr/bin/env python3
"""Guard line_patches path is wired backend -> frontend one2many runtime."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'addons/smart_core/handlers/api_onchange.py'
FORM = ROOT / 'frontend/apps/web/src/pages/ContractFormPage.vue'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        backend = _read(BACKEND)
        form = _read(FORM)
    except FileNotFoundError as exc:
        print('[FAIL] onchange_line_patch_guard')
        print(f'- {exc}')
        return 1

    backend_markers = [
        'def _normalize_line_patches(self, env_model, rows_raw: Any) -> List[Dict[str, Any]]:',
        'line_patches = self._normalize_line_patches(env_model, onchange_result.get("line_patches"))',
        '"line_patches": line_patches,',
    ]
    for marker in backend_markers:
        if marker not in backend:
            errors.append(f'backend missing marker: {marker}')

    form_markers = [
        'const onchangeLinePatches = ref<OnchangeLinePatch[]>([]);',
        'function applyOnchangeLinePatches(linePatches: OnchangeLinePatch[]) {',
        'function one2manyRowHints(fieldName: string, row: One2ManyInlineRow) {',
        'const linePatches = Array.isArray(response?.line_patches) ? response.line_patches : [];',
        'onchangeLinePatches.value = linePatches;',
        'applyOnchangeLinePatches(linePatches);',
    ]
    for marker in form_markers:
        if marker not in form:
            errors.append(f'form missing marker: {marker}')

    if errors:
        print('[FAIL] onchange_line_patch_guard')
        for item in errors:
            print(f'- {item}')
        return 1

    print('[OK] onchange_line_patch_guard')
    print(f'- backend: {BACKEND}')
    print(f'- form: {FORM}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
