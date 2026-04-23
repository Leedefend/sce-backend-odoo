type Dict = Record<string, unknown>;

export function normalizeActionViewRouteQuery(query: unknown): Dict {
  if (!query || typeof query !== 'object') return {};
  return query as Dict;
}

export type ActionViewRouteSnapshot = {
  preset: string;
  presetFilter: string;
  savedFilter: string;
  groupBy: string;
  groupValue: string;
  groupSampleLimitRaw: number;
  groupSortRaw: string;
  groupCollapsedRaw: string;
  groupPageRaw: string;
  groupOffsetRaw: number;
  groupFingerprintRaw: string;
  groupWindowIdRaw: string;
  groupWindowDigestRaw: string;
  groupWindowIdentityKeyRaw: string;
  routeSearch: string;
  routeOrder: string;
  routeActiveFilter: string;
  ctxSource: string;
};

export function resolveActionViewRouteSnapshot(query: Dict): ActionViewRouteSnapshot {
  return {
    preset: String(query.preset || '').trim(),
    presetFilter: String(query.preset_filter || '').trim(),
    savedFilter: String(query.saved_filter || '').trim(),
    groupBy: String(query.group_by || '').trim(),
    groupValue: String(query.group_value || '').trim(),
    groupSampleLimitRaw: Number(query.group_sample_limit || 0),
    groupSortRaw: String(query.group_sort || '').trim().toLowerCase(),
    groupCollapsedRaw: String(query.group_collapsed || '').trim(),
    groupPageRaw: String(query.group_page || '').trim(),
    groupOffsetRaw: Number(query.group_offset || 0),
    groupFingerprintRaw: String(query.group_fp || '').trim(),
    groupWindowIdRaw: String(query.group_wid || '').trim(),
    groupWindowDigestRaw: String(query.group_wdg || '').trim(),
    groupWindowIdentityKeyRaw: String(query.group_wik || '').trim(),
    routeSearch: String(query.search || '').trim(),
    routeOrder: String(query.order || query.sort || '').trim(),
    routeActiveFilter: String(query.active_filter || '').trim(),
    ctxSource: String(query.ctx_source || '').trim(),
  };
}

import { pickContractNavQuery } from '../navigationContext';
import { stripWorkspaceContext } from '../workspaceContext';
import { serializeGroupPageOffsets } from './actionViewGroupWindowRuntime';

type ListStatePatchOptions = {
  searchTerm: string;
  sortValue: string;
  filterValue: 'all' | 'active' | 'archived';
  groupSampleLimit: number;
  groupSort: 'asc' | 'desc';
  collapsedGroupKeys: string[];
  groupPage: string;
  activeGroupByField: string;
  groupWindowOffset: number;
  groupQueryFingerprint: string;
  groupWindowId: string;
  groupWindowDigest: string;
  groupWindowIdentityKey: string;
  extra?: Dict;
};

export function buildActionViewListStatePatch(options: ListStatePatchOptions): Dict {
  return {
    search: options.searchTerm.trim() || undefined,
    order: options.sortValue.trim() || undefined,
    active_filter: options.filterValue !== 'all' ? options.filterValue : undefined,
    group_sample_limit: options.groupSampleLimit !== 3 ? options.groupSampleLimit : undefined,
    group_sort: options.groupSort !== 'desc' ? options.groupSort : undefined,
    group_collapsed: options.collapsedGroupKeys.filter(Boolean).join(',') || undefined,
    group_page: options.groupPage || undefined,
    group_offset: options.activeGroupByField && options.groupWindowOffset > 0 ? options.groupWindowOffset : undefined,
    group_fp: options.activeGroupByField && options.groupQueryFingerprint ? options.groupQueryFingerprint : undefined,
    group_wid: options.activeGroupByField && options.groupWindowId ? options.groupWindowId : undefined,
    group_wdg: options.activeGroupByField && options.groupWindowDigest ? options.groupWindowDigest : undefined,
    group_wik: options.activeGroupByField && options.groupWindowIdentityKey ? options.groupWindowIdentityKey : undefined,
    ...(options.extra || {}),
  };
}

type SyncRouteQueryOptions = Omit<ListStatePatchOptions, 'groupPage'> & {
  groupPageOffsets: Record<string, number>;
};

export function buildActionViewSyncedRouteQuery(currentQuery: Dict, options: SyncRouteQueryOptions): Dict {
  return pickContractNavQuery(
    currentQuery,
    buildActionViewListStatePatch({
      searchTerm: options.searchTerm,
      sortValue: options.sortValue,
      filterValue: options.filterValue,
      groupSampleLimit: options.groupSampleLimit,
      groupSort: options.groupSort,
      collapsedGroupKeys: options.collapsedGroupKeys,
      groupPage: serializeGroupPageOffsets(options.groupPageOffsets),
      activeGroupByField: options.activeGroupByField,
      groupWindowOffset: options.groupWindowOffset,
      groupQueryFingerprint: options.groupQueryFingerprint,
      groupWindowId: options.groupWindowId,
      groupWindowDigest: options.groupWindowDigest,
      groupWindowIdentityKey: options.groupWindowIdentityKey,
      extra: options.extra,
    }),
  );
}

export function buildActionViewPatchedRouteQuery(currentQuery: Dict, patch: Dict): Dict {
  return pickContractNavQuery(currentQuery, patch);
}

export function buildActionViewClearedPresetQuery(currentQuery: Dict): Dict {
  return stripWorkspaceContext(currentQuery);
}

export function buildWorkbenchRouteTarget(query: Dict): { name: 'workbench'; query: Dict } {
  return {
    name: 'workbench',
    query,
  };
}

export function buildPathRouteTarget(path: string, query?: Dict): { path: string; query?: Dict } {
  return {
    path,
    query,
  };
}

export function buildModelFormRouteTarget(options: {
  model: string;
  id: string;
  query: Dict;
}): { name: 'model-form'; params: { model: string; id: string }; query: Dict } {
  return {
    name: 'model-form',
    params: {
      model: options.model,
      id: options.id,
    },
    query: options.query,
  };
}

export function buildPresetFilterPatch(key?: string): Dict {
  return { preset_filter: key || undefined };
}

export function buildSavedFilterPatch(key?: string): Dict {
  return { saved_filter: key || undefined };
}

export function buildGroupByPatch(field?: string): Dict {
  return {
    group_by: field || undefined,
    group_value: undefined,
    group_page: undefined,
    group_offset: undefined,
    group_fp: undefined,
    group_wid: undefined,
    group_wdg: undefined,
    group_wik: undefined,
  };
}
