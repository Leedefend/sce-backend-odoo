#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "frontend/apps/web/src/pages/contractForm/runtimeStateProtocol.ts"
TYPES = ROOT / "frontend/apps/web/src/pages/contractForm/types.ts"
PAGE = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
SAVE_HELPER = ROOT / "frontend/apps/web/src/pages/contractForm/saveRecordHelpers.ts"
ACTION_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/useFormActionRuntime.ts"
PRIMARY_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/usePrimaryFormActionRuntime.ts"
CI = ROOT / "make/ci.mk"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []
    protocol = _read(PROTOCOL)
    types = _read(TYPES)
    page = _read(PAGE)
    save_helper = _read(SAVE_HELPER)
    action_runtime = _read(ACTION_RUNTIME)
    primary_runtime = _read(PRIMARY_RUNTIME)
    ci = _read(CI)

    if not protocol:
        errors.append(f"missing protocol: {PROTOCOL.relative_to(ROOT)}")

    required_protocol_tokens = [
        "export type FormRuntimeStatus = 'loading' | 'ok' | 'error';",
        "export type FormRuntimeBusyKind = 'save' | 'action' | null;",
        "export type FormSubmissionFeedback",
        "export type FormRuntimeStateRefs",
        "export type FormRuntimeTransactionName",
        "export type FormRuntimeStateEvent",
        "export const FORM_RUNTIME_TRANSACTIONS",
        "'saveRecord'",
        "'runAction'",
        "'runOnchangeRoundtrip'",
    ]
    for token in required_protocol_tokens:
        if token not in protocol:
            errors.append(f"runtimeStateProtocol.ts missing token: {token}")

    forbidden_protocol_tokens = [
        "await ",
        "async ",
        "intentRequest",
        "triggerOnchange",
        "executeButton",
        "router.",
        "window.",
        "createContractFormRecord",
        "writeContractFormRecord",
        "queryRelationOptions",
        "reload(",
        ".value =",
    ]
    for token in forbidden_protocol_tokens:
        if token in protocol:
            errors.append(f"runtimeStateProtocol.ts must stay interface-only; forbidden token: {token}")

    required_type_exports = [
        "FormRuntimeBusyKind as BusyKind",
        "FormRuntimeStatus as UiStatus",
        "FormSubmissionFeedback as SubmissionFeedback",
        "FormRuntimeStateRefs",
        "FormRuntimeStateEvent",
    ]
    for token in required_type_exports:
        if token not in types:
            errors.append(f"types.ts missing runtime protocol export: {token}")

    if "type SubmissionFeedback = { kind: 'success' | 'warn' | 'error'; message: string } | null;" in save_helper:
        errors.append("saveRecordHelpers.ts still has local SubmissionFeedback alias")
    if "type SubmissionFeedback = { kind: 'success' | 'warn' | 'error'; message: string } | null;" in action_runtime:
        errors.append("useFormActionRuntime.ts still has local SubmissionFeedback alias")
    if "type SubmissionFeedback = { kind: 'success' | 'warn' | 'error'; message: string } | null;" in primary_runtime:
        errors.append("usePrimaryFormActionRuntime.ts still has local SubmissionFeedback alias")
    if "ref<{ kind: 'success' | 'warn' | 'error'; message: string } | null>(null)" in page:
        errors.append("ContractFormPage.vue still declares submissionFeedback inline")

    required_consumers = [
        (page, "type SubmissionFeedback,", "ContractFormPage.vue"),
        (save_helper, "import type { LayoutNode, SubmissionFeedback } from './types';", "saveRecordHelpers.ts"),
        (action_runtime, "import type { BusyKind, ContractAction, SubmissionFeedback } from './types';", "useFormActionRuntime.ts"),
        (primary_runtime, "import type { BusyKind, ContractAction, SubmissionFeedback } from './types';", "usePrimaryFormActionRuntime.ts"),
    ]
    for source, token, label in required_consumers:
        if token not in source:
            errors.append(f"{label} missing runtime protocol consumer token: {token}")

    ci_token = "python3 scripts/verify/contract_form_runtime_state_protocol_guard.py"
    if ci_token not in ci:
        errors.append("ci.local.quick must run contract_form_runtime_state_protocol_guard.py")

    if errors:
        print("[contract_form_runtime_state_protocol_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_form_runtime_state_protocol_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
