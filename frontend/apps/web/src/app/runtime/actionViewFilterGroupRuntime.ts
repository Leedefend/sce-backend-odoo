type Dict = Record<string, unknown>;

export function resolveNonEmptyControlKey(keyRaw: string): string {
  return String(keyRaw || '').trim();
}

export function resolveContractFilterApplyState(options: {
  key: string;
  buildPatch: (key?: string) => Dict;
}): {
  activeContractFilterKey: string;
  showMoreContractFilters: boolean;
  shouldClearSelection: boolean;
  routePatch: Dict;
} {
  return {
    activeContractFilterKey: options.key,
    showMoreContractFilters: false,
    shouldClearSelection: true,
    routePatch: options.buildPatch(options.key),
  };
}

export function resolveSavedFilterApplyState(options: {
  key: string;
  buildPatch: (key?: string) => Dict;
}): {
  activeSavedFilterKey: string;
  showMoreSavedFilters: boolean;
  shouldClearSelection: boolean;
  routePatch: Dict;
} {
  return {
    activeSavedFilterKey: options.key,
    showMoreSavedFilters: false,
    shouldClearSelection: true,
    routePatch: options.buildPatch(options.key),
  };
}

export function resolveGroupByApplyState(options: {
  field: string;
  buildPatch: (field?: string) => Dict;
}): {
  activeGroupByField: string;
  shouldResetGroupSharedState: boolean;
  shouldClearSelection: boolean;
  routePatch: Dict;
} {
  return {
    activeGroupByField: options.field,
    shouldResetGroupSharedState: true,
    shouldClearSelection: true,
    routePatch: options.buildPatch(options.field),
  };
}

export function resolveGroupByClearState(options: {
  buildPatch: (field?: string) => Dict;
}): {
  activeGroupByField: string;
  shouldResetGroupSharedState: boolean;
  shouldClearSelection: boolean;
  routePatch: Dict;
} {
  return {
    activeGroupByField: '',
    shouldResetGroupSharedState: true,
    shouldClearSelection: true,
    routePatch: options.buildPatch(),
  };
}

export function resolveContractFilterClearState(options: {
  buildPatch: (key?: string) => Dict;
}): {
  activeContractFilterKey: string;
  showMoreContractFilters: boolean;
  shouldClearSelection: boolean;
  routePatch: Dict;
} {
  return {
    activeContractFilterKey: '',
    showMoreContractFilters: false,
    shouldClearSelection: true,
    routePatch: options.buildPatch(),
  };
}

export function resolveSavedFilterClearState(options: {
  buildPatch: (key?: string) => Dict;
}): {
  activeSavedFilterKey: string;
  showMoreSavedFilters: boolean;
  shouldClearSelection: boolean;
  routePatch: Dict;
} {
  return {
    activeSavedFilterKey: '',
    showMoreSavedFilters: false,
    shouldClearSelection: true,
    routePatch: options.buildPatch(),
  };
}
