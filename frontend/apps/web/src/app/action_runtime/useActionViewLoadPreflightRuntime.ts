type Dict = Record<string, unknown>;

type ExecuteLoadPreflightOptions = {
  sessionMenuTree: unknown;
  actionId: number;
  actionMeta: Dict | null;
  routeQueryMap: Dict;
  routeViewModeRaw: unknown;
  routeFilterRaw: unknown;
  routeSavedFilterRaw: unknown;
  routeGroupByRaw: unknown;
  sceneReadyDefaultSortRaw: unknown;
  sceneDefaultSortRaw: unknown;
  sessionCapabilities: unknown;
  currentSortRaw: string;
  activeContractFilterKey: string;
  activeSavedFilterKey: string;
  activeGroupByField: string;
  contractSavedFilterChips: Array<Record<string, unknown>>;
  contractGroupByChips: Array<Record<string, unknown>>;
  currentPreferredViewModeRaw: string;
  buildWorkbenchRouteTarget: (input: { query: Dict }) => unknown;
  resolveWorkbenchQuery: (reason: string, payload?: { public?: Dict; diag?: Dict }) => Dict;
  buildModelFormRouteTarget: (input: { model: string; id: string; query: Dict }) => unknown;
  resolveCarryQuery: (extra?: Dict) => Dict;
  extractActionResId: (input: unknown) => number | null;
  resolveAction: (menuTree: unknown, actionId: number, actionMeta: Dict | null) => Promise<{ contract: unknown; meta?: Dict | null }>;
  setActionMeta: (meta: Dict) => void;
  resolveContractViewMode: (contract: unknown, viewType: unknown) => string;
  resolveActionViewType: (meta: unknown, contract: unknown) => string;
  resolvePreferredActionViewMode: (input: Dict) => string;
  resolveRouteSelectionState: (input: Dict) => Dict;
  resolveRouteSelectionApplyState: (input: { routeSelection: Dict }) => {
    activeContractFilterKey: string;
    activeSavedFilterKey: string;
    activeGroupByField: string;
  };
  resolveContractAccessPolicy: (contract: unknown) => { reasonCode?: unknown; mode?: unknown };
  resolveContractReadRight: (contract: unknown) => boolean;
  resolveLoadPreflightContractFlags: (input: Dict) => Dict;
  resolveContractFlagApplyState: (input: { contractFlags: Dict }) => {
    contractReadAllowed: boolean;
    contractWarningCount: number;
    contractDegraded: boolean;
  };
  resolveLoadContractReadRedirectPayload: (input: Dict) => Dict;
  resolveCapabilityMissingRedirectTarget: (input: {
    capabilityMissingCode: string;
    guardPayload: Dict;
    buildWorkbenchRouteTargetFn: (input: { query: Dict }) => unknown;
    resolveWorkbenchQueryFn: (reason: string, payload?: { public?: Dict; diag?: Dict }) => Dict;
  }) => unknown;
  isUrlAction: (meta: unknown, contract: unknown) => boolean;
  redirectUrlAction: (meta: unknown, contract: unknown) => Promise<boolean>;
  extractListOrderFromContract: (contract: unknown) => string;
  resolveLoadPreflightSortValue: (input: Dict) => string;
  resolveLoadPreflightContractLimit: (input: Dict) => number;
  evaluateCapabilityPolicy: (input: { source: unknown; available: unknown }) => { state?: unknown; missing?: unknown };
  resolveLoadCapabilityRedirectPayload: (input: Dict) => Dict;
  resolveModelFromContract: (contract: unknown) => string;
  resolveActionViewResolvedModel: (input: Dict) => string;
  isClientAction: (meta: unknown) => boolean;
  isWindowAction: (meta: unknown) => boolean;
  getActionType: (meta: unknown) => string;
  resolveLoadMissingModelRedirectDecision: (input: Dict) => Dict;
  resolveMissingModelRedirectTarget: (input: {
    missingModelRedirect: Dict;
    buildWorkbenchRouteTargetFn: (input: { query: Dict }) => unknown;
    resolveWorkbenchQueryFn: (reason: string, payload?: { public?: Dict; diag?: Dict }) => Dict;
  }) => unknown;
  resolveLoadFormActionResId: (input: Dict) => number | null;
  resolveLoadMissingContractViewTypeErrorState: () => Dict;
  resolveLoadMissingViewTypeApplyState: (input: { missingViewTypeState: Dict; currentErrorMessage: string }) => {
    message: string;
    statusInput: string;
  };
  resolveLoadMissingResolvedModelErrorState: () => Dict;
  resolveLoadMissingResolvedModelApplyState: (input: { missingModelErrorState: Dict; currentErrorMessage: string }) => {
    message: string;
    statusInput: string;
  };
  capabilityMissingCode: string;
};

