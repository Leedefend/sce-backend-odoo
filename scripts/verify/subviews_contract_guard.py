#!/usr/bin/env python3
"""Guard backend emits/normalizes structured form subviews contract for x2many."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_VIEW = ROOT / 'addons/smart_core/app_config_engine/models/app_view_config.py'
NORMALIZER = ROOT / 'addons/smart_core/app_config_engine/services/normalizer.py'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        app_view = _read(APP_VIEW)
        normalizer = _read(NORMALIZER)
    except FileNotFoundError as exc:
        print('[FAIL] subviews_contract_guard')
        print(f'- {exc}')
        return 1

    app_markers = [
        'def _infer_x2many_subviews(fields_meta):',
        "'tree': {'columns': _infer_tree_columns(meta, rel_fields)},",
        "'fields': rel_fields,",
        "'policies': {'inline_edit': True, 'can_create': True, 'can_unlink': True},",
    ]
    for marker in app_markers:
        if marker not in app_view:
            errors.append(f'app_view_config missing marker: {marker}')

    normalizer_markers = [
        'cfg.setdefault("subviews", {})',
        'views.form.subviews',
        'views.form.subviews.{key}.tree.columns',
        'normalized_columns.append({',
        '"ttype": _safe_str(col_obj.get("ttype", "char"), "char")',
    ]
    for marker in normalizer_markers:
        if marker not in normalizer:
            errors.append(f'normalizer missing marker: {marker}')

    if errors:
        print('[FAIL] subviews_contract_guard')
        for line in errors:
            print(f'- {line}')
        return 1

    print('[OK] subviews_contract_guard')
    print(f'- app_view: {APP_VIEW}')
    print(f'- normalizer: {NORMALIZER}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
