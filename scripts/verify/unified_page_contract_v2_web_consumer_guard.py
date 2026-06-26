#!/usr/bin/env python3
"""Guard the web Unified Page Contract v2 consumer surface."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = ROOT / "frontend/apps/web/src"
FORBIDDEN_FRONTEND_STRUCTURE_TITLE_TOKENS = (
    "合同事实",
    "工程与合同约定",
    "合同识别",
    "金额事实",
)


def read(path: str) -> str:
    return (WEB_ROOT / path).read_text(encoding="utf-8")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require_tokens(errors: list[str], source: str, label: str, tokens: tuple[str, ...]) -> None:
    for token in tokens:
        if token not in source:
            fail(errors, f"{label} missing token: {token}")


def main() -> int:
    errors: list[str] = []

    contract_source = read("app/contracts/unifiedPageContractV2.ts")
    action_view_source = read("views/ActionView.vue")
    record_runtime_source = read("app/contractRecordRuntime.ts")
    action_runtime_source = read("app/contractActionRuntime.ts")
    action_presentation_source = read("app/action_runtime/useActionViewActionPresentationRuntime.ts")
    load_request_source = read("app/action_runtime/useActionViewLoadRequestRuntime.ts")
    load_preflight_source = read("app/action_runtime/useActionViewLoadPreflightRuntime.ts")
    filter_runtime_source = read("app/action_runtime/useActionViewFilterComputedRuntime.ts")
    surface_contract_source = read("app/contracts/actionViewSurfaceContract.ts")
    meta_runtime_source = read("app/runtime/actionViewMetaRuntime.ts")
    navigation_runtime_source = read("app/action_runtime/useActionViewNavigationRuntime.ts")
    shape_runtime_source = read("app/action_runtime/useActionViewContractShapeRuntime.ts")
    contract_form_source = read("pages/ContractFormPage.vue")

    require_tokens(errors, contract_source, "web v2 contract resolver", (
        "export type UnifiedPageContractV2ClientType = 'web_pc' | 'wx_mini' | 'harmony_h5'",
        "export function isUnifiedPageContractV2",
        "asText(pageInfo.contractVersion).startsWith('2.')",
        "root.__unified_page_contract_v2",
        "rawBody.unified_page_contract_v2",
        "collectUnifiedPageContractV2FieldWidgets",
        "collectUnifiedPageContractV2WidgetStatus",
        "collectUnifiedPageContractV2ButtonStatus",
        "collectUnifiedPageContractV2SelectorStatus",
        "resolveUnifiedPageContractV2GlobalStatus",
        "collectUnifiedPageContractV2FieldContainerStatus",
        "resolveUnifiedPageContractV2PrimaryDataSource",
        "formStructureContract?: Record<string, unknown>",
        "businessOperationProfile?: Record<string, unknown>",
        "visibleFields?: UnifiedPageContractV2VisibleFields",
        "fieldGroups?: UnifiedPageContractV2FieldGroups",
        "deletePolicy?: Record<string, unknown>",
        "surfacePolicies?: Record<string, unknown>",
        "listProfile?: Record<string, unknown>",
    ))
    require_tokens(errors, record_runtime_source, "web v2 record runtime", (
        "resolveUnifiedPageContractV2(contract)",
        "resolveUnifiedPageContractV2GlobalStatus(contract)",
        "collectUnifiedPageContractV2FieldWidgets(contract)",
        "collectUnifiedPageContractV2FieldStatus(contract)",
        "collectUnifiedPageContractV2FieldContainerStatus(contract)",
        "buildV2Fields",
        "hasV2Form",
        "mapV2ActionButton",
        "collectUnifiedPageContractV2ButtonStatus(contract)",
        "status?.disabled === true",
    ))
    require_tokens(errors, action_runtime_source, "web v2 access runtime", (
        "resolveUnifiedPageContractV2(contract)",
        "v2?.pageInfo?.viewType",
        "resolveUnifiedPageContractV2GlobalStatus(contract)",
        "pageAuth === 'none'",
        "UNIFIED_PAGE_CONTRACT_V2_PAGE_FORBIDDEN",
    ))
    require_tokens(errors, action_presentation_source, "web v2 action presentation", (
        "normalizeV2ActionRows",
        "v2.actionContract.actionRuleList",
        "resolveV2RefreshPolicy(action.refreshMode)",
        "unified_page_contract_v2_action_id",
        "unified_page_contract_v2_source_widget_id",
        "unified_page_contract_v2_refresh_mode",
    ))
    require_tokens(errors, action_view_source, "web ActionView v2 status bridge", (
        "collectUnifiedPageContractV2ButtonStatus",
        "resolveActionViewV2ButtonStatus",
        "applyActionViewV2ButtonStatus",
        "status?.visible === false",
        "disabled_by_status_contract",
    ))
    require_tokens(errors, load_request_source, "web v2 load request", (
        "resolveUnifiedPageContractV2PrimaryDataSource(options.contract)",
        "sourceDomainRaw",
        "requestPayload.domain_raw = sourceDomainRaw",
        "sourceContextRaw",
        "requestPayload.context_raw = sourceContextRaw",
        "requestPayload.domain = v2PrimaryParams.domain",
        "requestPayload.context = {",
    ))
    require_tokens(errors, load_preflight_source, "web v2 load preflight", (
        "resolveUnifiedPageContractV2PrimaryDataSource(contract)",
        "v2PrimaryParams.order || searchDefaults?.order",
        "v2PrimaryParams.limit || searchDefaults?.limit",
    ))
    require_tokens(errors, filter_runtime_source, "web v2 selector status", (
        "resolveUnifiedPageContractV2SelectorStatus",
        "isSelectorEnabled",
        "status?.visible !== false && status?.disabled !== true",
        "selectorTokens(`filter.${key}`, key)",
        "selectorTokens(`group.${field}`, field)",
    ))
    require_tokens(errors, surface_contract_source, "web v2 surface modes", (
        "resolveUnifiedPageContractV2(contract)",
        "addModes(v2?.pageInfo?.viewType)",
    ))
    require_tokens(errors, meta_runtime_source, "web v2 meta runtime", (
        "resolveUnifiedPageContractV2(contract)",
        "v2?.pageInfo?.viewType",
    ))
    require_tokens(errors, navigation_runtime_source, "web v2 navigation runtime", (
        "resolveUnifiedPageContractV2(contract)",
        "['list', 'tree', 'kanban'].includes(v2ViewType)",
    ))
    require_tokens(errors, shape_runtime_source, "web v2 shape runtime", (
        "collectUnifiedPageContractV2FieldWidgets",
        "collectUnifiedPageContractV2FieldStatus",
        "resolveUnifiedPageContractV2",
        "v2?.pageInfo?.model",
    ))
    require_tokens(errors, contract_form_source, "web v2 form structure store selector", (
        "resolveContractV2FormStructureContract",
        "v2ShadowFormStructureContract",
        "v2ShadowFormStructureSlotCount",
    ))
    for token in FORBIDDEN_FRONTEND_STRUCTURE_TITLE_TOKENS:
        if token in contract_form_source or token in contract_source:
            fail(errors, f"web v2 form structure must not hard-code business title: {token}")

    if errors:
        print("Unified Page Contract v2 web consumer guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Unified Page Contract v2 web consumer guard passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
