#!/usr/bin/env python3
"""Guard backend/normalizer keep semantic support for advanced view types."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_CONTRACT = ROOT / 'addons/smart_core/handlers/ui_contract.py'
NORMALIZER = ROOT / 'addons/smart_core/app_config_engine/services/normalizer.py'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def _check_markers(text: str, markers: list[str], errors: list[str], label: str) -> None:
    for marker in markers:
        if marker not in text:
            errors.append(f'{label} missing marker: {marker}')


def main() -> int:
    errors: list[str] = []
    try:
        ui_text = _read(UI_CONTRACT)
        normalizer_text = _read(NORMALIZER)
    except FileNotFoundError as exc:
        print('[FAIL] view_type_contract_semantic_guard')
        print(f'- {exc}')
        return 1

    _check_markers(
        ui_text,
        [
            'VALID_VIEWS = {',
            '"pivot"',
            '"graph"',
            '"calendar"',
            '"gantt"',
            '"activity"',
            '"dashboard"',
        ],
        errors,
        'ui_contract',
    )
    _check_markers(
        normalizer_text,
        [
            'for vt in ["tree", "form", "kanban", "pivot", "graph", "calendar", "gantt", "activity", "dashboard"]:',
            'elif vt == "activity":',
            'cfg["field"] = _safe_str(cfg.get("field"), "res_id")',
            'elif vt == "dashboard":',
            'cfg["cards"] = _coerce_list(cfg["cards"], "views.dashboard.cards", warns)',
        ],
        errors,
        'normalizer',
    )

    if errors:
        print('[FAIL] view_type_contract_semantic_guard')
        for line in errors:
            print(f'- {line}')
        return 1

    print('[OK] view_type_contract_semantic_guard')
    print(f'- ui_contract: {UI_CONTRACT}')
    print(f'- normalizer: {NORMALIZER}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
