#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "frontend/apps/web/src/pages/contractForm/saveRecordHelpers.ts"
SAVE_RUNTIME = ROOT / "frontend/apps/web/src/pages/contractForm/useRecordFormActions.ts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"export function {re.escape(name)}\([^)]*\) \{{", source)
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
    helper = _read(HELPER)
    save_runtime = _read(SAVE_RUNTIME)
    if not helper:
        errors.append(f"missing helper: {HELPER.relative_to(ROOT)}")
    if not save_runtime:
        errors.append(f"missing save runtime: {SAVE_RUNTIME.relative_to(ROOT)}")

    required_tokens = [
        "export type SaveRecordPayloadBuildInput",
        "export function buildSaveRecordPayload(params: SaveRecordPayloadBuildInput)",
        "export function collectRecordSaveValues(params: SaveRecordPayloadBuildInput)",
        "return buildSaveRecordPayload(params);",
    ]
    for token in required_tokens:
        if token not in helper:
            errors.append(f"saveRecordHelpers.ts missing token: {token}")

    builder_body = _function_body(helper, "buildSaveRecordPayload")
    if not builder_body:
        errors.append("buildSaveRecordPayload body not found")
    else:
        forbidden_tokens = [
            "await ",
            "async ",
            "router.",
            "window.",
            "intentRequest",
            "createContractFormRecord",
            "writeContractFormRecord",
            "uploadPending",
            "busyKind",
            "submissionFeedback",
            "validationErrors",
            ".value =",
        ]
        for token in forbidden_tokens:
            if token in builder_body:
                errors.append(f"buildSaveRecordPayload must stay pure; forbidden token: {token}")
        if "Object.entries(params.editableMap)" not in builder_body:
            errors.append("buildSaveRecordPayload must be driven by editableMap entries")
        if "params.dirtyFieldSet.has(key)" not in builder_body:
            errors.append("buildSaveRecordPayload must preserve dirty-field filtering for existing records")
        if "params.comparableFieldValue(key, params.formData[key])" not in builder_body:
            errors.append("buildSaveRecordPayload must compare current formData against originalValues")

    runtime_required = [
        "buildSaveRecordPayload({",
        "comparableFieldValue: (name, value) => comparableFieldValue(name, value)",
        "editableMap",
        "dirtyFieldSet",
        "originalValues: originalValues.value",
    ]
    for token in runtime_required:
        if token not in save_runtime:
            errors.append(f"useRecordFormActions.ts missing token: {token}")
    if "collectRecordSaveValues({" in save_runtime:
        errors.append("useRecordFormActions.ts should call buildSaveRecordPayload directly")

    if errors:
        print("[contract_form_save_payload_builder_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_form_save_payload_builder_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
