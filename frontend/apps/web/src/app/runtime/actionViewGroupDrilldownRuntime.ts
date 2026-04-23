type Dict = Record<string, unknown>;

export type GroupSummaryTransitionState = {
  activeGroupSummaryKey: string;
  activeGroupSummaryDomain: unknown[];
  groupWindowOffset: number;
  searchTerm: string;
};

export function buildGroupSummaryPickState(item: {
  key?: string;
  label?: string;
  domain?: unknown[];
}): GroupSummaryTransitionState {
  return {
    activeGroupSummaryKey: String(item.key || ''),
    activeGroupSummaryDomain: Array.isArray(item.domain) ? item.domain : [],
    groupWindowOffset: 0,
    searchTerm: String(item.label || ''),
  };
}

export function buildOpenGroupedRowsState(group: {
  key?: string;
  domain?: unknown[];
}): GroupSummaryTransitionState {
  return {
    activeGroupSummaryKey: String(group.key || ''),
    activeGroupSummaryDomain: Array.isArray(group.domain) ? group.domain : [],
    groupWindowOffset: 0,
    searchTerm: '',
  };
}

export function buildClearGroupSummaryState(): GroupSummaryTransitionState {
  return {
    activeGroupSummaryKey: '',
    activeGroupSummaryDomain: [],
    groupWindowOffset: 0,
    searchTerm: '',
  };
}

export function buildGroupSummaryPickPatch(search: string, label: string): Dict {
  return {
    search: search.trim() || undefined,
    group_value: label || undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  };
}

export function buildOpenGroupedRowsPatch(label: string): Dict {
  return {
    search: undefined,
    group_value: label || undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  };
}

export function buildClearGroupSummaryPatch(): Dict {
  return {
    group_value: undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  };
}

export function buildGroupWindowMovePatch(offset: number): Dict {
  return {
    group_offset: offset || undefined,
    group_collapsed: undefined,
    group_page: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  };
}

export function resolveGroupWindowMoveTarget(options: {
  prevOffset: number | null;
  nextOffset: number | null;
  direction: 'prev' | 'next';
}): number | null {
  if (options.direction === 'prev') {
    return options.prevOffset === null ? null : Number(options.prevOffset);
  }
  return options.nextOffset === null ? null : Number(options.nextOffset);
}

export function normalizeGroupSampleLimit(limit: number): number | null {
  const normalized = Number(limit || 0);
  if (!Number.isFinite(normalized)) return null;
  if (![3, 5, 8].includes(normalized)) return null;
  return normalized;
}

export function buildGroupSampleLimitPatch(limit: number): Dict {
  return {
    group_sample_limit: limit,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  };
}

export function resolveGroupSampleLimitTransition(limit: number): {
  normalizedLimit: number | null;
  patch: Dict | null;
  resetGroupWindowOffset: boolean;
  resetGroupPageOffsets: boolean;
} {
  const normalizedLimit = normalizeGroupSampleLimit(limit);
  if (normalizedLimit === null) {
    return {
      normalizedLimit: null,
      patch: null,
      resetGroupWindowOffset: false,
      resetGroupPageOffsets: false,
    };
  }
  return {
    normalizedLimit,
    patch: buildGroupSampleLimitPatch(normalizedLimit),
    resetGroupWindowOffset: true,
    resetGroupPageOffsets: true,
  };
}

export function buildGroupSortPatch(sort: 'asc' | 'desc'): Dict {
  return {
    group_sort: sort !== 'desc' ? sort : undefined,
  };
}

export function resolveGroupSortTransition(sort: 'asc' | 'desc'): {
  normalizedSort: 'asc' | 'desc';
  patch: Dict;
} {
  const normalizedSort: 'asc' | 'desc' = sort === 'asc' ? 'asc' : 'desc';
  return {
    normalizedSort,
    patch: buildGroupSortPatch(normalizedSort),
  };
}

export function buildGroupCollapsedPatch(keys: string[]): Dict {
  return {
    group_collapsed: keys.length ? keys.join(',') : undefined,
  };
}

export function resolveGroupCollapsedTransition(keys: string[]): {
  normalizedKeys: string[];
  patch: Dict;
} {
  const normalizedKeys = Array.isArray(keys) ? keys.filter(Boolean) : [];
  return {
    normalizedKeys,
    patch: buildGroupCollapsedPatch(normalizedKeys),
  };
}
