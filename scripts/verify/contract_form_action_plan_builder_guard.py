#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "frontend/apps/web/src/pages/contractForm/actionExecutionPlan.ts"
RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/useFormActionRuntime.ts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"export function {re.escape(name)}\([^)]*\): [^{{]+ \{{", source)
    if not match:
        return ""
    start = match.end()
    depth = 1
    index = start
    while index < len(source):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:index]
        index += 1
    return ""


def main() -> int:
    errors: list[str] = []
    plan = _read(PLAN)
    runtime = _read(RUNTIME)
    if not plan:
      errors.append(f"missing plan helper: {PLAN.relative_to(ROOT)}")
    if not runtime:
      errors.append(f"missing runtime: {RUNTIME.relative_to(ROOT)}")

    required_plan_tokens = [
        "export type FormActionExecutionPlan",
        "export function buildFormActionExecutionPlan",
        "kind: 'local_mode'",
        "kind: 'save'",
        "kind: 'cancel'",
        "kind: 'open_action'",
        "kind: 'open_url'",
        "kind: 'scene_mutation'",
        "kind: 'record_button'",
        "kind: 'unsupported'",
    ]
    for token in required_plan_tokens:
        if token not in plan:
            errors.append(f"actionExecutionPlan.ts missing token: {token}")

    body = _function_body(plan, "buildFormActionExecutionPlan")
    if not body:
        errors.append("buildFormActionExecutionPlan body not found")
    else:
        forbidden_tokens = [
            "await ",
            "async ",
            "router.",
            "window.",
            "executeButton",
            "executeSceneMutation",
            "saveRecord",
            "busyKind",
            "submissionFeedback",
            "errorMessage",
            "status.value",
            ".value =",
        ]
        for token in forbidden_tokens:
            if token in body:
                errors.append(f"buildFormActionExecutionPlan must stay pure; forbidden token: {token}")

    required_runtime_tokens = [
        "import { buildFormActionExecutionPlan } from './actionExecutionPlan';",
        "const plan = buildFormActionExecutionPlan({",
        "if (plan.kind === 'local_mode')",
        "if (plan.kind === 'save')",
        "if (plan.kind === 'record_button')",
    ]
    for token in required_runtime_tokens:
        if token not in runtime:
            errors.append(f"useFormActionRuntime.ts missing token: {token}")

    stale_runtime_tokens = [
        "const actionKey = String(action.key || '').trim().toLowerCase();",
        "action.intent === 'ui.local_mode'",
        "actionKey === 'submit_intake'",
        "action.kind === 'open'",
    ]
    for token in stale_runtime_tokens:
        if token in runtime:
            errors.append(f"useFormActionRuntime.ts still owns classification token: {token}")

    if errors:
        print("[contract_form_action_plan_builder_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_form_action_plan_builder_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
