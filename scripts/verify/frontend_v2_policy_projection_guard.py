#!/usr/bin/env python3
"""Guard frontend consumers prefer formal V2 policy projections."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_SCHEMA = ROOT / "docs/architecture/unified_page_contract_v2/unified_page_contract_v2.schema.json"
CONTRACT_HELPERS = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractV2.ts"
STRICT_SCHEMA = ROOT / "frontend/apps/web/src/app/contracts/v2/schema.ts"
STRICT_TYPES = ROOT / "frontend/apps/web/src/app/contracts/v2/types.ts"
CONSUMER_FILES = [
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewPageDisplayStateRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewActionPresentationRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewSurfaceIntentRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewFilterComputedRuntime.ts",
    ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts",
    ROOT / "frontend/apps/web/src/views/ActionView.vue",
    ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue",
    ROOT / "frontend/apps/web/src/app/runtime/unifiedPageContractV2CompatProjection.ts",
    ROOT / "frontend/apps/web/scripts/low_code_global_stability_acceptance.mjs",
]

REQUIRED_HELPERS = (
    "resolveUnifiedPageContractV2DeletePolicy",
    "resolveUnifiedPageContractV2SurfacePolicies",
    "resolveUnifiedPageContractV2ListProfile",
    "resolveUnifiedPageContractV2BusinessOperationProfile",
    "resolveUnifiedPageContractV2FieldGroups",
    "resolveUnifiedPageContractV2FormStructureContract",
    "resolveUnifiedPageContractV2VisibleFields",
)

FORBIDDEN_DIRECT_READS = (
    ".delete_policy",
    ".surface_policies",
    ".list_profile",
    ".business_operation_profile",
    ".field_groups",
    ".form_structure_contract",
    ".visible_fields",
)

ALLOWED_DIRECT_READS = {
    "frontend/apps/web/src/app/runtime/unifiedPageContractV2CompatProjection.ts": {
        ".delete_policy": {"const candidate = asDict(node.delete_policy);"},
        ".list_profile": {"const legacyListProfile = asDict(legacyProjection.list_profile);"},
    },
    "frontend/apps/web/src/pages/ContractFormPage.vue": {
        ".field_groups": {"applyParams.field_groups = changedGroups;"},
    },
}

FORBIDDEN_STRICT_SCHEMA_COMPAT_ALIASES = (
    "['delete_policy']",
    "['surface_policies']",
    "['list_profile']",
    "['business_operation_profile']",
    "row.visible_fields",
    "row.field_groups",
    "row.source_authority",
    "root.form_structure_contract",
    "root.searchContract",
    "root.data",
    "root.rawBody",
    "['page_info']",
    "['layout_contract']",
    "['status_contract']",
    "['action_contract']",
    "['data_contract']",
    "['runtime_contract']",
    "unified_page_contract_v2",
    "__unified_page_contract_v2",
    "legacyContractProjection",
    "legacy_contract_projection",
)

FORBIDDEN_STRICT_TYPE_COMPAT_ALIASES = (
    "delete_policy",
    "surface_policies",
    "list_profile",
    "business_operation_profile",
    "visible_fields",
    "field_groups",
    "form_structure_contract",
    "searchContract",
    "legacyContractProjection",
    "legacy_contract_projection",
)


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _has_helper_call(source: str, helper: str) -> bool:
    return bool(re.search(rf"\b{re.escape(helper)}\s*\(", source))


def _strict_snapshot_fields(source: str) -> set[str]:
    match = re.search(r"export\s+interface\s+ContractV2Snapshot\s*\{(?P<body>.*?)\n\}", source, re.DOTALL)
    if not match:
        return set()
    fields: set[str] = set()
    for line in match.group("body").splitlines():
        field = re.match(r"\s*([A-Za-z_$][\w$]*)\??:", line)
        if field:
            fields.add(field.group(1))
    return fields


def main() -> int:
    violations: list[str] = []
    helper_source = CONTRACT_HELPERS.read_text(encoding="utf-8")
    for helper in REQUIRED_HELPERS:
        if f"export function {helper}(" not in helper_source:
            violations.append(f"{_relative(CONTRACT_HELPERS)}: missing exported helper {helper}")
    strict_schema_source = STRICT_SCHEMA.read_text(encoding="utf-8")
    for token in FORBIDDEN_STRICT_SCHEMA_COMPAT_ALIASES:
        if token in strict_schema_source:
            violations.append(
                f"{_relative(STRICT_SCHEMA)}: strict V2 decoder must not accept compatibility alias {token}"
            )
    strict_type_source = STRICT_TYPES.read_text(encoding="utf-8")
    for token in FORBIDDEN_STRICT_TYPE_COMPAT_ALIASES:
        if token in strict_type_source:
            violations.append(
                f"{_relative(STRICT_TYPES)}: strict V2 types must not declare compatibility alias {token}"
            )
    schema_payload = json.loads(BACKEND_SCHEMA.read_text(encoding="utf-8"))
    schema_top_level = set((schema_payload.get("properties") or {}).keys())
    strict_snapshot_fields = _strict_snapshot_fields(strict_type_source)
    if not strict_snapshot_fields:
        violations.append(f"{_relative(STRICT_TYPES)}: missing ContractV2Snapshot interface")
    elif strict_snapshot_fields != schema_top_level:
        violations.append(
            f"{_relative(STRICT_TYPES)}: ContractV2Snapshot fields must match schema top-level properties; "
            f"extra={sorted(strict_snapshot_fields - schema_top_level)} missing={sorted(schema_top_level - strict_snapshot_fields)}"
        )
    if "const meta = readAliasedObject(root, 'meta', [], '$', issues)" not in strict_schema_source:
        violations.append(f"{_relative(STRICT_SCHEMA)}: strict V2 decoder must require top-level meta object")

    for path in CONSUMER_FILES:
        source = path.read_text(encoding="utf-8")
        rel = _relative(path)
        if "legacyContractProjection" in source or "legacy_contract_projection" in source:
            violations.append(f"{rel}: stable V2 consumers must not read legacyContractProjection")
        if rel != _relative(CONTRACT_HELPERS):
            if "surface_policies" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2SurfacePolicies"):
                violations.append(f"{rel}: surface_policies consumers must use resolveUnifiedPageContractV2SurfacePolicies")
            if "list_profile" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2ListProfile"):
                violations.append(f"{rel}: list_profile consumers must use resolveUnifiedPageContractV2ListProfile")
            if "delete_policy" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2DeletePolicy"):
                violations.append(f"{rel}: delete_policy consumers must use resolveUnifiedPageContractV2DeletePolicy")
            if "business_operation_profile" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2BusinessOperationProfile"):
                violations.append(f"{rel}: business_operation_profile consumers must use resolveUnifiedPageContractV2BusinessOperationProfile")
            if "field_groups" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2FieldGroups"):
                violations.append(f"{rel}: field_groups consumers must use resolveUnifiedPageContractV2FieldGroups")
            if "form_structure_contract" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2FormStructureContract"):
                violations.append(f"{rel}: form_structure_contract consumers must use resolveUnifiedPageContractV2FormStructureContract")
            if "visible_fields" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2VisibleFields"):
                violations.append(f"{rel}: visible_fields consumers must use resolveUnifiedPageContractV2VisibleFields")

        allowed = ALLOWED_DIRECT_READS.get(rel, {})
        for index, line in enumerate(source.splitlines(), start=1):
            stripped = line.strip()
            for token in FORBIDDEN_DIRECT_READS:
                if token not in stripped:
                    continue
                if stripped in allowed.get(token, set()):
                    continue
                violations.append(f"{rel}:{index}: direct read of legacy root field {token}")

    if violations:
        print("[frontend_v2_policy_projection_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[frontend_v2_policy_projection_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
