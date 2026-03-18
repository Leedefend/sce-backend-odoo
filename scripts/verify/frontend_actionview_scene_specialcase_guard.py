#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
ACTION_VIEW = ROOT / "frontend/apps/web/src/views/ActionView.vue"
ACTION_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewActionRuntime.ts"
BATCH_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewBatchRuntime.ts"
PAGE_MODEL = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts"
SELECTION_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewSelectionRuntime.ts"
TRIGGER_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewTriggerRuntime.ts"
GROUPED_ROWS_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewGroupedRowsRuntime.ts"
ROUTE_PRESET_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewRoutePresetRuntime.ts"
FILTER_GROUP_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewFilterGroupRuntime.ts"
HEADER_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewHeaderRuntime.ts"
NAVIGATION_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewNavigationRuntime.ts"
REQUEST_CONTEXT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewRequestContextRuntime.ts"
SCOPED_METRICS_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewScopedMetricsRuntime.ts"
CONTRACT_SHAPE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewContractShapeRuntime.ts"
ACTION_META_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewActionMetaRuntime.ts"
SCENE_IDENTITY_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewSceneIdentityRuntime.ts"
BATCH_ARTIFACT_GLUE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewBatchArtifactGlueRuntime.ts"
ASSIGNEE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewAssigneeRuntime.ts"
VIEW_MODE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewModeRuntime.ts"
PROJECT_METRIC_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewProjectMetricRuntime.ts"
CONTRACT_ACTION_BUTTON_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewContractActionButtonRuntime.ts"
ACTION_GROUPING_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewActionGroupingRuntime.ts"
DISPLAY_COMPUTED_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewDisplayComputedRuntime.ts"
FILTER_COMPUTED_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewFilterComputedRuntime.ts"
LOAD_LIFECYCLE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadLifecycleRuntime.ts"
LOAD_BEGIN_INPUT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadBeginInputRuntime.ts"
LOAD_BEGIN_PHASE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadBeginPhaseRuntime.ts"
LOAD_PREFLIGHT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightRuntime.ts"
LOAD_PREFLIGHT_APPLY_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightApplyRuntime.ts"
LOAD_REQUEST_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestRuntime.ts"
LOAD_REQUEST_GUARD_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestGuardRuntime.ts"
LOAD_REQUEST_PHASE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestPhaseRuntime.ts"
LOAD_SUCCESS_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadSuccessRuntime.ts"
LOAD_SUCCESS_PHASE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadSuccessPhaseRuntime.ts"
LOAD_REQUEST_INPUT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestInputRuntime.ts"
LOAD_SUCCESS_DYNAMIC_INPUT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadSuccessDynamicInputRuntime.ts"
LOAD_CATCH_PHASE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadCatchPhaseRuntime.ts"
LOAD_PREFLIGHT_INPUT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightInputRuntime.ts"
LOAD_REQUEST_BLOCKED_APPLY_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestBlockedApplyRuntime.ts"
LOAD_PREFLIGHT_APPLY_BOUND_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightApplyBoundRuntime.ts"
LOAD_PREFLIGHT_PHASE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadPreflightPhaseRuntime.ts"
LOAD_REQUEST_DYNAMIC_INPUT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadRequestDynamicInputRuntime.ts"
LOAD_SUCCESS_PHASE_INPUT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadSuccessPhaseInputRuntime.ts"
LOAD_MAIN_PHASE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadMainPhaseRuntime.ts"
LOAD_MAIN_PHASE_INPUT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadMainPhaseInputRuntime.ts"
LOAD_MAIN_BOUND_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadMainBoundRuntime.ts"
LOAD_BOUND_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewLoadBoundRuntime.ts"
SECTION_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewSectionRuntime.ts"
TEMPLATE_STATE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewTemplateStateRuntime.ts"
TEMPLATE_INTERACTION_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewTemplateInteractionRuntime.ts"
TEXT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewTextRuntime.ts"
TEMPLATE_UI_STATE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewTemplateUiStateRuntime.ts"
FILTER_UI_STATE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewFilterUiStateRuntime.ts"
PAGE_DISPLAY_STATE_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewPageDisplayStateRuntime.ts"
HUD_ENTRIES_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewHudEntriesRuntime.ts"
HUD_ENTRIES_INPUT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewHudEntriesInputRuntime.ts"
SURFACE_INTENT_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewSurfaceIntentRuntime.ts"
ADVANCED_DISPLAY_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewAdvancedDisplayRuntime.ts"
CONTENT_DISPLAY_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewContentDisplayRuntime.ts"
SURFACE_DISPLAY_RUNTIME = ROOT / "frontend/apps/web/src/app/assemblers/action/useActionViewSurfaceDisplayRuntime.ts"
REPORT_JSON = ROOT / "artifacts/backend/frontend_actionview_scene_specialcase_guard_report.json"
REPORT_MD = ROOT / "docs/ops/audit/frontend_actionview_scene_specialcase_guard_report.md"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _check_required_tokens(path: Path, text: str, tokens: List[str], errors: List[str]) -> None:
    if not text:
        errors.append(f"missing file: {path.relative_to(ROOT)}")
        return
    for token in tokens:
        if token not in text:
            errors.append(f"missing required token in {path.relative_to(ROOT)}: {token}")


