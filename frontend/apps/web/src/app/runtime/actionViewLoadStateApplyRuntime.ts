type RouteSelectionState = {
  activeContractFilterKey: string;
  activeSavedFilterKey: string;
  activeGroupByField: string;
};

type ContractFlagState = {
  contractReadAllowed: boolean;
  contractWarningCount: number;
  contractDegraded: boolean;
};

type GroupPagingState = {
  effectiveGroupOffset: number;
  groupWindowId: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
};

type ProjectScopeState = {
  projectScopeTotals: Record<string, number>;
  projectScopeMetrics: Record<string, unknown>;
};

type WindowMetricsState = {
  groupWindowCount: number;
  groupWindowStart: number;
  groupWindowEnd: number;
  groupWindowTotal: number;
  groupWindowNextOffset: number;
  groupWindowPrevOffset: number;
};

export function resolveRouteSelectionApplyState(options: {
  routeSelection: RouteSelectionState;
}): RouteSelectionState {
  return {
    activeContractFilterKey: options.routeSelection.activeContractFilterKey,
    activeSavedFilterKey: options.routeSelection.activeSavedFilterKey,
    activeGroupByField: options.routeSelection.activeGroupByField,
  };
}

export function resolveContractFlagApplyState(options: {
  contractFlags: ContractFlagState;
}): ContractFlagState {
  return {
    contractReadAllowed: options.contractFlags.contractReadAllowed,
    contractWarningCount: options.contractFlags.contractWarningCount,
    contractDegraded: options.contractFlags.contractDegraded,
  };
}

export function resolveGroupPagingIdentityApplyState(options: {
  pagingState: GroupPagingState;
  responseGroupFingerprint: string;
}): {
  groupWindowOffset: number;
  groupWindowId: string;
  groupQueryFingerprint: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
} {
  return {
    groupWindowOffset: options.pagingState.effectiveGroupOffset,
    groupWindowId: options.pagingState.groupWindowId,
    groupQueryFingerprint: options.responseGroupFingerprint,
    groupWindowDigest: options.pagingState.groupWindowDigest,
    groupWindowIdentityKey: options.pagingState.groupWindowIdentityKey,
  };
}

export function resolveProjectScopeApplyState(options: {
  projectScopeState: ProjectScopeState;
}): ProjectScopeState {
  return {
    projectScopeTotals: options.projectScopeState.projectScopeTotals,
    projectScopeMetrics: options.projectScopeState.projectScopeMetrics,
  };
}

export function resolveWindowMetricsApplyState(options: {
  windowState: WindowMetricsState;
}): WindowMetricsState {
  return {
    groupWindowCount: options.windowState.groupWindowCount,
    groupWindowStart: options.windowState.groupWindowStart,
    groupWindowEnd: options.windowState.groupWindowEnd,
    groupWindowTotal: options.windowState.groupWindowTotal,
    groupWindowNextOffset: options.windowState.groupWindowNextOffset,
    groupWindowPrevOffset: options.windowState.groupWindowPrevOffset,
  };
}