export type ExecuteLoadPreflightResult =
  | { kind: 'blocked'; message: string; statusInput: string }
  | { kind: 'redirect'; target: unknown }
  | { kind: 'handled' }
  | {
      kind: 'continue';
      contract: unknown;
      meta: Dict | null;
      typedContract: Dict;
      contractViewType: string;
      preferredViewMode: string;
      activeContractFilterKey: string;
      activeSavedFilterKey: string;
      activeGroupByField: string;
      contractReadAllowed: boolean;
      contractWarningCount: number;
      contractDegraded: boolean;
      contractLimit: number;
      resolvedModel: string;
      setMetaModel: string;
      sortValue: string;
    };

export function useActionViewLoadPreflightRuntime() {
  async function executeLoadPreflight(options: ExecuteLoadPreflightOptions): Promise<ExecuteLoadPreflightResult> {
    const { contract, meta } = await options.resolveAction(options.sessionMenuTree, options.actionId, options.actionMeta);
    const nextMeta = (meta || null) as Dict | null;
    if (nextMeta) {
      options.setActionMeta(nextMeta);
    }

    const contractViewType = options.resolveContractViewMode(contract, options.resolveActionViewType(nextMeta, contract));
    if (!contractViewType) {
      const missingViewTypeState = options.resolveLoadMissingContractViewTypeErrorState();
      const missingViewTypeApplyState = options.resolveLoadMissingViewTypeApplyState({
        missingViewTypeState,
        currentErrorMessage: '',
      });
      return {
        kind: 'blocked',
        message: missingViewTypeApplyState.message,
        statusInput: missingViewTypeApplyState.statusInput,
      };
    }

    const typedContract = (contract || {}) as Dict;
    const preferredViewMode = options.resolvePreferredActionViewMode({
      contractViewTypeRaw: contractViewType,
      metaViewModesRaw: (nextMeta as { view_modes?: unknown } | null)?.view_modes,
      contract: typedContract,
      routeViewModeRaw: options.routeViewModeRaw,
      currentPreferredViewModeRaw: options.currentPreferredViewModeRaw,
    });

    const routeSelection = options.resolveRouteSelectionState({
      routeFilterRaw: options.routeFilterRaw,
      routeSavedFilterRaw: options.routeSavedFilterRaw,
      routeGroupByRaw: options.routeGroupByRaw,
      activeContractFilterKey: options.activeContractFilterKey,
      activeSavedFilterKey: options.activeSavedFilterKey,
      activeGroupByField: options.activeGroupByField,
      contractFiltersRaw: (typedContract.search as Dict | undefined)?.filters,
      savedFilterChips: options.contractSavedFilterChips,
      groupByChips: options.contractGroupByChips,
    });
    const routeSelectionState = options.resolveRouteSelectionApplyState({ routeSelection });

    const accessPolicy = options.resolveContractAccessPolicy(typedContract);
    const contractFlags = options.resolveLoadPreflightContractFlags({
      contractReadAllowedRaw: options.resolveContractReadRight(typedContract),
      warningsRaw: typedContract.warnings,
      degradedRaw: typedContract.degraded,
    });
    const contractFlagState = options.resolveContractFlagApplyState({ contractFlags });

    const contractReadGuardPayload = options.resolveLoadContractReadRedirectPayload({
      contractReadAllowed: contractFlagState.contractReadAllowed,
      reasonCodeRaw: accessPolicy.reasonCode,
      accessModeRaw: accessPolicy.mode,
    });
    const contractReadGuardTarget = options.resolveCapabilityMissingRedirectTarget({
      capabilityMissingCode: options.capabilityMissingCode,
      guardPayload: contractReadGuardPayload,
      buildWorkbenchRouteTargetFn: options.buildWorkbenchRouteTarget,
      resolveWorkbenchQueryFn: options.resolveWorkbenchQuery,
    });
    if (contractReadGuardTarget) {
      return { kind: 'redirect', target: contractReadGuardTarget };
    }

    if (options.isUrlAction(nextMeta, contract)) {
      await options.redirectUrlAction(nextMeta, contract);
      return { kind: 'handled' };
    }

    let sortValue = options.currentSortRaw;
    if (!sortValue) {
      const searchDefaults = (typedContract.search as Dict | undefined)?.defaults as Dict | undefined;
      const viewsTree = (typedContract.views as Dict | undefined)?.tree as Dict | undefined;
      const uiContractViews = (typedContract.ui_contract as Dict | undefined)?.views as Dict | undefined;
      const uiContractTree = uiContractViews?.tree as Dict | undefined;
      const fallbackSort = options.extractListOrderFromContract(contract) || '';
      sortValue = options.resolveLoadPreflightSortValue({
        currentSortRaw: sortValue,
        sceneReadyDefaultSortRaw: options.sceneReadyDefaultSortRaw,
        sceneDefaultSortRaw: options.sceneDefaultSortRaw,
        searchDefaultOrderRaw: searchDefaults?.order,
        viewOrderRaw: viewsTree?.order || uiContractTree?.order,
        metaOrderRaw: '',
        fallbackSortRaw: fallbackSort,
      });
    }

    const searchDefaults = (typedContract.search as Dict | undefined)?.defaults as Dict | undefined;
    const contractLimit = options.resolveLoadPreflightContractLimit({ searchDefaultLimitRaw: searchDefaults?.limit });

    const policy = options.evaluateCapabilityPolicy({ source: nextMeta, available: options.sessionCapabilities });
    const capabilityGuardPayload = options.resolveLoadCapabilityRedirectPayload({
      stateRaw: policy.state,
      missingRaw: policy.missing,
    });
    const capabilityGuardTarget = options.resolveCapabilityMissingRedirectTarget({
      capabilityMissingCode: options.capabilityMissingCode,
      guardPayload: capabilityGuardPayload,
      buildWorkbenchRouteTargetFn: options.buildWorkbenchRouteTarget,
      resolveWorkbenchQueryFn: options.resolveWorkbenchQuery,
    });
    if (capabilityGuardTarget) {
      return { kind: 'redirect', target: capabilityGuardTarget };
    }

    const contractModel = options.resolveModelFromContract(contract);
    const resolvedModel = options.resolveActionViewResolvedModel({
      metaModelRaw: (nextMeta as Dict | null)?.model,
      routeModelRaw: '',
      contractModelRaw: contractModel,
    });
    const setMetaModel = !String((nextMeta as Dict | null)?.model || '').trim() && resolvedModel ? resolvedModel : '';

    const missingModelRedirect = options.resolveLoadMissingModelRedirectDecision({
      resolvedModel,
      isClientAction: options.isClientAction(nextMeta),
      isWindowAction: options.isWindowAction(nextMeta),
      actionTypeRaw: options.getActionType(nextMeta),
      contractDataTypeRaw: (typedContract.data as Dict | undefined)?.type,
      contractUrlRaw: (typedContract.data as Dict | undefined)?.url,
      metaUrlRaw: (nextMeta as Dict | null)?.url,
      noModelCode: 'ACT_NO_MODEL',
      unsupportedCode: 'ACT_UNSUPPORTED_TYPE',
    });
    const missingModelRedirectTarget = options.resolveMissingModelRedirectTarget({
      missingModelRedirect,
      buildWorkbenchRouteTargetFn: options.buildWorkbenchRouteTarget,
      resolveWorkbenchQueryFn: options.resolveWorkbenchQuery,
    });
    if (missingModelRedirectTarget) {
      return { kind: 'redirect', target: missingModelRedirectTarget };
    }
    if (!resolvedModel) {
      const missingModelErrorState = options.resolveLoadMissingResolvedModelErrorState();
      const missingResolvedModelApplyState = options.resolveLoadMissingResolvedModelApplyState({
        missingModelErrorState,
        currentErrorMessage: '',
      });
      return {
        kind: 'blocked',
        message: missingResolvedModelApplyState.message,
        statusInput: missingResolvedModelApplyState.statusInput,
      };
    }

    if (contractViewType === 'form') {
      const actionResId = options.resolveLoadFormActionResId({
        contractRaw: contract,
        routeQueryMapRaw: options.routeQueryMap,
        extractActionResIdFn: options.extractActionResId,
      });
      const target = options.buildModelFormRouteTarget({
        model: resolvedModel,
        id: actionResId ? String(actionResId) : 'new',
        query: options.resolveCarryQuery(),
      });
      return { kind: 'redirect', target };
    }

    return {
      kind: 'continue',
      contract,
      meta: nextMeta,
      typedContract,
      contractViewType,
      preferredViewMode,
      activeContractFilterKey: routeSelectionState.activeContractFilterKey,
      activeSavedFilterKey: routeSelectionState.activeSavedFilterKey,
      activeGroupByField: routeSelectionState.activeGroupByField,
      contractReadAllowed: contractFlagState.contractReadAllowed,
      contractWarningCount: contractFlagState.contractWarningCount,
      contractDegraded: contractFlagState.contractDegraded,
      contractLimit,
      resolvedModel,
      setMetaModel,
      sortValue,
    };
  }

  return {
    executeLoadPreflight,
  };
}
