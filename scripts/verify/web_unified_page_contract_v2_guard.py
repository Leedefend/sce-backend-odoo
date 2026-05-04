#!/usr/bin/env python3
"""Guard web contract API migration to Unified Page Contract v2."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB_CONTRACT_API = ROOT / "frontend/apps/web/src/api/contract.ts"
WEB_CONTRACT_V2 = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractV2.ts"
WEB_ACTION_SHAPE = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts"
WEB_ACTION_NAV = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewNavigationRuntime.ts"
WEB_ACTION_PREFLIGHT = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewLoadPreflightRuntime.ts"
WEB_ACTION_META = ROOT / "frontend/apps/web/src/app/runtime/actionViewMetaRuntime.ts"
WEB_ACTION_CONTRACT_RUNTIME = ROOT / "frontend/apps/web/src/app/contractActionRuntime.ts"


def main() -> int:
    source = WEB_CONTRACT_API.read_text(encoding="utf-8") if WEB_CONTRACT_API.exists() else ""
    errors: list[str] = []
    if not source:
        errors.append("frontend web contract API is missing")
    v2_source = WEB_CONTRACT_V2.read_text(encoding="utf-8") if WEB_CONTRACT_V2.exists() else ""
    shape_source = WEB_ACTION_SHAPE.read_text(encoding="utf-8") if WEB_ACTION_SHAPE.exists() else ""
    nav_source = WEB_ACTION_NAV.read_text(encoding="utf-8") if WEB_ACTION_NAV.exists() else ""
    preflight_source = WEB_ACTION_PREFLIGHT.read_text(encoding="utf-8") if WEB_ACTION_PREFLIGHT.exists() else ""
    meta_source = WEB_ACTION_META.read_text(encoding="utf-8") if WEB_ACTION_META.exists() else ""
    contract_runtime_source = WEB_ACTION_CONTRACT_RUNTIME.read_text(encoding="utf-8") if WEB_ACTION_CONTRACT_RUNTIME.exists() else ""
    if "intent: 'ui.contract.v2'" not in source and 'intent: "ui.contract.v2"' not in source:
        errors.append("web contract API must request ui.contract.v2")
    if "intent: 'ui.contract'," in source or 'intent: "ui.contract",' in source:
        errors.append("web contract API must not request legacy ui.contract directly")
    for token in (
        "adaptUnifiedPageContractV2Raw",
        "__unified_page_contract_v2",
        "resolveCompatSource",
        "delivery_profile: 'full'",
        "client_type: 'web_pc'",
        "loadActionUnifiedPageContractV2",
        "loadModelUnifiedPageContractV2",
    ):
        if token not in source:
            errors.append(f"web contract API missing v2 compatibility token: {token}")
    for token in (
        "UnifiedPageContractV2",
        "resolveUnifiedPageContractV2",
        "collectUnifiedPageContractV2FieldWidgets",
        "layoutContract",
        "dataContract",
        "resolveUnifiedPageContractV2PrimaryDataSource",
    ):
        if token not in v2_source:
            errors.append(f"web v2 contract runtime missing token: {token}")
    if "collectUnifiedPageContractV2FieldWidgets" not in shape_source:
        errors.append("web action view shape runtime must consume v2 field widgets before legacy ui_contract fallback")
    if "resolveUnifiedPageContractV2" not in nav_source or "row_click" not in nav_source:
        errors.append("web row navigation runtime must derive default row open behavior from v2 list contracts")
    if "resolveUnifiedPageContractV2PrimaryDataSource" not in preflight_source:
        errors.append("web load preflight runtime must consume v2 primary dataSource")
    if "resolveUnifiedPageContractV2" not in meta_source or "resolveUnifiedPageContractV2" not in contract_runtime_source:
        errors.append("web view mode runtime must resolve view type from v2 pageInfo before legacy fallback")

    if errors:
        print("web unified page contract v2 guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("web unified page contract v2 guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
