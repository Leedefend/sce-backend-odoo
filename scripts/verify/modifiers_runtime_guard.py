#!/usr/bin/env python3
"""Guard modifier runtime wiring remains contract-driven and active in form engine."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / 'frontend/apps/web/src/app/modifierEngine.ts'
FORM_PAGE = ROOT / 'frontend/apps/web/src/pages/ContractFormPage.vue'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        engine = _read(ENGINE)
        form = _read(FORM_PAGE)
    except FileNotFoundError as exc:
        print('[FAIL] modifiers_runtime_guard')
        print(f'- {exc}')
        return 1

    engine_markers = [
        'export function buildRuntimeFieldStates(',
        "if (head === '|')",
        "if (head === '&')",
        "if (head === '!')",
        'invisible: evalModifierBucket(',
        'readonly: evalModifierBucket(',
        'required: evalModifierBucket(',
    ]
    for marker in engine_markers:
        if marker not in engine:
            errors.append(f'engine missing marker: {marker}')

    form_markers = [
        "import { buildRuntimeFieldStates } from '../app/modifierEngine';",
        'const runtimeFieldStates = computed(() => {',
        'function runtimeState(name: string) {',
        'if (state.invisible) return false;',
        'state.readonly',
        'state.required',
    ]
    for marker in form_markers:
        if marker not in form:
            errors.append(f'form missing marker: {marker}')

    if errors:
        print('[FAIL] modifiers_runtime_guard')
        for line in errors:
            print(f'- {line}')
        return 1

    print('[OK] modifiers_runtime_guard')
    print(f'- engine: {ENGINE}')
    print(f'- form: {FORM_PAGE}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
