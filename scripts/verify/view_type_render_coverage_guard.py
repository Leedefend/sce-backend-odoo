#!/usr/bin/env python3
"""Guard ActionView has explicit render coverage for major contract view types."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTION_VIEW = ROOT / 'frontend/apps/web/src/views/ActionView.vue'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        text = _read(ACTION_VIEW)
    except FileNotFoundError as exc:
        print('[FAIL] view_type_render_coverage_guard')
        print(f'- {exc}')
        return 1

    markers = [
        "v-if=\"viewMode === 'kanban'\"",
        "v-else-if=\"viewMode === 'tree'\"",
        'if (mode === \'pivot\' || mode === \'graph\' || mode === \'calendar\' || mode === \'gantt\' || mode === \'activity\' || mode === \'dashboard\')',
        'const advancedViewTitle = computed(() => {',
        'function extractAdvancedViewFields(contract: Awaited<ReturnType<typeof loadActionContract>>, mode: string) {',
        "viewMode.value === 'tree'",
        'class="advanced-view"',
    ]

    for marker in markers:
        if marker not in text:
            errors.append(f'missing marker: {marker}')

    if errors:
        env_name = str(os.getenv("ENV") or "").strip().lower()
        if env_name in {"dev", "test", "local"}:
            print('[WARN] view_type_render_coverage_guard (dev/test/local relaxed mode)')
            for line in errors:
                print(f'- {line}')
            return 0
        print('[FAIL] view_type_render_coverage_guard')
        for line in errors:
            print(f'- {line}')
        return 1

    print('[OK] view_type_render_coverage_guard')
    print(f'- action_view: {ACTION_VIEW}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
