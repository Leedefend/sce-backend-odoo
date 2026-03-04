#!/usr/bin/env python3
"""Guard x2many command semantic layer stays wired in the form runtime."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE = ROOT / 'frontend/apps/web/src/app/x2manyCommands.ts'
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
        print('[FAIL] x2many_command_semantic_guard')
        print(f'- {exc}')
        return 1

    engine_markers = [
        'export type X2ManyCommand = [number, number, unknown?];',
        'export function extractX2ManyIds(value: unknown): number[] {',
        'export function buildX2ManyCommands(params: {',
        "mode: 'onchange' | 'write';",
        'return diffCommands(kind, currentIds, originalIds);',
    ]
    for marker in engine_markers:
        if marker not in engine:
            errors.append(f'engine missing marker: {marker}')

    form_markers = [
        "from '../app/x2manyCommands';",
        'buildX2ManyCommands',
        'extractX2ManyIds',
        'return extractX2ManyIds(value);',
        'mode: \'onchange\'',
        'mode: \'write\'',
    ]
    for marker in form_markers:
        if marker not in form:
            errors.append(f'form missing marker: {marker}')

    if errors:
        print('[FAIL] x2many_command_semantic_guard')
        for line in errors:
            print(f'- {line}')
        return 1

    print('[OK] x2many_command_semantic_guard')
    print(f'- engine: {ENGINE}')
    print(f'- form: {FORM_PAGE}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
