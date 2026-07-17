#!/usr/bin/env python3
"""Guard web contract API migration to Unified Page Contract v2."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB_CONTRACT_API = ROOT / "frontend/apps/web/src/api/contract.ts"
WEB_CONTRACT_V2 = ROOT / "frontend/apps/web/src/app/contracts/unifiedPageContractV2.ts"
WEB_ACTION_SHAPE = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewContractShapeRuntime.ts"
WEB_FILTER_COMPUTED = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewFilterComputedRuntime.ts"
WEB_ACTION_PRESENTATION = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewActionPresentationRuntime.ts"
WEB_ACTION_RUNTIME = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewActionRuntime.ts"
WEB_ACTION_NAV = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewNavigationRuntime.ts"
WEB_ACTION_PREFLIGHT = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewLoadPreflightRuntime.ts"
WEB_ACTION_LOAD_REQUEST = ROOT / "frontend/apps/web/src/app/action_runtime/useActionViewLoadRequestRuntime.ts"
WEB_ACTION_META = ROOT / "frontend/apps/web/src/app/runtime/actionViewMetaRuntime.ts"
WEB_COMPAT_PROJECTION = ROOT / "frontend/apps/web/src/app/runtime/unifiedPageContractV2CompatProjection.ts"
WEB_ACTION_CONTRACT_RUNTIME = ROOT / "frontend/apps/web/src/app/contractActionRuntime.ts"
WEB_RECORD_RUNTIME = ROOT / "frontend/apps/web/src/app/contractRecordRuntime.ts"
WEB_SURFACE_CONTRACT = ROOT / "frontend/apps/web/src/app/contracts/actionViewSurfaceContract.ts"
WEB_ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
WEB_NATIVE_LAYOUT = ROOT / "frontend/apps/web/src/pages/contractForm/nativeLayoutUtils.ts"


def main() -> int:
    source = WEB_CONTRACT_API.read_text(encoding="utf-8") if WEB_CONTRACT_API.exists() else ""
    errors: list[str] = []
    if not source:
        errors.append("frontend web contract API is missing")
    v2_source = WEB_CONTRACT_V2.read_text(encoding="utf-8") if WEB_CONTRACT_V2.exists() else ""
    shape_source = WEB_ACTION_SHAPE.read_text(encoding="utf-8") if WEB_ACTION_SHAPE.exists() else ""
    filter_source = WEB_FILTER_COMPUTED.read_text(encoding="utf-8") if WEB_FILTER_COMPUTED.exists() else ""
    action_presentation_source = WEB_ACTION_PRESENTATION.read_text(encoding="utf-8") if WEB_ACTION_PRESENTATION.exists() else ""
    action_runtime_source = WEB_ACTION_RUNTIME.read_text(encoding="utf-8") if WEB_ACTION_RUNTIME.exists() else ""
    nav_source = WEB_ACTION_NAV.read_text(encoding="utf-8") if WEB_ACTION_NAV.exists() else ""
    preflight_source = WEB_ACTION_PREFLIGHT.read_text(encoding="utf-8") if WEB_ACTION_PREFLIGHT.exists() else ""
    load_request_source = WEB_ACTION_LOAD_REQUEST.read_text(encoding="utf-8") if WEB_ACTION_LOAD_REQUEST.exists() else ""
    meta_source = WEB_ACTION_META.read_text(encoding="utf-8") if WEB_ACTION_META.exists() else ""
    compat_projection_source = WEB_COMPAT_PROJECTION.read_text(encoding="utf-8") if WEB_COMPAT_PROJECTION.exists() else ""
    contract_runtime_source = WEB_ACTION_CONTRACT_RUNTIME.read_text(encoding="utf-8") if WEB_ACTION_CONTRACT_RUNTIME.exists() else ""
    record_runtime_source = WEB_RECORD_RUNTIME.read_text(encoding="utf-8") if WEB_RECORD_RUNTIME.exists() else ""
    surface_source = WEB_SURFACE_CONTRACT.read_text(encoding="utf-8") if WEB_SURFACE_CONTRACT.exists() else ""
    action_view_source = WEB_ACTION_VIEW.read_text(encoding="utf-8") if WEB_ACTION_VIEW.exists() else ""
    native_layout_source = WEB_NATIVE_LAYOUT.read_text(encoding="utf-8") if WEB_NATIVE_LAYOUT.exists() else ""
    field_schema_source = (ROOT / "frontend/apps/web/src/pages/contractForm/useRecordFormFieldSchemas.ts").read_text(encoding="utf-8")
    form_page_source = (ROOT / "frontend/apps/web/src/pages/ContractFormPage.vue").read_text(encoding="utf-8")
    if "intent: 'ui.contract.v2'" not in source and 'intent: "ui.contract.v2"' not in source:
        errors.append("web contract API must request ui.contract.v2")
    if "intent: 'ui.contract'," in source or 'intent: "ui.contract",' in source:
        errors.append("web contract API must not request legacy ui.contract directly")
    for token in (
        "adaptUnifiedPageContractV2Raw",
        "__unified_page_contract_v2",
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
        "collectUnifiedPageContractV2FieldStatus",
        "collectUnifiedPageContractV2WidgetStatus",
        "collectUnifiedPageContractV2ButtonStatus",
        "collectUnifiedPageContractV2SelectorStatus",
        "resolveUnifiedPageContractV2SelectorStatus",
        "resolveUnifiedPageContractV2GlobalStatus",
        "collectUnifiedPageContractV2ContainerStatus",
        "collectUnifiedPageContractV2FieldContainerStatus",
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
    if "resolveUnifiedPageContractV2PrimaryDataSource" not in load_request_source or "domain_raw" not in load_request_source or "context_raw" not in load_request_source:
        errors.append("web load request runtime must merge v2 primary dataSource domain/context into api.data payload")
    if "resolveUnifiedPageContractV2" not in meta_source or "resolveUnifiedPageContractV2" not in contract_runtime_source:
        errors.append("web view mode runtime must resolve view type from v2 pageInfo before legacy fallback")
    if "resolveUnifiedPageContractV2GlobalStatus" not in contract_runtime_source or "UNIFIED_PAGE_CONTRACT_V2_PAGE_FORBIDDEN" not in contract_runtime_source:
        errors.append("web contract action runtime must honor v2 globalStatus for page access/read guards")
    if "collectUnifiedPageContractV2FieldWidgets" not in record_runtime_source or "collectUnifiedPageContractV2FieldStatus" not in record_runtime_source or "mapV2ActionButton" not in record_runtime_source:
        errors.append("web record runtime must build form fields, states, and actions from v2 before legacy fallback")
    if "resolveV2CollaborationContract" not in compat_projection_source:
        errors.append("web v2 compatibility projection must consume runtimeContract.collaboration for chatter/attachments")
    for token in (
        "v2Contract.workflowContract",
        "asDict(v2Contract.runtimeContract).workflowContract",
        "workflowContract,",
        "runtimeContract: { workflowContract }",
        "__unified_page_contract_v2: v2Contract",
    ):
        if token not in compat_projection_source:
            errors.append(f"web v2 compatibility projection must preserve workflow contract token: {token}")
    if "resolveUnifiedPageContractV2GlobalStatus" not in record_runtime_source or "pageAuth === 'read'" not in record_runtime_source:
        errors.append("web record runtime must merge v2 globalStatus into form rights")
    if "collectUnifiedPageContractV2FieldContainerStatus" not in record_runtime_source or "container?.visible === false" not in record_runtime_source:
        errors.append("web record runtime must merge v2 containerStatus into form fields")
    if "collectUnifiedPageContractV2ButtonStatus" not in record_runtime_source or "resolveV2ActionButtonStatus" not in record_runtime_source:
        errors.append("web record runtime must apply v2 buttonStatus to form action buttons")
    if "collectUnifiedPageContractV2FieldStatus" not in shape_source:
        errors.append("web list shape runtime must honor v2 widget status for default column visibility")
    if "resolveUnifiedPageContractV2SelectorStatus" not in filter_source or "isSelectorEnabled" not in filter_source:
        errors.append("web filter runtime must honor v2 selectorStatus for search/filter/group controls")
    if "pageInfo?.model" not in shape_source:
        errors.append("web model resolver must prefer v2 pageInfo.model before legacy model fallbacks")
    if "resolveUnifiedPageContractV2" not in surface_source:
        errors.append("web action surface contract must include v2 pageInfo view modes")
    if "collectUnifiedPageContractV2FieldStatus" not in form_page_source:
        errors.append("web contract form page must merge v2 widget status into runtime field states")
    if "resolveUnifiedPageContractV2GlobalStatus" not in form_page_source or "pageAuth === 'read'" not in form_page_source:
        errors.append("web contract form page must merge v2 globalStatus into form rights")
    if (
        "collectUnifiedPageContractV2FieldContainerStatus" not in field_schema_source
        or "containerStatus:collectUnifiedPageContractV2FieldContainerStatus(context.contract.value)" not in field_schema_source
        or "containerStatus?.visible === false" not in native_layout_source
    ):
        errors.append("web contract form page must merge v2 containerStatus into layout field visibility/read state")
    if "collectUnifiedPageContractV2ButtonStatus" not in form_page_source or "resolveV2ButtonStatus" not in form_page_source:
        errors.append("web contract form page must merge v2 buttonStatus into contract actions")
    if "collectUnifiedPageContractV2ButtonStatus" not in action_view_source or "applyActionViewV2ButtonStatus" not in action_view_source:
        errors.append("web action view toolbar actions must merge v2 buttonStatus into contract actions")
    if "normalizeV2ActionRows" not in action_presentation_source or "actionContract.actionRuleList" not in action_presentation_source:
        errors.append("web action presentation runtime must merge v2 actionRuleList into toolbar actions")
    if "resolveV2RefreshPolicy" not in action_presentation_source or "action.refreshMode" not in action_presentation_source:
        errors.append("web action presentation runtime must map v2 refreshMode into refreshPolicy")
    if "applyActionRefreshPolicy(action.refreshPolicy)" not in action_runtime_source:
        errors.append("web action runtime must apply action refreshPolicy after successful button execution")

    if errors:
        print("web unified page contract v2 guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("web unified page contract v2 guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
