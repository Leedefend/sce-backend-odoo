#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/engineering_convergence/contract_form_side_effect_map.md"
PAGE = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
ACTION_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/useFormActionRuntime.ts"
CI = ROOT / "make/ci.mk"

REQUIRED_GUARDS = [
    "contract_form_runtime_state_protocol_guard.py",
    "contract_form_runtime_state_behavior_guard.sh",
    "contract_form_onchange_normalization_guard.py",
    "contract_form_action_plan_builder_guard.py",
    "contract_form_save_payload_builder_guard.py",
    "frontend_page_contract_boundary_guard.py",
    "frontend_page_contract_orchestration_consumption_guard.py",
]

REQUIRED_SCENARIOS = [
    "Edit existing record",
    "Create record",
    "Save validation failure",
    "Save API failure",
    "Normal action",
    "Tier or prompt action",
    "Config save",
    "Inline field policy",
    "Contract mode action",
    "Onchange field patch",
    "Relation onchange",
    "Native structures",
    "Duplicate click",
    "Network or action error",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"(?:async\s+)?function\s+{re.escape(name)}\([^)]*\)[^{{]*\{{", source)
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


def _method_body(source: str, name: str) -> str:
    marker = f"async function {name}("
    start = source.find(marker)
    if start < 0:
        return ""
    open_brace = source.find("{", start)
    if open_brace < 0:
        return ""
    depth = 1
    index = open_brace + 1
    while index < len(source):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[open_brace + 1:index]
        index += 1
    return ""


def _line_for_token(source: str, token: str) -> int:
    index = source.find(token)
    if index < 0:
        return -1
    return source[:index].count("\n") + 1


def main() -> int:
    errors: list[str] = []
    doc = _read(DOC)
    page = _read(PAGE)
    action_runtime = _read(ACTION_RUNTIME)
    ci = _read(CI)

    if not doc:
        errors.append(f"missing side-effect map: {DOC.relative_to(ROOT)}")
    if not page:
        errors.append(f"missing ContractFormPage: {PAGE.relative_to(ROOT)}")
    if not action_runtime:
        errors.append(f"missing action runtime: {ACTION_RUNTIME.relative_to(ROOT)}")

    required_doc_tokens = [
        "## Behavior Regression Matrix",
        "does not authorize moving transaction owners out of the page/runtime",
        "Manual form regression means exercising the path in a browser or containerized",
        "`saveRecord`",
        "`runAction`",
        "`runOnchangeRoundtrip`",
    ]
    for token in required_doc_tokens:
        if token not in doc:
            errors.append(f"side-effect map missing token: {token}")

    for scenario in REQUIRED_SCENARIOS:
        row_marker = f"| {scenario} |"
        if row_marker not in doc:
            errors.append(f"behavior regression matrix missing scenario: {scenario}")

    for guard in REQUIRED_GUARDS:
        if guard not in doc:
            errors.append(f"behavior regression matrix must cite guard: {guard}")
        if guard not in ci:
            errors.append(f"ci.local.quick must run or retain guard: {guard}")

    if "contract_form_side_effect_regression_guard.py" not in ci:
        errors.append("ci.local.quick must run contract_form_side_effect_regression_guard.py")

    save_body = _function_body(page, "saveRecord")
    if not save_body:
        errors.append("ContractFormPage.vue must keep saveRecord transaction owner")
    else:
        validation_line = _line_for_token(save_body, "const validation = await validateBeforeSaveRecord({")
        save_busy_line = _line_for_token(save_body, "busyKind.value = 'save';")
        finally_clear_line = _line_for_token(save_body, "finally {\n    busyKind.value = null;")
        if validation_line < 0:
            errors.append("saveRecord must keep validateBeforeSaveRecord precheck")
        if save_busy_line < 0:
            errors.append("saveRecord must still own save busy lifecycle")
        if validation_line >= 0 and save_busy_line >= 0 and not validation_line < save_busy_line:
            errors.append("saveRecord validation must happen before save busy begins")
        for token in [
            "if (!validation.ok || !validation.editableMap) {",
            "return false;",
            "await writeContractFormRecord({",
            "await createContractFormRecord({",
            "await uploadPendingNativeAttachments(Number(created.id))",
            "await navigateCreatedRecord({",
            "validationErrors.value = [message];",
            "submissionFeedback.value = { kind: 'error'",
        ]:
            if token not in save_body:
                errors.append(f"saveRecord missing side-effect boundary token: {token}")
        if finally_clear_line < 0:
            errors.append("saveRecord must clear save busy in finally")

    onchange_body = _function_body(page, "runOnchangeRoundtrip")
    if not onchange_body:
        errors.append("ContractFormPage.vue must keep runOnchangeRoundtrip transaction owner")
    else:
        for token in [
            "const response = await triggerOnchange({",
            "normalizeOnchangeResponse(response)",
            "onchangeWarnings.value = warnings;",
            "onchangeLinePatches.value = linePatches;",
            "applyOnchangeLinePatches(linePatches);",
            "catch {",
            "Onchange is best-effort; keep current values when roundtrip fails.",
        ]:
            if token not in onchange_body:
                errors.append(f"runOnchangeRoundtrip missing behavior token: {token}")
        if "busyKind.value" in onchange_body:
            errors.append("runOnchangeRoundtrip must stay silent and not own global busyKind")

    action_body = _method_body(action_runtime, "runAction")
    if not action_body:
        errors.append("useFormActionRuntime.ts must keep runAction transaction owner")
    else:
        for token in [
            "if (!action.enabled) return;",
            "if (!await params.confirmActionSafety(action)) return;",
            "const plan = buildFormActionExecutionPlan({",
            "if (plan.kind === 'scene_mutation')",
            "if (actionParams === null) return;",
            "params.busyKind.value = 'action';",
            "await params.executeSceneMutation({",
            "if (!await params.ensureSavedBeforeRecordAction()) return;",
            "const response = await executeButton({",
            "applyFormRuntimeStatusEvent(params, {",
            "params.busyKind.value = null;",
        ]:
            if token not in action_body:
                errors.append(f"runAction missing behavior token: {token}")

    if errors:
        print("[contract_form_side_effect_regression_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_form_side_effect_regression_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
