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

function normalizeGroupSampleLimitOptions(limits?: number[]): number[] {
  const values = Array.isArray(limits) ? limits : [];
  return Array.from(new Set(values
    .map((item) => Number(item || 0))
    .filter((item) => Number.isFinite(item) && item > 0)
    .map((item) => Math.trunc(item))));
}

function normalizeGroupSortDirections(directions?: string[]): Array<'asc' | 'desc'> {
  const values = Array.isArray(directions) ? directions : [];
  const normalized = values
    .map((item) => String(item || '').trim())
    .filter((item): item is 'asc' | 'desc' => item === 'asc' || item === 'desc');
  return normalized.length ? Array.from(new Set(normalized)) : ['desc', 'asc'];
}

export function normalizeGroupSampleLimit(limit: number, sampleLimits?: number[]): number | null {
  const normalized = Number(limit || 0);
  if (!Number.isFinite(normalized)) return null;
  const candidate = Math.trunc(normalized);
  const allowedLimits = normalizeGroupSampleLimitOptions(sampleLimits);
  if (!allowedLimits.length || !allowedLimits.includes(candidate)) return null;
  return candidate;
}

export function buildGroupSampleLimitPatch(limit: number, options?: {
  defaultSampleLimit?: number;
}): Dict {
  const defaultSampleLimitRaw = Number(options?.defaultSampleLimit || 0);
  const defaultSampleLimit = Number.isFinite(defaultSampleLimitRaw) && defaultSampleLimitRaw > 0
    ? Math.trunc(defaultSampleLimitRaw)
    : null;
  return {
    group_sample_limit: defaultSampleLimit !== null && limit === defaultSampleLimit ? undefined : limit,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  };
}

export function resolveGroupSampleLimitTransition(limit: number, options?: {
  sampleLimits?: number[];
  defaultSampleLimit?: number;
}): {
  normalizedLimit: number | null;
  patch: Dict | null;
  resetGroupWindowOffset: boolean;
  resetGroupPageOffsets: boolean;
} {
  const normalizedLimit = normalizeGroupSampleLimit(limit, options?.sampleLimits);
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
    patch: buildGroupSampleLimitPatch(normalizedLimit, { defaultSampleLimit: options?.defaultSampleLimit }),
    resetGroupWindowOffset: true,
    resetGroupPageOffsets: true,
  };
}

export function buildGroupSortPatch(sort: 'asc' | 'desc', options?: {
  defaultSort?: 'asc' | 'desc';
}): Dict {
  const defaultSort = options?.defaultSort === 'asc' || options?.defaultSort === 'desc'
    ? options.defaultSort
    : 'desc';
  return {
    group_sort: sort !== defaultSort ? sort : undefined,
  };
}

export function resolveGroupSortTransition(sort: 'asc' | 'desc', options?: {
  sortDirections?: string[];
  defaultSort?: 'asc' | 'desc';
}): {
  normalizedSort: 'asc' | 'desc';
  patch: Dict;
} {
  const sortDirections = normalizeGroupSortDirections(options?.sortDirections);
  const defaultSort = options?.defaultSort === 'asc' || options?.defaultSort === 'desc'
    ? options.defaultSort
    : sortDirections[0];
  const normalizedSort: 'asc' | 'desc' = sortDirections.includes(sort) ? sort : defaultSort;
  return {
    normalizedSort,
    patch: buildGroupSortPatch(normalizedSort, { defaultSort }),
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
