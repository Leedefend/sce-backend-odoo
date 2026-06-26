#!/usr/bin/env python3
"""Guard frontend consumers prefer formal V2 policy projections."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_HELPERS = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractV2.ts"
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
]

REQUIRED_HELPERS = (
    "resolveUnifiedPageContractV2DeletePolicy",
    "resolveUnifiedPageContractV2SurfacePolicies",
    "resolveUnifiedPageContractV2ListProfile",
    "resolveUnifiedPageContractV2BusinessOperationProfile",
    "resolveUnifiedPageContractV2FormStructureContract",
    "resolveUnifiedPageContractV2VisibleFields",
)

FORBIDDEN_DIRECT_READS = (
    ".delete_policy",
    ".surface_policies",
    ".list_profile",
    ".business_operation_profile",
    ".form_structure_contract",
    ".visible_fields",
)

ALLOWED_DIRECT_READS = {
    "frontend/apps/web/src/app/runtime/unifiedPageContractV2CompatProjection.ts": {
        ".delete_policy": {"const candidate = asDict(node.delete_policy);"},
        ".list_profile": {"const legacyListProfile = asDict(legacyProjection.list_profile);"},
    },
}


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _has_helper_call(source: str, helper: str) -> bool:
    return bool(re.search(rf"\b{re.escape(helper)}\s*\(", source))


def main() -> int:
    violations: list[str] = []
    helper_source = CONTRACT_HELPERS.read_text(encoding="utf-8")
    for helper in REQUIRED_HELPERS:
        if f"export function {helper}(" not in helper_source:
            violations.append(f"{_relative(CONTRACT_HELPERS)}: missing exported helper {helper}")

    for path in CONSUMER_FILES:
        source = path.read_text(encoding="utf-8")
        rel = _relative(path)
        if rel != _relative(CONTRACT_HELPERS):
            if "surface_policies" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2SurfacePolicies"):
                violations.append(f"{rel}: surface_policies consumers must use resolveUnifiedPageContractV2SurfacePolicies")
            if "list_profile" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2ListProfile"):
                violations.append(f"{rel}: list_profile consumers must use resolveUnifiedPageContractV2ListProfile")
            if "delete_policy" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2DeletePolicy"):
                violations.append(f"{rel}: delete_policy consumers must use resolveUnifiedPageContractV2DeletePolicy")
            if "business_operation_profile" in source and not _has_helper_call(source, "resolveUnifiedPageContractV2BusinessOperationProfile"):
                violations.append(f"{rel}: business_operation_profile consumers must use resolveUnifiedPageContractV2BusinessOperationProfile")
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
