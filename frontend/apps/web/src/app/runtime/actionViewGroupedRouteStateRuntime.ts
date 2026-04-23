type Dict = Record<string, unknown>;

import { buildNormalizedGroupedRoutePatch } from './actionViewGroupedRouteNormalizeRuntime';

export function resolveGroupedRouteInactiveResetPlan(options: {
  activeGroupByField: string;
  groupWindowOffset: number;
  collapsedGroupKeys: string[];
  groupPageOffsets: Record<string, number>;
}): {
  shouldReset: boolean;
  resetGroupWindowOffset: boolean;
  resetCollapsedGroupKeys: boolean;
  resetGroupPageOffsets: boolean;
  offsetPatch: Dict;
  collapsedPatch: Dict;
  pagesPatch: Dict;
} {
  if (options.activeGroupByField) {
    return {
      shouldReset: false,
      resetGroupWindowOffset: false,
      resetCollapsedGroupKeys: false,
      resetGroupPageOffsets: false,
      offsetPatch: {},
      collapsedPatch: {},
      pagesPatch: {},
    };
  }
  const resetGroupWindowOffset = options.groupWindowOffset !== 0;
  const resetCollapsedGroupKeys = options.collapsedGroupKeys.length > 0;
  const resetGroupPageOffsets = Object.keys(options.groupPageOffsets).length > 0;
  return {
    shouldReset: resetGroupWindowOffset || resetCollapsedGroupKeys || resetGroupPageOffsets,
    resetGroupWindowOffset,
    resetCollapsedGroupKeys,
    resetGroupPageOffsets,
    offsetPatch: { group_offset: undefined },
    collapsedPatch: { group_collapsed: undefined, group_page: undefined, group_offset: undefined },
    pagesPatch: { group_page: undefined, group_offset: undefined },
  };
}

export function buildGroupedRouteNormalizeInput(options: {
  groupedRows: unknown[];
  groupSummaryItems: unknown[];
  collapsedGroupKeys: string[];
  groupPageOffsets: Record<string, number>;
  routeGroupValue: string;
  groupSampleLimit: number;
}): {
  groupedRows: unknown[];
  groupSummaryItems: unknown[];
  collapsedGroupKeys: string[];
  groupPageOffsets: Record<string, number>;
  routeGroupValue: string;
  groupSampleLimit: number;
} {
  return {
    groupedRows: options.groupedRows,
    groupSummaryItems: options.groupSummaryItems,
    collapsedGroupKeys: options.collapsedGroupKeys,
    groupPageOffsets: options.groupPageOffsets,
    routeGroupValue: options.routeGroupValue,
    groupSampleLimit: options.groupSampleLimit,
  };
}

export function resolveGroupedRouteSelectionReset(options: {
  groupValueExists: boolean;
  currentActiveGroupSummaryKey: string;
  currentActiveGroupSummaryDomain: unknown[];
}): {
  activeGroupSummaryKey: string;
  activeGroupSummaryDomain: unknown[];
} {
  if (options.groupValueExists) {
    return {
      activeGroupSummaryKey: options.currentActiveGroupSummaryKey,
      activeGroupSummaryDomain: options.currentActiveGroupSummaryDomain,
    };
  }
  return {
    activeGroupSummaryKey: '',
    activeGroupSummaryDomain: [],
  };
}

export function shouldSyncGroupedRouteState(options: {
  collapsedChanged: boolean;
  groupValueExists: boolean;
  groupPageChanged: boolean;
  groupOffsetChanged: boolean;
}): boolean {
  return options.collapsedChanged || !options.groupValueExists || options.groupPageChanged || options.groupOffsetChanged;
}

export function buildGroupedRouteActiveSyncPayload(options: {
  normalizedCollapsed: string[];
  normalizedGroupPages: Record<string, number>;
  groupWindowOffset: number;
  groupValueExists: boolean;
}): {
  normalizedCollapsed: string[];
  normalizedGroupPages: Record<string, number>;
  groupWindowOffset: number;
  groupValueExists: boolean;
} {
  return {
    normalizedCollapsed: options.normalizedCollapsed,
    normalizedGroupPages: options.normalizedGroupPages,
    groupWindowOffset: options.groupWindowOffset,
    groupValueExists: options.groupValueExists,
  };
}

export function resolveGroupedRouteLocalState(options: {
  groupValueExists: boolean;
  currentActiveGroupSummaryKey: string;
  currentActiveGroupSummaryDomain: unknown[];
  normalizedCollapsed: string[];
  normalizedGroupPages: Record<string, number>;
}): {
  activeGroupSummaryKey: string;
  activeGroupSummaryDomain: unknown[];
  collapsedGroupKeys: string[];
  groupPageOffsets: Record<string, number>;
} {
  const nextSelection = resolveGroupedRouteSelectionReset({
    groupValueExists: options.groupValueExists,
    currentActiveGroupSummaryKey: options.currentActiveGroupSummaryKey,
    currentActiveGroupSummaryDomain: options.currentActiveGroupSummaryDomain,
  });
  return {
    activeGroupSummaryKey: nextSelection.activeGroupSummaryKey,
    activeGroupSummaryDomain: nextSelection.activeGroupSummaryDomain,
    collapsedGroupKeys: options.normalizedCollapsed,
    groupPageOffsets: options.normalizedGroupPages,
  };
}

export function resolveGroupedRouteSyncPlan(options: {
  normalizedCollapsed: string[];
  normalizedGroupPages: Record<string, number>;
  groupWindowOffset: number;
  groupValueExists: boolean;
  collapsedChanged: boolean;
  groupPageChanged: boolean;
  routeGroupOffsetRaw: string;
  hasOffsetChanged: (raw: string, offset: number) => boolean;
}): {
  nextState: Dict;
  groupOffsetChanged: boolean;
  shouldSync: boolean;
} {
  const nextState = buildNormalizedGroupedRoutePatch(buildGroupedRouteActiveSyncPayload({
    normalizedCollapsed: options.normalizedCollapsed,
    normalizedGroupPages: options.normalizedGroupPages,
    groupWindowOffset: options.groupWindowOffset,
    groupValueExists: options.groupValueExists,
  }));
  const groupOffsetChanged = options.hasOffsetChanged(options.routeGroupOffsetRaw, options.groupWindowOffset);
  const shouldSync = shouldSyncGroupedRouteState({
    collapsedChanged: options.collapsedChanged,
    groupValueExists: options.groupValueExists,
    groupPageChanged: options.groupPageChanged,
    groupOffsetChanged,
  });
  return {
    nextState,
    groupOffsetChanged,
    shouldSync,
  };
}
