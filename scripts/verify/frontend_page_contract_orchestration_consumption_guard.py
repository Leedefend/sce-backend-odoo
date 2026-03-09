#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PAGE_CONTRACT_TS = ROOT / "frontend/apps/web/src/app/pageContract.ts"
PAGE_BUILDER = ROOT / "addons/smart_core/core/page_contracts_builder.py"
WORKBENCH_VIEW = ROOT / "frontend/apps/web/src/views/WorkbenchView.vue"


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
    errors: list[str] = []

    if not page_contract_text:
        errors.append(f"missing file: {PAGE_CONTRACT_TS.relative_to(ROOT).as_posix()}")
    if not page_builder_text:
        errors.append(f"missing file: {PAGE_BUILDER.relative_to(ROOT).as_posix()}")
    if not workbench_text:
        errors.append(f"missing file: {WORKBENCH_VIEW.relative_to(ROOT).as_posix()}")
    if errors:
        return _fail(errors)

    _expect(
        page_contract_text,
        "pageContract.ts",
        [
            "contract.value?.page_orchestration_v1?.action_schema",
            "const orchestrationActions = computed<Record<string, unknown>>(() => {",
            "const row = orchestrationActions.value[key];",
            "const label = asText((row as Record<string, unknown>).label);",
            "function actionIntent(key: string, fallback = ''): string {",
            "function actionTarget(key: string): Record<string, unknown> {",
            "actionIntent, actionTarget",
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
        ],
        errors,
    )
    _expect(
        workbench_text,
        "WorkbenchView.vue",
        [
            "const pageActionText = pageContract.actionText;",
            "const pageActionTarget = pageContract.actionTarget;",
            "pageActionText('open_workbench'",
            "const target = pageActionTarget('open_menu');",
            "String(target.kind || '') === 'menu.first_reachable'",
        ],
        errors,
    )

    if errors:
        return _fail(errors)

    print("[frontend_page_contract_orchestration_consumption_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
