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
        'from ..utils.reason_codes import normalize_onchange_reason_code',
        '"reason_code": normalize_onchange_reason_code(',
        'def _relation_field_names(self, env_model, field_name: str) -> List[str]:',
        'def _normalize_line_patch_values(self, env_model, field_name: str, patch_raw: Any) -> Dict[str, Any]:',
        'def _normalize_line_patch_modifiers(self, env_model, field_name: str, modifiers_raw: Any) -> Dict[str, Dict[str, Any]]:',
        'row_patch = self._normalize_line_patch_values(env_model, field, item.get("patch"))',
        'row_modifiers = self._normalize_line_patch_modifiers(env_model, field, item.get("modifiers_patch"))',
        'def _normalize_row_state(self, item: Dict[str, Any], row_patch: Dict[str, Any], warnings: List[Dict[str, str]]) -> str:',
        'def _command_hint_for_row_state(self, row_state: str) -> List[int]:',
        '"command_hint": self._command_hint_for_row_state(row_state),',
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
        "messages.push(`原因码: ${reasonCode}`);",
        'const rowState = String(patch.row_state || \'\').trim().toLowerCase();',
        'messages.push(`命令提示: ${patch.command_hint.join(\'/\')}`);',
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
