import { normalizeActionViewMode, resolveActionViewAvailableModes } from '../contracts/actionViewSurfaceContract';

type Dict = Record<string, unknown>;

type SavedFilterChip = { key: string; isDefault?: boolean };
type GroupByChip = { field: string; isDefault?: boolean };

export function resolvePreferredActionViewMode(options: {
  contractViewTypeRaw: unknown;
  metaViewModesRaw: unknown;
  metaViewsRaw?: unknown;
  contract: Dict;
  routeViewModeRaw: unknown;
  currentPreferredViewModeRaw: unknown;
}): string {
  const candidates = resolveActionViewAvailableModes({
    contractViewTypeRaw: options.contractViewTypeRaw,
    metaViewModesRaw: options.metaViewModesRaw,
    metaViewsRaw: options.metaViewsRaw,
    contract: options.contract,
  });
  const routeMode = normalizeActionViewMode(options.routeViewModeRaw);
  if (routeMode && candidates.includes(routeMode)) {
    return routeMode;
  }
  const currentMode = normalizeActionViewMode(options.currentPreferredViewModeRaw);
  if (currentMode && candidates.includes(currentMode)) {
    return currentMode;
  }
  return candidates[0] || '';
}

export function resolveRouteSelectionState(options: {
  routeFilterRaw: unknown;
  routeSavedFilterRaw: unknown;
  routeGroupByRaw: unknown;
  activeContractFilterKey: string;
  activeSavedFilterKey: string;
  activeGroupByField: string;
  contractFiltersRaw: unknown;
  savedFilterChips: SavedFilterChip[];
  groupByChips: GroupByChip[];
}): {
  activeContractFilterKey: string;
  activeSavedFilterKey: string;
  activeGroupByField: string;
} {
  const routeFilter = String(options.routeFilterRaw || '').trim();
  const routeSavedFilter = String(options.routeSavedFilterRaw || '').trim();
  const routeGroupBy = String(options.routeGroupByRaw || '').trim();

  let activeContractFilterKey = String(options.activeContractFilterKey || '').trim();
  if (!activeContractFilterKey && routeFilter) {
    activeContractFilterKey = routeFilter;
  }
  if (activeContractFilterKey) {
    const hasFilter = Array.isArray(options.contractFiltersRaw)
      && options.contractFiltersRaw.some((row) => String((row as { key?: unknown })?.key || '') === activeContractFilterKey);
    if (!hasFilter) {
      activeContractFilterKey = '';
    }
  }

  let activeSavedFilterKey = String(options.activeSavedFilterKey || '').trim();
  if (!activeSavedFilterKey && routeSavedFilter) {
    activeSavedFilterKey = routeSavedFilter;
  }
  if (activeSavedFilterKey) {
    const hasSavedFilter = options.savedFilterChips.some((row) => row.key === activeSavedFilterKey);
    if (!hasSavedFilter) {
      activeSavedFilterKey = '';
    }
  } else {
    const defaultSaved = options.savedFilterChips.find((row) => row.isDefault);
    if (defaultSaved) activeSavedFilterKey = defaultSaved.key;
  }

  let activeGroupByField = String(options.activeGroupByField || '').trim();
  if (!activeGroupByField && routeGroupBy) {
    activeGroupByField = routeGroupBy;
  }
  if (activeGroupByField) {
    const hasGroupBy = options.groupByChips.some((item) => item.field === activeGroupByField);
    if (!hasGroupBy) activeGroupByField = '';
  } else {
    const defaultGroupBy = options.groupByChips.find((item) => item.isDefault);
    if (defaultGroupBy) activeGroupByField = defaultGroupBy.field;
  }

  return {
    activeContractFilterKey,
    activeSavedFilterKey,
    activeGroupByField,
  };
}
