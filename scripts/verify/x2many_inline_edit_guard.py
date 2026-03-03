#!/usr/bin/env python3
"""Guard one2many inline edit wiring remains active in ContractFormPage."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORM_PAGE = ROOT / 'frontend/apps/web/src/pages/ContractFormPage.vue'
ENGINE = ROOT / 'frontend/apps/web/src/app/x2manyCommands.ts'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        form = _read(FORM_PAGE)
        engine = _read(ENGINE)
    except FileNotFoundError as exc:
        print('[FAIL] x2many_inline_edit_guard')
        print(f'- {exc}')
        return 1

    engine_markers = [
        'export function buildOne2ManyInlineCommands(params: {',
        "mode: 'onchange' | 'write';",
        'commands.push([0, 0, values]);',
        'commands.push([1, id, values]);',
        'commands.push([2, id]);',
    ]
    for marker in engine_markers:
        if marker not in engine:
            errors.append(f'engine missing marker: {marker}')

    form_markers = [
        "v-else-if=\"fieldType(node.descriptor) === 'one2many'\"",
        'function one2manyColumns(name: string): One2ManyColumn[] {',
        'function addOne2manyRow(name: string) {',
        'function setOne2manyRowField(fieldName: string, rowKey: string, columnName: string, value: string) {',
        'function removeOne2manyRow(fieldName: string, rowKey: string) {',
        'function restoreOne2manyRow(fieldName: string, rowKey: string) {',
        'function one2manyRowLabel(fieldName: string, row: One2ManyInlineRow) {',
        'function collectOne2manyDraftErrors() {',
        "return buildOne2manyCommandValue(name, 'write');",
        "out[name] = buildOne2manyCommandValue(name, 'onchange');",
    ]
    for marker in form_markers:
        if marker not in form:
            errors.append(f'form missing marker: {marker}')

    if errors:
        print('[FAIL] x2many_inline_edit_guard')
        for line in errors:
            print(f'- {line}')
        return 1

    print('[OK] x2many_inline_edit_guard')
    print(f'- form: {FORM_PAGE}')
    print(f'- engine: {ENGINE}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
