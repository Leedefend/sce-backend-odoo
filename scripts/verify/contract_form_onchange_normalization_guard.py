#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "frontend/apps/web/src/pages/contractForm/onchangeNormalization.ts"
PAGE = ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue"
CI = ROOT / "make/ci.mk"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _function_body(source: str, name: str) -> str:
    marker = f"export function {name}"
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


def main() -> int:
    errors: list[str] = []
    helper = _read(HELPER)
    page = _read(PAGE)
    ci = _read(CI)
    if not helper:
        errors.append(f"missing helper: {HELPER.relative_to(ROOT)}")
    if not page:
        errors.append(f"missing page: {PAGE.relative_to(ROOT)}")

    required_helper_tokens = [
        "export type OnchangeRequestPayloadBuildInput",
        "export function buildOnchangeRequestPayload",
        "export function normalizeOnchangeResponse",
        "export function normalizeOnchangeFieldPatch",
        "normalizeContractFieldValue({",
        "mode: 'onchange'",
        "parseMany2oneDisplay(params.value)",
        "normalizeRelationIds(params.value)",
    ]
    for token in required_helper_tokens:
        if token not in helper:
            errors.append(f"onchangeNormalization.ts missing token: {token}")

    forbidden_tokens = [
        "await ",
        "async ",
        "triggerOnchange",
        "intentRequest",
        "router.",
        "window.",
        "queryRelationOptions",
        "upsertRelationOption",
        "initOne2manyRows",
        "applyOnchangeLinePatches",
        "changedFieldSet",
        "dirtyFieldSet",
        "onchangeWarnings",
        "onchangeLinePatches",
        "onchangeModifiersPatch",
        "applyingOnchangePatch",
        ".value =",
    ]
    for name in ("buildOnchangeRequestPayload", "normalizeOnchangeResponse", "normalizeOnchangeFieldPatch"):
        body = _function_body(helper, name)
        if not body:
            errors.append(f"{name} body not found")
            continue
        for token in forbidden_tokens:
            if token in body:
                errors.append(f"{name} must stay pure; forbidden token: {token}")

    required_page_tokens = [
        "buildOnchangeRequestPayload({",
        "normalizeOnchangeResponse(response)",
        "normalizeOnchangeFieldPatch({",
        "const response = await triggerOnchange({",
        "onchangeWarnings.value = warnings;",
        "onchangeLinePatches.value = linePatches;",
        "applyOnchangeLinePatches(linePatches);",
    ]
    for token in required_page_tokens:
        if token not in page:
            errors.append(f"ContractFormPage.vue missing token: {token}")

    stale_page_tokens = [
        "Object.keys(contract.value?.fields || {}).forEach((name) => {",
        "const patch = response?.patch;",
        "const modifiersPatch = response?.modifiers_patch;",
        "Array.isArray(response?.line_patches) ? response.line_patches : []",
        "Array.isArray(response?.warnings) ? response.warnings : []",
        "const option = parseMany2oneDisplay(value);",
        "const ids = normalizeRelationIds(value);",
    ]
    for token in stale_page_tokens:
        if token in page:
            errors.append(f"ContractFormPage.vue still owns onchange normalization token: {token}")

    ci_token = "python3 scripts/verify/contract_form_onchange_normalization_guard.py"
    if ci_token not in ci:
        errors.append("ci.local.quick must run contract_form_onchange_normalization_guard.py")

    if errors:
        print("[contract_form_onchange_normalization_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_form_onchange_normalization_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
