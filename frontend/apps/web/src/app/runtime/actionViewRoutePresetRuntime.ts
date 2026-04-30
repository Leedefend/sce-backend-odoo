export function resolveRoutePresetSearchTerm(options: {
  routeSearch: string;
  preset: string;
  presetFilter: string;
  groupValue: string;
}): string {
  if (options.routeSearch) return options.routeSearch;
  if (options.groupValue) return options.groupValue;
  return '';
}

export function resolveRoutePresetAppliedLabel(options: {
  preset: string;
  presetFilter: string;
  savedFilter: string;
  text: (key: string, fallback: string) => string;
}): string {
  if (!options.preset && options.presetFilter) {
    return `${options.text('preset_label_contract_filter_prefix', '契约筛选: ')}${options.presetFilter}`;
  }
  if (options.savedFilter) {
    return `${options.text('preset_label_saved_filter_prefix', '保存筛选: ')}${options.savedFilter}`;
  }
  return '';
}

export function resolveRoutePresetGroupWindowState(options: {
  groupBy: string;
  groupOffsetRaw: number;
  groupFingerprintRaw: string;
  groupWindowIdRaw: string;
  groupWindowDigestRaw: string;
  groupWindowIdentityKeyRaw: string;
}): {
  activeGroupByField: string;
  groupWindowOffset: number;
  groupQueryFingerprint: string;
  groupWindowId: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
} {
  if (!options.groupBy) {
    return {
      activeGroupByField: '',
      groupWindowOffset: 0,
      groupQueryFingerprint: '',
      groupWindowId: '',
      groupWindowDigest: '',
      groupWindowIdentityKey: '',
    };
  }
  const normalizedGroupOffset = Number.isFinite(options.groupOffsetRaw) && options.groupOffsetRaw > 0
    ? Math.trunc(options.groupOffsetRaw)
    : 0;
  return {
    activeGroupByField: options.groupBy,
    groupWindowOffset: normalizedGroupOffset,
    groupQueryFingerprint: options.groupFingerprintRaw,
    groupWindowId: options.groupWindowIdRaw,
    groupWindowDigest: options.groupWindowDigestRaw,
    groupWindowIdentityKey: options.groupWindowIdentityKeyRaw,
  };
}

export function resolveRoutePresetGroupVisualState(options: {
  groupSampleLimitRaw: number;
  groupSortRaw: string;
  groupCollapsedRaw: string;
  sampleLimits?: number[];
  defaultSampleLimit?: number;
  sortDirections?: string[];
  defaultSortDirection?: string;
}): {
  groupSampleLimit: number;
  groupSort: 'asc' | 'desc';
  collapsedList: string[];
} {
  const sampleLimits = Array.isArray(options.sampleLimits)
    ? options.sampleLimits
        .map((item) => Number(item))
        .filter((item) => Number.isFinite(item) && item > 0)
        .map((item) => Math.trunc(item))
    : [];
  const effectiveSampleLimits = sampleLimits.length ? sampleLimits : [3];
  const defaultSampleLimitRaw = Number(options.defaultSampleLimit || 0);
  const defaultSampleLimit = Number.isFinite(defaultSampleLimitRaw) && effectiveSampleLimits.includes(Math.trunc(defaultSampleLimitRaw))
    ? Math.trunc(defaultSampleLimitRaw)
    : effectiveSampleLimits[0];
  const groupSampleLimit = Number.isFinite(options.groupSampleLimitRaw) && effectiveSampleLimits.includes(options.groupSampleLimitRaw)
    ? options.groupSampleLimitRaw
    : defaultSampleLimit;
  const sortDirections = Array.isArray(options.sortDirections)
    ? options.sortDirections.filter((item): item is 'asc' | 'desc' => item === 'asc' || item === 'desc')
    : [];
  const effectiveSortDirections: Array<'asc' | 'desc'> = sortDirections.length ? sortDirections : ['desc', 'asc'];
  const defaultSortDirection = options.defaultSortDirection === 'asc' ? 'asc' : 'desc';
  const fallbackSortDirection: 'asc' | 'desc' = effectiveSortDirections.includes(defaultSortDirection) ? defaultSortDirection : effectiveSortDirections[0];
  const groupSort = (options.groupSortRaw === 'asc' || options.groupSortRaw === 'desc') && effectiveSortDirections.includes(options.groupSortRaw)
    ? options.groupSortRaw
    : fallbackSortDirection;
  const collapsedList = options.groupCollapsedRaw
    ? options.groupCollapsedRaw.split(',').map((item) => item.trim()).filter(Boolean)
    : [];
  return {
    groupSampleLimit,
    groupSort,
    collapsedList,
  };
}

export function resolveRoutePresetTrackingState(options: {
  preset: string;
  presetFilter: string;
  savedFilter: string;
  groupBy: string;
  lastTrackedPreset: string;
}): {
  shouldTrackPresetApply: boolean;
  nextTrackedPreset: string;
} {
  if (options.preset) {
    const shouldTrackPresetApply = options.preset !== options.lastTrackedPreset;
    return {
      shouldTrackPresetApply,
      nextTrackedPreset: options.preset,
    };
  }
  if (!options.presetFilter && !options.savedFilter && !options.groupBy) {
    return {
      shouldTrackPresetApply: false,
      nextTrackedPreset: '',
    };
  }
  return {
    shouldTrackPresetApply: false,
    nextTrackedPreset: options.lastTrackedPreset,
  };
}

export function resolveRoutePresetSavedFilterValue(savedFilter: string): string {
  return savedFilter || '';
}

export function resolveRoutePresetActiveFilterValue(routeActiveFilter: string): 'all' | 'active' | 'archived' | null {
  if (routeActiveFilter === 'all' || routeActiveFilter === 'active' || routeActiveFilter === 'archived') {
    return routeActiveFilter;
  }
  return null;
}

export function resolveRoutePresetGroupSummaryResetState(groupValue: string): {
  shouldReset: boolean;
  activeGroupSummaryKey: string;
  activeGroupSummaryDomain: unknown[];
} {
  if (groupValue) {
    return {
      shouldReset: false,
      activeGroupSummaryKey: '',
      activeGroupSummaryDomain: [],
    };
  }
  return {
    shouldReset: true,
    activeGroupSummaryKey: '',
    activeGroupSummaryDomain: [],
  };
}

export function hasRoutePresetGroupPageStateChanged(options: {
  parsedGroupPages: Record<string, number>;
  currentGroupPages: Record<string, number>;
}): boolean {
  const parsedKeys = Object.keys(options.parsedGroupPages);
  const currentKeys = Object.keys(options.currentGroupPages);
  if (parsedKeys.length !== currentKeys.length) return true;
  return parsedKeys.some((key) => options.currentGroupPages[key] !== options.parsedGroupPages[key]);
}

export function resolveRoutePresetGroupPageState(options: {
  parsedGroupPages: Record<string, number>;
  currentGroupPages: Record<string, number>;
}): {
  changed: boolean;
  nextGroupPages: Record<string, number>;
} {
  const changed = hasRoutePresetGroupPageStateChanged(options);
  return {
    changed,
    nextGroupPages: changed ? options.parsedGroupPages : options.currentGroupPages,
  };
}
