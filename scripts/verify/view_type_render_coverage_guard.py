#!/usr/bin/env python3
"""Guard ActionView has explicit render coverage for major contract view types."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTION_VIEW = ROOT / 'frontend/apps/web/src/views/ActionView.vue'
ACTION_RUNTIME_CONTRACT_SHAPE = (
    ROOT / 'frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts'
)
ACTION_RUNTIME_ADVANCED_DISPLAY = (
    ROOT / 'frontend/apps/web/src/app/action_runtime/useActionViewAdvancedDisplayRuntime.ts'
)
ACTION_RUNTIME_LOAD_VIEW_STATE = (
    ROOT / 'frontend/apps/web/src/app/runtime/actionViewLoadViewFieldStateRuntime.ts'
)


def _read(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding='utf-8')


def main() -> int:
    errors: list[str] = []
    try:
        action_view = _read(ACTION_VIEW)
        action_runtime_contract_shape = _read(ACTION_RUNTIME_CONTRACT_SHAPE)
        action_runtime_advanced_display = _read(ACTION_RUNTIME_ADVANCED_DISPLAY)
        action_runtime_load_view_state = _read(ACTION_RUNTIME_LOAD_VIEW_STATE)
    except FileNotFoundError as exc:
        print('[FAIL] view_type_render_coverage_guard')
        print(f'- {exc}')
        return 1

    marker_specs = [
        (
            'action_view',
            ACTION_VIEW,
            action_view,
            [
                "vm.content.kind === 'kanban'",
                "vm.content.kind === 'list'",
                'class="advanced-view"',
            ],
        ),
        (
            'action_runtime_load_view_state',
            ACTION_RUNTIME_LOAD_VIEW_STATE,
            action_runtime_load_view_state,
            ["if (options.viewMode === 'kanban')", "if (options.viewMode === 'tree')"],
        ),
        (
            'action_runtime_contract_shape',
            ACTION_RUNTIME_CONTRACT_SHAPE,
            action_runtime_contract_shape,
            [
                "if (mode === 'pivot')",
                "if (mode === 'graph')",
                "if (mode === 'calendar' || mode === 'gantt')",
                "if (mode === 'activity')",
                "if (mode === 'dashboard')",
                'function extractAdvancedViewFields(contract: unknown, mode: string) {',
            ],
        ),
        (
            'action_runtime_advanced_display',
            ACTION_RUNTIME_ADVANCED_DISPLAY,
            action_runtime_advanced_display,
            ['const advancedViewTitle = computed(() => {'],
        ),
    ]

    for label, _, content, markers in marker_specs:
        for marker in markers:
            if marker not in content:
                errors.append(f'{label} missing marker: {marker}')

    if errors:
        print('[FAIL] view_type_render_coverage_guard')
        for line in errors:
            print(f'- {line}')
        return 1

    print('[OK] view_type_render_coverage_guard')
    print(f'- action_view: {ACTION_VIEW}')
    print(f'- action_runtime_contract_shape: {ACTION_RUNTIME_CONTRACT_SHAPE}')
    print(f'- action_runtime_advanced_display: {ACTION_RUNTIME_ADVANCED_DISPLAY}')
    print(f'- action_runtime_load_view_state: {ACTION_RUNTIME_LOAD_VIEW_STATE}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
