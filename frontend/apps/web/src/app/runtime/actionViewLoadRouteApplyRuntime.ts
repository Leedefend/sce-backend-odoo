type Dict = Record<string, unknown>;

export function resolveLoadRouteResetApplyState(options: {
  resetPatch: Dict | null;
}): {
  shouldReset: boolean;
  groupWindowOffset: number;
  groupPageOffsets: Record<string, number>;
  collapsedGroupKeys: string[];
  patch: Dict | null;
} {
  if (!options.resetPatch) {
    return {
      shouldReset: false,
      groupWindowOffset: 0,
      groupPageOffsets: {},
      collapsedGroupKeys: [],
      patch: null,
    };
  }
  return {
    shouldReset: true,
    groupWindowOffset: 0,
    groupPageOffsets: {},
    collapsedGroupKeys: [],
    patch: options.resetPatch,
  };
}

export function resolveLoadRouteSyncApplyState(options: {
  syncPatch: Dict | null;
}): {
  shouldSync: boolean;
  patch: Dict | null;
} {
  return {
    shouldSync: Boolean(options.syncPatch),
    patch: options.syncPatch,
  };
}
