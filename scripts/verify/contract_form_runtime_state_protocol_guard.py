#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "frontend/apps/web/src/pages/contractForm/runtimeStateProtocol.ts"
REDUCER = ROOT / "frontend/apps/web/src/pages/contractForm/runtimeStateReducer.ts"
APPLIER = ROOT / "frontend/apps/web/src/pages/contractForm/runtimeStateApplier.ts"
TYPES = ROOT / "frontend/apps/web/src/pages/contractForm/types.ts"
PAGE = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
SAVE_HELPER = ROOT / "frontend/apps/web/src/pages/contractForm/saveRecordHelpers.ts"
ACTION_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/useFormActionRuntime.ts"
PRIMARY_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/usePrimaryFormActionRuntime.ts"
FORM_CONFIG_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/useFormConfigSaveRuntime.ts"
INLINE_POLICY_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/useInlineFieldPolicyRuntime.ts"
CONTRACT_MODE_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/useContractModeActionRuntime.ts"
CI = ROOT / "make/ci.mk"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def main() -> int:
    errors: list[str] = []
    protocol = _read(PROTOCOL)
    reducer = _read(REDUCER)
    applier = _read(APPLIER)
    types = _read(TYPES)
    page = _read(PAGE)
    save_helper = _read(SAVE_HELPER)
    action_runtime = _read(ACTION_RUNTIME)
    primary_runtime = _read(PRIMARY_RUNTIME)
    form_config_runtime = _read(FORM_CONFIG_RUNTIME)
    inline_policy_runtime = _read(INLINE_POLICY_RUNTIME)
    contract_mode_runtime = _read(CONTRACT_MODE_RUNTIME)
    ci = _read(CI)

    if not protocol:
        errors.append(f"missing protocol: {PROTOCOL.relative_to(ROOT)}")
    if not reducer:
        errors.append(f"missing reducer: {REDUCER.relative_to(ROOT)}")
    if not applier:
        errors.append(f"missing applier: {APPLIER.relative_to(ROOT)}")

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
        "'formReload'",
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

    required_reducer_tokens = [
        "export type FormRuntimeStateSnapshot",
        "export const INITIAL_FORM_RUNTIME_STATE",
        "export function reduceFormRuntimeState",
        "export function reduceFormRuntimeStateEvents",
        "event.kind === 'begin'",
        "event.kind === 'end'",
        "event.kind === 'status'",
        "event.kind === 'validation'",
        "event.kind === 'feedback'",
    ]
    for token in required_reducer_tokens:
        if token not in reducer:
            errors.append(f"runtimeStateReducer.ts missing token: {token}")

    forbidden_reducer_tokens = [
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
    for token in forbidden_reducer_tokens:
        if token in reducer:
            errors.append(f"runtimeStateReducer.ts must stay pure; forbidden token: {token}")

    required_applier_tokens = [
        "export function applyFormRuntimeStatusEvent",
        "export function applyFormRuntimeBusyEvent",
        "type FormRuntimeStatusEvent = Extract<FormRuntimeStateEvent, { kind: 'status' }>",
        "type FormRuntimeBusyEvent = Extract<FormRuntimeStateEvent, { kind: 'begin' } | { kind: 'end' }>",
        "FormRuntimeStatusRefs",
        "FormRuntimeBusyRefs",
        "INITIAL_FORM_RUNTIME_STATE",
        "reduceFormRuntimeState",
        "status: refs.status.value",
        "errorMessage: refs.errorMessage.value",
        "busyKind: refs.busyKind.value",
        "refs.status.value = next.status",
        "refs.errorMessage.value = next.errorMessage",
        "refs.busyKind.value = next.busyKind",
    ]
    for token in required_applier_tokens:
        if token not in applier:
            errors.append(f"runtimeStateApplier.ts missing token: {token}")

    forbidden_applier_tokens = [
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
        "submissionFeedback.value",
        "validationErrors.value",
        "showOne2manyErrors.value",
    ]
    for token in forbidden_applier_tokens:
        if token in applier:
            errors.append(f"runtimeStateApplier.ts must stay event-only; forbidden token: {token}")

    required_type_exports = [
        "FormRuntimeBusyKind as BusyKind",
        "FormRuntimeStatus as UiStatus",
        "FormSubmissionFeedback as SubmissionFeedback",
        "FormRuntimeStateRefs",
        "FormRuntimeStateEvent",
        "FormRuntimeStateSnapshot",
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
        (page, "import { applyFormRuntimeStatusEvent } from './contractForm/runtimeStateApplier';", "ContractFormPage.vue"),
        (save_helper, "import type { LayoutNode, SubmissionFeedback } from './types';", "saveRecordHelpers.ts"),
        (action_runtime, "import { applyFormRuntimeStatusEvent } from './runtimeStateApplier';", "useFormActionRuntime.ts"),
        (action_runtime, "import type { BusyKind, ContractAction, SubmissionFeedback, UiStatus } from './types';", "useFormActionRuntime.ts"),
        (primary_runtime, "import { applyFormRuntimeStatusEvent } from './runtimeStateApplier';", "usePrimaryFormActionRuntime.ts"),
        (primary_runtime, "import type { BusyKind, ContractAction, SubmissionFeedback, UiStatus } from './types';", "usePrimaryFormActionRuntime.ts"),
        (form_config_runtime, "import { applyFormRuntimeBusyEvent, applyFormRuntimeStatusEvent } from './runtimeStateApplier';", "useFormConfigSaveRuntime.ts"),
        (form_config_runtime, "UiStatus", "useFormConfigSaveRuntime.ts"),
        (inline_policy_runtime, "import { applyFormRuntimeBusyEvent, applyFormRuntimeStatusEvent } from './runtimeStateApplier';", "useInlineFieldPolicyRuntime.ts"),
        (inline_policy_runtime, "UiStatus", "useInlineFieldPolicyRuntime.ts"),
        (contract_mode_runtime, "import { applyFormRuntimeBusyEvent, applyFormRuntimeStatusEvent } from './runtimeStateApplier';", "useContractModeActionRuntime.ts"),
        (contract_mode_runtime, "UiStatus", "useContractModeActionRuntime.ts"),
    ]
    for source, token, label in required_consumers:
        if token not in source:
            errors.append(f"{label} missing runtime protocol consumer token: {token}")

    required_action_applier_tokens = [
        "applyFormRuntimeStatusEvent(params, {",
        "transaction: 'runAction'",
        "errorMessage: '打开操作缺少目标页面'",
        "errorMessage: err instanceof Error ? err.message : '场景操作执行失败'",
        "errorMessage: err instanceof Error ? err.message : '操作执行失败'",
    ]
    for token in required_action_applier_tokens:
        if token not in action_runtime:
            errors.append(f"useFormActionRuntime.ts missing status applier token: {token}")

    stale_action_writes = [
        "params.errorMessage.value = '打开操作缺少目标页面';",
        "params.errorMessage.value = err instanceof Error ? err.message : '场景操作执行失败';",
        "params.errorMessage.value = err instanceof Error ? err.message : '操作执行失败';",
    ]
    for token in stale_action_writes:
        if token in action_runtime:
            errors.append(f"useFormActionRuntime.ts still bypasses status applier: {token}")

    required_primary_applier_tokens = [
        "applyFormRuntimeStatusEvent(params, {",
        "transaction: 'primaryAction'",
        "errorMessage: '操作失败：请先保存记录后再执行'",
        "errorMessage: '提交失败：请先保存记录后再提交'",
    ]
    for token in required_primary_applier_tokens:
        if token not in primary_runtime:
            errors.append(f"usePrimaryFormActionRuntime.ts missing status applier token: {token}")

    stale_primary_writes = [
        "params.errorMessage.value = '操作失败：请先保存记录后再执行';",
        "params.errorMessage.value = '提交失败：请先保存记录后再提交';",
    ]
    for token in stale_primary_writes:
        if token in primary_runtime:
            errors.append(f"usePrimaryFormActionRuntime.ts still bypasses status applier: {token}")

    config_status_event_requirements = [
        (form_config_runtime, "useFormConfigSaveRuntime.ts", "transaction: 'formConfig'", "errorMessage: err instanceof Error ? err.message : '表单字段顺序更新失败'"),
        (inline_policy_runtime, "useInlineFieldPolicyRuntime.ts", "transaction: 'inlinePolicy'", "errorMessage: err instanceof Error ? err.message : '字段显示规则更新失败'"),
        (contract_mode_runtime, "useContractModeActionRuntime.ts", "transaction: 'contractMode'", "errorMessage: err instanceof Error ? err.message : '表单配置操作失败'"),
    ]
    for source, label, transaction_token, error_token in config_status_event_requirements:
        for token in ["applyFormRuntimeStatusEvent(params, {", transaction_token, error_token]:
            if token not in source:
                errors.append(f"{label} missing config status applier token: {token}")

    stale_config_writes = [
        (form_config_runtime, "useFormConfigSaveRuntime.ts", "params.errorMessage.value = err instanceof Error ? err.message : '表单字段顺序更新失败';"),
        (inline_policy_runtime, "useInlineFieldPolicyRuntime.ts", "params.errorMessage.value = err instanceof Error ? err.message : '字段显示规则更新失败';"),
        (contract_mode_runtime, "useContractModeActionRuntime.ts", "params.errorMessage.value = err instanceof Error ? err.message : '表单配置操作失败';"),
    ]
    for source, label, token in stale_config_writes:
        if token in source:
            errors.append(f"{label} still bypasses status applier: {token}")

    config_busy_event_requirements = [
        (form_config_runtime, "useFormConfigSaveRuntime.ts", "transaction: 'formConfig'"),
        (inline_policy_runtime, "useInlineFieldPolicyRuntime.ts", "transaction: 'inlinePolicy'"),
        (contract_mode_runtime, "useContractModeActionRuntime.ts", "transaction: 'contractMode'"),
    ]
    for source, label, transaction_token in config_busy_event_requirements:
        for token in [
            "applyFormRuntimeBusyEvent(params, {",
            "kind: 'begin'",
            "busyKind: 'action'",
            "kind: 'end'",
            transaction_token,
        ]:
            if token not in source:
                errors.append(f"{label} missing config busy applier token: {token}")

    stale_config_busy_writes = [
        (form_config_runtime, "useFormConfigSaveRuntime.ts"),
        (inline_policy_runtime, "useInlineFieldPolicyRuntime.ts"),
        (contract_mode_runtime, "useContractModeActionRuntime.ts"),
    ]
    for source, label in stale_config_busy_writes:
        if "params.busyKind.value =" in source:
            errors.append(f"{label} still bypasses busy applier")

    required_page_status_tokens = [
        "transaction: 'formReload'",
        "transaction: 'runAction'",
        "transaction: 'formConfig'",
        "transaction: 'contractMode'",
        "transaction: 'primaryAction'",
        "errorMessage: '请填写操作原因'",
        "errorMessage: err instanceof Error ? err.message : '表单加载失败'",
    ]
    for token in required_page_status_tokens:
        if token not in page:
            errors.append(f"ContractFormPage.vue missing status applier token: {token}")

    forbidden_page_status_write_patterns = [
        (r"\bstatus\.value\s*=(?!=)", "status.value assignment"),
        (r"\berrorMessage\.value\s*=(?!=)", "errorMessage.value assignment"),
    ]
    for pattern, label in forbidden_page_status_write_patterns:
        if re.search(pattern, page):
            errors.append(f"ContractFormPage.vue must route status/error writes through applier; forbidden token: {label}")

    ci_token = "python3 scripts/verify/contract_form_runtime_state_protocol_guard.py"
    if ci_token not in ci:
        errors.append("ci.local.quick must run contract_form_runtime_state_protocol_guard.py")
    behavior_ci_token = "scripts/verify/contract_form_runtime_state_behavior_guard.sh"
    if behavior_ci_token not in ci:
        errors.append("ci.local.quick must run contract_form_runtime_state_behavior_guard.sh")

    if errors:
        print("[contract_form_runtime_state_protocol_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_form_runtime_state_protocol_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
