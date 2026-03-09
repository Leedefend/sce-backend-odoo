#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PAGE_CONTRACT_TS = ROOT / "frontend/apps/web/src/app/pageContract.ts"
PAGE_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
WORKBENCH_VIEW = ROOT / "frontend/apps/web/src/views/WorkbenchView.vue"
SCENE_HEALTH_VIEW = ROOT / "frontend/apps/web/src/views/SceneHealthView.vue"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _fail(errors: list[str]) -> int:
    print("[frontend_page_contract_orchestration_consumption_guard] FAIL")
    for err in errors:
        print(f"- {err}")
    return 1


def _expect(text: str, scope: str, tokens: list[str], errors: list[str]) -> None:
    for token in tokens:
        if token not in text:
            errors.append(f"{scope} missing token: {token}")


def main() -> int:
    page_contract_text = _read(PAGE_CONTRACT_TS)
    page_builder_text = _read(PAGE_BUILDER)
    workbench_text = _read(WORKBENCH_VIEW)
    scene_health_text = _read(SCENE_HEALTH_VIEW)
    errors: list[str] = []

    if not page_contract_text:
        errors.append(f"missing file: {PAGE_CONTRACT_TS.relative_to(ROOT).as_posix()}")
    if not page_builder_text:
        errors.append(f"missing file: {PAGE_BUILDER.relative_to(ROOT).as_posix()}")
    if not workbench_text:
        errors.append(f"missing file: {WORKBENCH_VIEW.relative_to(ROOT).as_posix()}")
    if not scene_health_text:
        errors.append(f"missing file: {SCENE_HEALTH_VIEW.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    _expect(
        page_contract_text,
        "pageContract.ts",
        [
            "contract.value?.page_orchestration_v1?.action_schema",
            "const globalActions = computed<GlobalActionConfig[]>(() => {",
            "(page as Record<string, unknown>).global_actions",
            "const orchestrationActions = computed<Record<string, unknown>>(() => {",
            "const row = orchestrationActions.value[key];",
            "const label = asText((row as Record<string, unknown>).label);",
            "function actionIntent(key: string, fallback = ''): string {",
            "function actionTarget(key: string): Record<string, unknown> {",
            "actionIntent, actionTarget, globalActions",
        ],
        errors,
    )
    _expect(
        page_builder_text,
        "page_contracts_builder.py",
        [
            '"action_schema": {"actions": action_schema_actions},',
            '"actions": _action_templates(section_key),',
            "def _default_page_actions(page_key: str) -> list[Dict[str, Any]]:",
            '{"key": "open_workbench", "label": "返回工作台", "intent": "ui.contract"}',
            'if key in {"scene_health", "usage_analytics"}:',
        ],
        errors,
    )
    _expect(
        workbench_text,
        "WorkbenchView.vue",
        [
            "const pageActionText = pageContract.actionText;",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => {",
            "v-for=\"action in headerActions\"",
            "@click=\"executeWorkbenchAction(action.key)\"",
            "async function executeWorkbenchAction(actionKey: string) {",
            "const intent = pageActionIntent(actionKey, 'ui.contract');",
            "const target = pageActionTarget(actionKey);",
            "const kind = String(target.kind || '');",
            "if (kind === 'menu.first_reachable') {",
        ],
        errors,
    )
    _expect(
        scene_health_text,
        "SceneHealthView.vue",
        [
            "const pageActionText = pageContract.actionText;",
            "const pageActionIntent = pageContract.actionIntent;",
            "const pageActionTarget = pageContract.actionTarget;",
            "const pageGlobalActions = pageContract.globalActions;",
            "const headerActions = computed(() => {",
            "v-for=\"action in headerActions\"",
            "@click=\"executeHeaderAction(action.key)\"",
            "async function executeHeaderAction(actionKey: string) {",
            "const target = pageActionTarget(actionKey);",
            "if (kind === 'page.refresh' || actionKey === 'refresh_page') {",
        ],
        errors,
    )

    if errors:
        return _fail(errors)

    print("[frontend_page_contract_orchestration_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
