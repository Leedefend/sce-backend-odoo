type Dict = Record<string, unknown>;

export function buildActionViewRouteSyncStatePayload(options: {
  searchTerm: string;
  sortValue: string;
  filterValue: string;
  groupSampleLimit: number;
  groupSort: 'asc' | 'desc';
  defaultGroupSampleLimit?: number;
  defaultGroupSort?: 'asc' | 'desc';
  collapsedGroupKeys: string[];
  groupPageOffsets: Record<string, number>;
  activeGroupByField: string;
  groupWindowOffset: number;
  groupQueryFingerprint: string;
  groupWindowId: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
  extra?: Dict;
}): Dict {
  return {
    searchTerm: options.searchTerm,
    sortValue: options.sortValue,
    filterValue: options.filterValue,
    groupSampleLimit: options.groupSampleLimit,
    groupSort: options.groupSort,
    defaultGroupSampleLimit: options.defaultGroupSampleLimit,
    defaultGroupSort: options.defaultGroupSort,
    collapsedGroupKeys: options.collapsedGroupKeys,
    groupPageOffsets: options.groupPageOffsets,
    activeGroupByField: options.activeGroupByField,
    groupWindowOffset: options.groupWindowOffset,
    groupQueryFingerprint: options.groupQueryFingerprint,
    groupWindowId: options.groupWindowId,
    groupWindowDigest: options.groupWindowDigest,
    groupWindowIdentityKey: options.groupWindowIdentityKey,
    extra: options.extra,
  };
}

export function resolveRouteSyncExtra(extra?: Dict): Dict | undefined {
  if (!extra || !Object.keys(extra).length) return undefined;
  return extra;
}

export function resolveRouteSyncShouldAwaitLoad(mode: 'fire_and_forget' | 'await'): boolean {
  return mode === 'await';
}