def _check_forbidden_tokens(path: Path, text: str, tokens: List[str], errors: List[str]) -> None:
    if not text:
        return
    for token in tokens:
        if token in text:
            errors.append(f"forbidden token present in {path.relative_to(ROOT)}: {token}")


def main() -> int:
    errors: List[str] = []

    action_view_text = _read(ACTION_VIEW)
    action_runtime_text = _read(ACTION_RUNTIME)
    batch_runtime_text = _read(BATCH_RUNTIME)
    page_model_text = _read(PAGE_MODEL)

    required_by_file: Dict[Path, List[str]] = {
        ACTION_VIEW: [
            "useActionViewActionRuntime({",
            "useActionViewBatchRuntime({",
            "useActionViewSelectionRuntime({",
            "useActionViewTriggerRuntime({",
            "useActionViewGroupedRowsRuntime({",
            "useActionViewRoutePresetRuntime({",
            "useActionViewFilterGroupRuntime({",
            "useActionViewHeaderRuntime({",
            "useActionViewNavigationRuntime({",
            "useActionViewRequestContextRuntime({",
            "useActionViewScopedMetricsRuntime({",
            "useActionViewContractShapeRuntime({",
            "useActionViewActionMetaRuntime({",
            "useActionViewSceneIdentityRuntime()",
            "useActionViewBatchArtifactGlueRuntime({",
            "useActionViewAssigneeRuntime({",
            "useActionViewModeRuntime({",
            "useActionViewProjectMetricRuntime()",
            "useActionViewContractActionButtonRuntime({",
            "useActionViewActionGroupingRuntime()",
            "useActionViewDisplayComputedRuntime({",
            "useActionViewFilterComputedRuntime({",
            "useActionViewLoadLifecycleRuntime()",
            "useActionViewLoadBeginInputRuntime({",
            "useActionViewLoadBeginPhaseRuntime({",
            "useActionViewLoadPreflightRuntime()",
            "useActionViewLoadPreflightApplyRuntime()",
            "useActionViewLoadPreflightApplyBoundRuntime({",
            "useActionViewLoadPreflightInputRuntime({",
            "useActionViewLoadPreflightPhaseRuntime({",
            "useActionViewLoadRequestRuntime()",
            "useActionViewLoadRequestGuardRuntime()",
            "useActionViewLoadRequestBlockedApplyRuntime({",
            "useActionViewLoadRequestPhaseRuntime()",
            "useActionViewLoadRequestInputRuntime({",
            "useActionViewLoadRequestDynamicInputRuntime()",
            "useActionViewLoadMainPhaseRuntime()",
            "useActionViewLoadMainPhaseInputRuntime({",
            "useActionViewLoadMainBoundRuntime({",
            "useActionViewLoadBoundRuntime({",
            "useActionViewSectionRuntime({",
            "useActionViewTemplateStateRuntime({",
            "useActionViewTemplateInteractionRuntime({",
            "useActionViewTextRuntime({",
            "useActionViewTemplateUiStateRuntime()",
            "useActionViewFilterUiStateRuntime()",
            "useActionViewPageDisplayStateRuntime({",
            "useActionViewHudEntriesRuntime({",
            "useActionViewHudEntriesInputRuntime({",
            "useActionViewSurfaceIntentRuntime({",
            "useActionViewAdvancedDisplayRuntime({",
            "useActionViewContentDisplayRuntime({",
            "useActionViewSurfaceDisplayRuntime({",
            "useActionViewLoadSuccessRuntime()",
            "useActionViewLoadSuccessPhaseRuntime({",
            "useActionViewLoadSuccessDynamicInputRuntime({",
            "useActionViewLoadSuccessPhaseInputRuntime()",
            "useActionViewLoadCatchPhaseRuntime({",
            "useActionPageModel({",
            "vm.sections.",
            "vm.content.kind",
            "handleBatchAction",
            "runContractAction",
        ],
        ACTION_RUNTIME: [
            "export function useActionViewActionRuntime",
            "async function runContractAction",
            "resolveExecIds",
            "resolveRunIds",
            "buildButtonRequest",
            "resolveCounters",
            "shouldNavigate",
            "resolveDoneMessage",
        ],
        BATCH_RUNTIME: [
            "export function useActionViewBatchRuntime",
            "async function handleBatchAction",
            "async function handleBatchAssign",
            "function handleBatchExport",
            "function handleDownloadFailedCsv",
            "async function handleLoadMoreFailures",
            "resolveBatchActionTargetModel({",
            "resolveBatchAssignGuardDecision({",
            "resolveBatchExportGuardDecision({",
            "resolveLoadMoreFailuresGuardPlan({",
        ],
        PAGE_MODEL: [
            "export function useActionPageModel",
            "const vm = computed<ActionPageVM>",
            "sections:",
            "content:",
        ],
        SELECTION_RUNTIME: [
            "export function useActionViewSelectionRuntime",
            "function clearSelection",
            "function handleAssigneeChange",
            "function handleToggleSelection",
            "function handleToggleSelectionAll",
            "function buildIfMatchMap",
            "function buildIdempotencyKey",
        ],
        TRIGGER_RUNTIME: [
            "export function useActionViewTriggerRuntime",
            "function handleSearch",
            "function handleSort",
            "function handleFilter",
            "resolveSearchTriggerPlan({",
            "resolveSortTriggerPlan({",
            "resolveFilterTriggerPlan({",
        ],
        GROUPED_ROWS_RUNTIME: [
            "export function useActionViewGroupedRowsRuntime",
            "async function handleGroupedRowsPageChange",
            "async function hydrateGroupedRowsByOffset",
            "function normalizeGroupedRouteState",
            "resolveGroupedRowsPageChangeTarget({",
            "resolveGroupedRowsHydrateCandidates(",
            "resolveGroupedRouteSyncPlan({",
        ],
        ROUTE_PRESET_RUNTIME: [
            "export function useActionViewRoutePresetRuntime",
            "function applyRoutePreset",
            "function clearRoutePreset",
            "function applyRoutePatchAndReload",
            "function syncRouteListState",
            "function syncRouteStateAndReload",
            "function restartLoadWithRouteSync",
            "resolveActionViewRouteSnapshot(",
            "buildActionViewSyncedRouteQuery(",
        ],
        FILTER_GROUP_RUNTIME: [
            "export function useActionViewFilterGroupRuntime",
            "function applyContractFilter",
            "function applySavedFilter",
            "function clearContractFilter",
            "function clearSavedFilter",
            "function applyGroupBy",
            "function clearGroupBy",
            "resolveContractFilterApplyState({",
            "resolveSavedFilterApplyState({",
            "resolveGroupByApplyState({",
        ],
        HEADER_RUNTIME: [
            "export function useActionViewHeaderRuntime",
            "function reload",
            "function openFocusAction",
            "async function executeHeaderAction",
            "resolveReloadTriggerPlan",
            "resolveFocusActionPushState",
            "executePageContractAction",
        ],
        NAVIGATION_RUNTIME: [
            "export function useActionViewNavigationRuntime",
            "function resolveWorkspaceContextQuery",
            "function resolveCarryQuery",
            "function resolveWorkbenchQuery",
            "function handleRowClick",
            "buildActionViewRowClickTarget({",
            "resolveRowClickPushState({",
        ],
        REQUEST_CONTEXT_RUNTIME: [
            "export function useActionViewRequestContextRuntime",
            "function resolveContractFilterDomain",
            "function resolveSavedFilterDomain",
            "function resolveEffectiveFilterDomain",
            "function resolveEffectiveRequestContext",
            "function mergeContext",
            "function mergeActiveFilterDomain",
        ],
        SCOPED_METRICS_RUNTIME: [
            "export function useActionViewScopedMetricsRuntime",
            "async function fetchScopedTotal",
            "async function fetchProjectScopeMetrics",
            "readTotalFromListResult",
        ],
        CONTRACT_SHAPE_RUNTIME: [
            "export function useActionViewContractShapeRuntime",
            "function extractColumnsFromContract",
            "function extractKanbanFields",
            "function extractAdvancedViewFields",
            "function advancedRowTitle",
            "function advancedRowMeta",
            "function buildGroupKey",
            "function resolveModelFromContract",
        ],
        ACTION_META_RUNTIME: [
            "export function useActionViewActionMetaRuntime",
            "function getActionType",
            "function isClientAction",
            "function isUrlAction",
            "function normalizeUrlTarget",
            "function isShellRoute",
            "function resolveNavigationUrl",
            "function isPortalPath",
            "function resolveActionUrl",
            "async function redirectUrlAction",
            "function isWindowAction",
        ],
        SCENE_IDENTITY_RUNTIME: [
            "export function useActionViewSceneIdentityRuntime",
            "function resolveSceneCode",
            "function resolveNodeSceneKey",
            "function findMenuNode",
        ],
        BATCH_ARTIFACT_GLUE_RUNTIME: [
            "export function useActionViewBatchArtifactGlueRuntime",
            "function downloadCsvBase64",
            "function applyBatchFailureArtifacts",
            "function handleBatchDetailAction",
        ],
        ASSIGNEE_RUNTIME: [
            "export function useActionViewAssigneeRuntime",
            "async function loadAssigneeOptions",
            "resolveAssigneeOptionsLoadGuard",
            "resolveAssigneePermissionWarningMessage",
        ],
        VIEW_MODE_RUNTIME: [
            "export function useActionViewModeRuntime",
            "function viewModeLabel",
            "function switchViewMode",
            "resolveActionViewModeLabel",
        ],
        PROJECT_METRIC_RUNTIME: [
            "export function useActionViewProjectMetricRuntime",
            "function resolveProjectStateCell",
            "function resolveProjectAmount",
            "function isCompletedState",
            "function resolveDefaultSort",
        ],
        CONTRACT_ACTION_BUTTON_RUNTIME: [
            "export function useActionViewContractActionButtonRuntime",
            "function toContractActionButton",
            "normalizeSceneActionProtocol",
            "detectObjectMethodFromActionKey",
        ],
        ACTION_GROUPING_RUNTIME: [
            "export function useActionViewActionGroupingRuntime",
            "function resolveContractActionGroups",
            "function resolveContractPrimaryActions",
            "function resolveContractOverflowActions",
            "function resolveContractOverflowActionGroups",
        ],
        DISPLAY_COMPUTED_RUNTIME: [
            "export function useActionViewDisplayComputedRuntime",
            "const sortOptions = computed(() =>",
            "const subtitle = computed(",
            "const statusLabel = computed(() =>",
            "const pageStatus = computed<'loading' | 'ok' | 'empty' | 'error'>(",
            "const recordCount = computed(() =>",
        ],
        FILTER_COMPUTED_RUNTIME: [
            "export function useActionViewFilterComputedRuntime",
            "const contractFilterChips = computed(() =>",
            "const filterPrimaryBudget = computed(() =>",
            "const contractSavedFilterChips = computed(() =>",
            "const contractGroupByChips = computed(() =>",
            "const activeGroupByLabel = computed(() =>",
        ],
        LOAD_LIFECYCLE_RUNTIME: [
            "export function useActionViewLoadLifecycleRuntime",
            "function beginActionViewLoad",
            "function handleActionViewLoadCatch",
            "resolveLoadMissingActionApplyState",
            "resolveLoadCatchState",
        ],
        LOAD_PREFLIGHT_RUNTIME: [
            "export function useActionViewLoadPreflightRuntime",
            "async function executeLoadPreflight",
            "resolveLoadMissingViewTypeApplyState",
            "resolveLoadMissingResolvedModelApplyState",
            "resolveLoadPreflightSortValue",
        ],
        LOAD_PREFLIGHT_APPLY_RUNTIME: [
            "export function useActionViewLoadPreflightApplyRuntime",
            "function applyLoadPreflightContinueState",
            "function applyLoadPreflightBlockedState",
        ],
        LOAD_REQUEST_RUNTIME: [
            "export function useActionViewLoadRequestRuntime",
            "async function executeLoadDataRequest",
            "resolveLoadRequestPayloadState",
            "resolveLoadDomainStateApply",
            "resolveLoadContextStateApply",
        ],
        LOAD_REQUEST_GUARD_RUNTIME: [
            "export function useActionViewLoadRequestGuardRuntime",
            "function applyLoadRequestBlockedState",
        ],
        LOAD_REQUEST_PHASE_RUNTIME: [
            "export function useActionViewLoadRequestPhaseRuntime",
            "async function executeLoadRequestPhase",
            "executeLoadDataRequest",
            "applyLoadRequestBlockedState",
        ],
        LOAD_REQUEST_INPUT_RUNTIME: [
            "export function useActionViewLoadRequestInputRuntime",
            "function buildLoadRequestInput",
            "staticInput",
        ],
        LOAD_REQUEST_DYNAMIC_INPUT_RUNTIME: [
            "export function useActionViewLoadRequestDynamicInputRuntime",
            "function buildLoadRequestDynamicInput",
            "metaDomainRaw",
            "metaContextRaw",
        ],
        LOAD_MAIN_PHASE_RUNTIME: [
            "export function useActionViewLoadMainPhaseRuntime",
            "async function executeLoadMainPhase",
            "executeLoadPreflightPhase",
            "executeLoadRequestPhase",
            "executeLoadSuccessPhase",
            "executeLoadCatchPhase",
        ],
        LOAD_MAIN_PHASE_INPUT_RUNTIME: [
            "export function useActionViewLoadMainPhaseInputRuntime",
            "function buildLoadMainPhaseInput",
            "staticInput",
        ],
        LOAD_MAIN_BOUND_RUNTIME: [
            "export function useActionViewLoadMainBoundRuntime",
            "async function executeLoadMainBound",
            "buildLoadMainPhaseInput",
            "executeLoadMainPhase",
        ],
        LOAD_BOUND_RUNTIME: [
            "export function useActionViewLoadBoundRuntime",
            "async function executeLoad",
            "executeLoadBeginPhase",
            "executeLoadMainBound",
        ],
        SECTION_RUNTIME: [
            "export function useActionViewSectionRuntime",
            "function isSectionVisible",
            "function getSectionStyle",
            "pageSectionEnabled",
            "pageSectionTagIs",
            "pageSectionStyle",
        ],
        TEMPLATE_STATE_RUNTIME: [
            "export function useActionViewTemplateStateRuntime",
            "const isUiBusy = computed",
            "function isViewModeDisabled",
            "function isBusyDisabled",
            "function isContractActionDisabled",
        ],
        TEMPLATE_INTERACTION_RUNTIME: [
            "export function useActionViewTemplateInteractionRuntime",
            "function toggleMoreContractFilters",
            "function toggleMoreSavedFilters",
            "function toggleMoreGroupBy",
            "function toggleMoreContractActions",
        ],
        TEXT_RUNTIME: [
            "export function useActionViewTextRuntime",
            "function t(",
            "pageText",
        ],
        TEMPLATE_UI_STATE_RUNTIME: [
            "export function useActionViewTemplateUiStateRuntime",
            "const showMoreContractActions = ref(false)",
            "const showMoreContractFilters = ref(false)",
            "const showMoreSavedFilters = ref(false)",
        ],
        FILTER_UI_STATE_RUNTIME: [
            "export function useActionViewFilterUiStateRuntime",
            "const activeContractFilterKey = ref('')",
            "const activeSavedFilterKey = ref('')",
            "const contractLimit = ref(40)",
            "const preferredViewMode = ref('')",
        ],
        PAGE_DISPLAY_STATE_RUNTIME: [
            "export function useActionViewPageDisplayStateRuntime",
            "const pageTitle = computed",
            "const emptyReasonText = computed",
            "const showHud = computed",
            "errorMessage",
        ],
        HUD_ENTRIES_RUNTIME: [
            "export function useActionViewHudEntriesRuntime",
            "function buildHudEntries",
            "buildHudEntriesInput",
            "contract_actions",
            "route",
        ],
        HUD_ENTRIES_INPUT_RUNTIME: [
            "export function useActionViewHudEntriesInputRuntime",
            "function buildHudEntriesInput",
            "staticInput",
        ],
        SURFACE_INTENT_RUNTIME: [
            "export function useActionViewSurfaceIntentRuntime",
            "const contractSurfaceIntent = computed",
            "const surfaceIntent = computed",
            "resolveActionViewSurfaceIntent",
            "strictSurfaceContract",
        ],
        ADVANCED_DISPLAY_RUNTIME: [
            "export function useActionViewAdvancedDisplayRuntime",
            "const advancedViewTitle = computed",
            "const advancedViewHint = computed",
            "resolveActionViewAdvancedTitle",
            "resolveActionViewAdvancedHint",
        ],
        CONTENT_DISPLAY_RUNTIME: [
            "export function useActionViewContentDisplayRuntime",
            "const ledgerOverviewItems = computed",
            "const listSummaryItems = computed",
            "const kanbanTitleField = computed",
            "mapProjectionMetricItems",
        ],
        SURFACE_DISPLAY_RUNTIME: [
            "export function useActionViewSurfaceDisplayRuntime",
            "const sortLabel = computed",
            "const surfaceKind = computed",
            "resolveActionViewSurfaceKind",
            "strictSurfaceContract",
        ],
        LOAD_SUCCESS_RUNTIME: [
            "export function useActionViewLoadSuccessRuntime",
            "async function applyLoadSuccess",
            "resolveLoadSuccessProjectScopeApplyState",
            "resolveLoadFinalizeApplyState",
            "resolveLoadTraceApplyState",
        ],
        LOAD_SUCCESS_PHASE_RUNTIME: [
            "export function useActionViewLoadSuccessPhaseRuntime",
            "async function executeLoadSuccessPhase",
            "applyLoadSuccess",
        ],
        LOAD_SUCCESS_DYNAMIC_INPUT_RUNTIME: [
            "export function useActionViewLoadSuccessDynamicInputRuntime",
            "function buildLoadSuccessDynamicInput",
            "staticInput",
        ],
        LOAD_SUCCESS_PHASE_INPUT_RUNTIME: [
            "export function useActionViewLoadSuccessPhaseInputRuntime",
            "function buildLoadSuccessPhaseInput",
            "requestContextRaw",
        ],
        LOAD_CATCH_PHASE_RUNTIME: [
            "export function useActionViewLoadCatchPhaseRuntime",
            "function executeLoadCatchPhase",
            "handleActionViewLoadCatch",
        ],
        LOAD_PREFLIGHT_INPUT_RUNTIME: [
            "export function useActionViewLoadPreflightInputRuntime",
            "function buildLoadPreflightInput",
            "staticInput",
        ],
        LOAD_PREFLIGHT_APPLY_BOUND_RUNTIME: [
            "export function useActionViewLoadPreflightApplyBoundRuntime",
            "function applyLoadPreflightContinue",
            "function applyLoadPreflightBlocked",
            "applyLoadPreflightContinueState",
            "applyLoadPreflightBlockedState",
        ],
        LOAD_PREFLIGHT_PHASE_RUNTIME: [
            "export function useActionViewLoadPreflightPhaseRuntime",
            "async function executeLoadPreflightPhase",
            "executeLoadPreflight",
            "buildLoadPreflightInput",
            "applyLoadPreflightBlocked",
            "applyLoadPreflightContinue",
        ],
        LOAD_REQUEST_BLOCKED_APPLY_RUNTIME: [
            "export function useActionViewLoadRequestBlockedApplyRuntime",
            "function applyLoadRequestBlocked",
            "applyLoadRequestBlockedState",
        ],
        LOAD_BEGIN_INPUT_RUNTIME: [
            "export function useActionViewLoadBeginInputRuntime",
            "function buildLoadBeginInput",
            "staticInput",
        ],
        LOAD_BEGIN_PHASE_RUNTIME: [
            "export function useActionViewLoadBeginPhaseRuntime",
            "function executeLoadBeginPhase",
            "beginActionViewLoad",
            "buildLoadBeginInput",
        ],
    }

    forbidden_by_file: Dict[Path, List[str]] = {
        ACTION_VIEW: [
            "handleBatchActionLegacy",
            "handleBatchAssignLegacy",
            "handleBatchExportLegacy",
            "exportByBackendLegacy",
            "handleDownloadFailedCsvLegacy",
            "handleLoadMoreFailuresLegacy",
            "resolveClearSelectionState();",
            "resolveAssigneeSelectionState({",
            "resolveToggleSelectionState({",
            "resolveToggleSelectionAllState({",
            "resolveIfMatchMapState({",
            "resolveBatchIdempotencyPayload({",
            "resolveBatchIdempotencyKey({",
            "resolveSearchTriggerPlan({",
            "resolveSortTriggerPlan({",
            "resolveFilterTriggerPlan({",
            "resolveTriggerGroupWindowOffset({",
            "function handleGroupedRowsPageChange(",
            "function hydrateGroupedRowsByOffset(",
            "function normalizeGroupedRouteState(",
            "function applyRoutePreset(",
            "function clearRoutePreset(",
            "function applyRoutePatchAndReload(",
            "function syncRouteListState(",
            "function syncRouteStateAndReload(",
            "function restartLoadWithRouteSync(",
            "function applyContractFilter(",
            "function applySavedFilter(",
            "function clearContractFilter(",
            "function clearSavedFilter(",
            "function applyGroupBy(",
            "function clearGroupBy(",
            "function applyGroupSharedState(",
            "function reload(",
            "function openFocusAction(",
            "async function executeHeaderAction(",
            "function resolveWorkspaceContextQuery(",
            "function resolveCarryQuery(",
            "function resolveWorkbenchQuery(",
            "function handleRowClick(",
            "function resolveContractFilterDomain(",
            "function resolveContractFilterDomainRaw(",
            "function resolveContractFilterContext(",
            "function resolveContractFilterContextRaw(",
            "function resolveSavedFilterDomain(",
            "function resolveSavedFilterDomainRaw(",
            "function resolveSavedFilterContext(",
            "function resolveSavedFilterContextRaw(",
            "function resolveEffectiveFilterDomain(",
            "function resolveEffectiveFilterDomainRaw(",
            "function resolveEffectiveFilterContext(",
            "function resolveEffectiveFilterContextRaw(",
            "function resolveGroupByContext(",
            "function resolveGroupByContextRaw(",
            "function resolveEffectiveRequestContext(",
            "function resolveEffectiveRequestContextRaw(",
            "function mergeContext(",
            "function mergeActiveFilterDomain(",
            "async function fetchScopedTotal(",
            "async function fetchProjectScopeMetrics(",
            "function extractColumnsFromContract(",
            "function extractKanbanFields(",
            "function extractAdvancedViewFields(",
            "function advancedRowTitle(",
            "function advancedRowMeta(",
            "function buildGroupKey(",
            "function resolveModelFromContract(",
            "function getActionType(",
            "function isClientAction(",
            "function isUrlAction(",
            "function normalizeUrlTarget(",
            "function isShellRoute(",
            "function resolveNavigationUrl(",
            "function isPortalPath(",
            "function resolveActionUrl(",
            "function redirectUrlAction(",
            "function isWindowAction(",
            "type NavNodeWithScene =",
            "function resolveSceneCode(",
            "function resolveNodeSceneKey(",
            "function findMenuNode(",
            "function downloadCsvBase64(",
            "function applyBatchFailureArtifacts(",
            "function handleBatchDetailAction(",
            "async function loadAssigneeOptions(",
            "function viewModeLabel(",
            "function switchViewMode(",
            "function replaceCurrentRouteQuery(",
            "function resolveProjectStateCell(",
            "function resolveProjectAmount(",
            "function isCompletedState(",
            "function resolveDefaultSort(",
            "function toContractActionButton(",
            "const sortOptions = computed(() =>",
            "const subtitle = computed(",
            "const statusLabel = computed(() =>",
            "const pageStatus = computed<'loading' | 'ok' | 'empty' | 'error'>(",
            "const recordCount = computed(() =>",
            "const contractFilterChips = computed<ContractFilterChip[]>(() =>",
            "const filterPrimaryBudget = computed(() =>",
            "const contractSavedFilterChips = computed<ContractSavedFilterChip[]>(() =>",
            "const contractGroupByChips = computed<ContractGroupByChip[]>(() =>",
            "const activeGroupByLabel = computed(() =>",
            "resolveLoadCatchListApplyState({",
            "resolveLoadCatchScopeApplyState({",
            "resolveLoadCatchTraceStatusApplyState({",
            "resolveLoadCatchLatencyApplyState({",
            "const requestPayload = resolveLoadRequestPayloadState({",
            "const result = await listRecordsRaw(requestPayload);",
            "const { contract, meta } = await resolveAction(",
            "const routeSelection = resolveRouteSelectionState({",
            "const accessPolicy = resolveContractAccessPolicy(",
            "const policy = evaluateCapabilityPolicy({",
            "const preflightResult = await executeLoadPreflight({",
            "if (preflightResult.kind === 'redirect') {",
            "if (preflightResult.kind === 'handled') {",
            "if (preflightResult.kind === 'blocked') {",
            "const beginState = beginActionViewLoad({",
            "const loadMainPhaseResult = await executeLoadMainPhase({",
            "const beginState = executeLoadBeginPhase({ input: {} });",
            "const loadMainPhaseResult = await executeLoadMainPhase(",
            "const pageSectionEnabled = pageContract.sectionEnabled;",
            "const pageSectionTagIs = pageContract.sectionTagIs;",
            "const pageSectionStyle = pageContract.sectionStyle;",
            "status === 'loading' || batchBusy",
            "showMoreContractFilters = !showMoreContractFilters",
            "showMoreSavedFilters = !showMoreSavedFilters",
            "showMoreGroupBy = !showMoreGroupBy",
            "showMoreContractActions = !showMoreContractActions",
            "pageText(",
            "const showMoreContractActions = ref(false);",
            "const showMoreContractFilters = ref(false);",
            "const showMoreSavedFilters = ref(false);",
            "const activeContractFilterKey = ref('');",
            "const activeSavedFilterKey = ref('');",
            "const contractLimit = ref(40);",
            "const preferredViewMode = ref('');",
            "const pageTitle = computed(() => {",
            "const emptyReasonText = computed(() => {",
            "const showHud = computed(() => isHudEnabled(route));",
            "const hudEntries = computed(() => [",
            "useActionViewHudEntriesRuntime({\n  staticInput:",
            "const contractSurfaceIntent = computed<SurfaceIntentContract>(() => {",
            "const surfaceIntent = computed<SurfaceIntent>(() => {",
            "const advancedViewTitle = computed(() => {",
            "const advancedViewHint = computed(() => {",
            "const ledgerOverviewItems = computed(() => {",
            "const listSummaryItems = computed(() => {",
            "const kanbanTitleField = computed(() => {",
            "const sortLabel = computed(() => sortValue.value || 'id asc');",
            "const surfaceKind = computed<ActionViewSurfaceKind>(() => {",
            "setError(new Error(preflightResult.message), preflightResult.message);",
            "status.value = deriveListStatus(preflightResult.statusInput);",
            "applyLoadPreflightBlockedState({",
            "applyLoadPreflightContinueState({",
            "setError(new Error(loadRequestResult.message), loadRequestResult.message);",
            "status.value = deriveListStatus(loadRequestResult.statusInput);",
            "const loadRequestResult = await executeLoadDataRequest({",
            "await applyLoadSuccess({",
            "requestInput: {",
            "dynamicInput: {",
            "handleActionViewLoadCatch({",
            "resolveActionViewGroupPagingState({",
            "resolveLoadGroupRouteSyncPlan({",
            "resolveLoadRouteResetApplyState({",
            "resolveLoadRouteSyncApplyState({",
            "resolveLoadFinalizeApplyState({",
            "resolveLoadTraceApplyState({",
            "const CORE_SCENES = new Set(",
            "sceneKey.value === 'projects.list'",
            "sceneKey.value === 'risk.center'",
            "includesAnyKeyword(",
            "keywordList(",
            "surface_kind_keywords_",
            "group_keywords_",
        ],
    }

    file_text_map: Dict[Path, str] = {
        ACTION_VIEW: action_view_text,
        ACTION_RUNTIME: action_runtime_text,
        BATCH_RUNTIME: batch_runtime_text,
        PAGE_MODEL: page_model_text,
        SELECTION_RUNTIME: _read(SELECTION_RUNTIME),
        TRIGGER_RUNTIME: _read(TRIGGER_RUNTIME),
        GROUPED_ROWS_RUNTIME: _read(GROUPED_ROWS_RUNTIME),
        ROUTE_PRESET_RUNTIME: _read(ROUTE_PRESET_RUNTIME),
        FILTER_GROUP_RUNTIME: _read(FILTER_GROUP_RUNTIME),
        HEADER_RUNTIME: _read(HEADER_RUNTIME),
        NAVIGATION_RUNTIME: _read(NAVIGATION_RUNTIME),
        REQUEST_CONTEXT_RUNTIME: _read(REQUEST_CONTEXT_RUNTIME),
        SCOPED_METRICS_RUNTIME: _read(SCOPED_METRICS_RUNTIME),
        CONTRACT_SHAPE_RUNTIME: _read(CONTRACT_SHAPE_RUNTIME),
        ACTION_META_RUNTIME: _read(ACTION_META_RUNTIME),
        SCENE_IDENTITY_RUNTIME: _read(SCENE_IDENTITY_RUNTIME),
        BATCH_ARTIFACT_GLUE_RUNTIME: _read(BATCH_ARTIFACT_GLUE_RUNTIME),
        ASSIGNEE_RUNTIME: _read(ASSIGNEE_RUNTIME),
        VIEW_MODE_RUNTIME: _read(VIEW_MODE_RUNTIME),
        PROJECT_METRIC_RUNTIME: _read(PROJECT_METRIC_RUNTIME),
        CONTRACT_ACTION_BUTTON_RUNTIME: _read(CONTRACT_ACTION_BUTTON_RUNTIME),
        ACTION_GROUPING_RUNTIME: _read(ACTION_GROUPING_RUNTIME),
        DISPLAY_COMPUTED_RUNTIME: _read(DISPLAY_COMPUTED_RUNTIME),
        FILTER_COMPUTED_RUNTIME: _read(FILTER_COMPUTED_RUNTIME),
        LOAD_LIFECYCLE_RUNTIME: _read(LOAD_LIFECYCLE_RUNTIME),
        LOAD_BEGIN_INPUT_RUNTIME: _read(LOAD_BEGIN_INPUT_RUNTIME),
        LOAD_BEGIN_PHASE_RUNTIME: _read(LOAD_BEGIN_PHASE_RUNTIME),
        LOAD_PREFLIGHT_RUNTIME: _read(LOAD_PREFLIGHT_RUNTIME),
        LOAD_PREFLIGHT_APPLY_RUNTIME: _read(LOAD_PREFLIGHT_APPLY_RUNTIME),
        LOAD_REQUEST_RUNTIME: _read(LOAD_REQUEST_RUNTIME),
        LOAD_REQUEST_GUARD_RUNTIME: _read(LOAD_REQUEST_GUARD_RUNTIME),
        LOAD_REQUEST_PHASE_RUNTIME: _read(LOAD_REQUEST_PHASE_RUNTIME),
        LOAD_REQUEST_INPUT_RUNTIME: _read(LOAD_REQUEST_INPUT_RUNTIME),
        LOAD_SUCCESS_RUNTIME: _read(LOAD_SUCCESS_RUNTIME),
        LOAD_SUCCESS_PHASE_RUNTIME: _read(LOAD_SUCCESS_PHASE_RUNTIME),
        LOAD_SUCCESS_DYNAMIC_INPUT_RUNTIME: _read(LOAD_SUCCESS_DYNAMIC_INPUT_RUNTIME),
        LOAD_CATCH_PHASE_RUNTIME: _read(LOAD_CATCH_PHASE_RUNTIME),
        LOAD_PREFLIGHT_INPUT_RUNTIME: _read(LOAD_PREFLIGHT_INPUT_RUNTIME),
        LOAD_PREFLIGHT_APPLY_BOUND_RUNTIME: _read(LOAD_PREFLIGHT_APPLY_BOUND_RUNTIME),
        LOAD_PREFLIGHT_PHASE_RUNTIME: _read(LOAD_PREFLIGHT_PHASE_RUNTIME),
        LOAD_REQUEST_DYNAMIC_INPUT_RUNTIME: _read(LOAD_REQUEST_DYNAMIC_INPUT_RUNTIME),
        LOAD_SUCCESS_PHASE_INPUT_RUNTIME: _read(LOAD_SUCCESS_PHASE_INPUT_RUNTIME),
        LOAD_MAIN_PHASE_RUNTIME: _read(LOAD_MAIN_PHASE_RUNTIME),
        LOAD_MAIN_PHASE_INPUT_RUNTIME: _read(LOAD_MAIN_PHASE_INPUT_RUNTIME),
        LOAD_MAIN_BOUND_RUNTIME: _read(LOAD_MAIN_BOUND_RUNTIME),
        LOAD_BOUND_RUNTIME: _read(LOAD_BOUND_RUNTIME),
        SECTION_RUNTIME: _read(SECTION_RUNTIME),
        TEMPLATE_STATE_RUNTIME: _read(TEMPLATE_STATE_RUNTIME),
        TEMPLATE_INTERACTION_RUNTIME: _read(TEMPLATE_INTERACTION_RUNTIME),
        TEXT_RUNTIME: _read(TEXT_RUNTIME),
        TEMPLATE_UI_STATE_RUNTIME: _read(TEMPLATE_UI_STATE_RUNTIME),
        FILTER_UI_STATE_RUNTIME: _read(FILTER_UI_STATE_RUNTIME),
        PAGE_DISPLAY_STATE_RUNTIME: _read(PAGE_DISPLAY_STATE_RUNTIME),
        HUD_ENTRIES_RUNTIME: _read(HUD_ENTRIES_RUNTIME),
        HUD_ENTRIES_INPUT_RUNTIME: _read(HUD_ENTRIES_INPUT_RUNTIME),
        SURFACE_INTENT_RUNTIME: _read(SURFACE_INTENT_RUNTIME),
        ADVANCED_DISPLAY_RUNTIME: _read(ADVANCED_DISPLAY_RUNTIME),
        CONTENT_DISPLAY_RUNTIME: _read(CONTENT_DISPLAY_RUNTIME),
        SURFACE_DISPLAY_RUNTIME: _read(SURFACE_DISPLAY_RUNTIME),
        LOAD_REQUEST_BLOCKED_APPLY_RUNTIME: _read(LOAD_REQUEST_BLOCKED_APPLY_RUNTIME),
    }

    for path, tokens in required_by_file.items():
        _check_required_tokens(path, file_text_map.get(path, ""), tokens, errors)

    for path, tokens in forbidden_by_file.items():
        _check_forbidden_tokens(path, file_text_map.get(path, ""), tokens, errors)

    payload = {
        "ok": not errors,
        "check": "verify.frontend.actionview.scene_specialcase.guard",
        "files": [str(path.relative_to(ROOT)) for path in file_text_map],
        "errors": errors,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Frontend ActionView Scene Specialcase Guard Report",
        "",
        f"- ok: {str(payload['ok']).lower()}",
        f"- check: {payload['check']}",
        "- files:",
    ]
    for path in payload["files"]:
        lines.append(f"  - {path}")
    if errors:
        lines.append("- errors:")
        for err in errors:
            lines.append(f"  - {err}")
    else:
        lines.append("- errors: []")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if errors:
        print("[verify.frontend.actionview.scene_specialcase.guard] FAIL")
        for err in errors:
            print(f" - {err}")
        return 2
    print("[verify.frontend.actionview.scene_specialcase.guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
