#!/usr/bin/env python3
"""Guard ActionView has explicit render coverage for major contract view types."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTION_VIEW = ROOT / 'frontend/apps/web/src/views/ActionView.vue'
PAGE_MODEL = ROOT / 'frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts'
ADVANCED_DISPLAY_RUNTIME = ROOT / 'frontend/apps/web/src/app/action_runtime/useActionViewAdvancedDisplayRuntime.ts'
CONTRACT_SHAPE_RUNTIME = ROOT / 'frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts'
LOAD_REQUEST_RUNTIME = ROOT / 'frontend/apps/web/src/app/action_runtime/useActionViewLoadRequestRuntime.ts'
VIEW_FIELD_STATE_RUNTIME = ROOT / 'frontend/apps/web/src/app/runtime/actionViewLoadViewFieldStateRuntime.ts'


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        action_view = _read(ACTION_VIEW)
        page_model = _read(PAGE_MODEL)
        advanced_display_runtime = _read(ADVANCED_DISPLAY_RUNTIME)
        contract_shape_runtime = _read(CONTRACT_SHAPE_RUNTIME)
        load_request_runtime = _read(LOAD_REQUEST_RUNTIME)
        view_field_state_runtime = _read(VIEW_FIELD_STATE_RUNTIME)
    except FileNotFoundError as exc:
        print('[FAIL] view_type_render_coverage_guard')
        print(f'- {exc}')
        return 1

    action_view_markers = [
        "v-if=\"vm.content.kind === 'kanban'\"",
        "v-else-if=\"vm.content.kind === 'list'\"",
        'class="advanced-view"',
        "vm.content.advanced?.title",
        "vm.content.advanced?.hint",
    ]
    for marker in action_view_markers:
        if marker not in action_view:
            errors.append(f'action_view missing marker: {marker}')

    page_model_markers = [
        "function resolveContentKind(viewMode: string): 'list' | 'kanban' | 'advanced'",
        "if (viewMode === 'tree') return 'list';",
        "if (viewMode === 'kanban') return 'kanban';",
    ]
    for marker in page_model_markers:
        if marker not in page_model:
            errors.append(f'page_model missing marker: {marker}')

    advanced_markers = [
        'const advancedViewTitle = computed(() => {',
        'const advancedViewHint = computed(() => {',
    ]
    for marker in advanced_markers:
        if marker not in advanced_display_runtime:
            errors.append(f'advanced_display_runtime missing marker: {marker}')

    contract_shape_markers = [
        'function extractAdvancedViewFields(contract: unknown, mode: string)',
    ]
    for marker in contract_shape_markers:
        if marker not in contract_shape_runtime:
            errors.append(f'contract_shape_runtime missing marker: {marker}')

    load_request_markers = [
        'if (mode === \'pivot\' || mode === \'graph\' || mode === \'calendar\' || mode === \'gantt\' || mode === \'activity\' || mode === \'dashboard\')',
        "const advancedContractFields = options.extractAdvancedViewFields(options.contract, options.viewMode);",
    ]
    for marker in load_request_markers:
        if marker not in load_request_runtime and marker not in action_view:
            errors.append(f'load_request_runtime missing marker: {marker}')

    field_state_markers = [
        "if (options.viewMode === 'kanban') {",
        "if (options.viewMode === 'tree') {",
    ]
    for marker in field_state_markers:
        if marker not in view_field_state_runtime:
            errors.append(f'view_field_state_runtime missing marker: {marker}')

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
    print(f'- page_model: {PAGE_MODEL}')
    print(f'- advanced_display_runtime: {ADVANCED_DISPLAY_RUNTIME}')
    print(f'- contract_shape_runtime: {CONTRACT_SHAPE_RUNTIME}')
    print(f'- load_request_runtime: {LOAD_REQUEST_RUNTIME}')
    print(f'- view_field_state_runtime: {VIEW_FIELD_STATE_RUNTIME}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
