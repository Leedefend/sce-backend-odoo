import type { Ref } from 'vue';
import type { SceneListProfile } from '../resolvers/sceneRegistry';

type Dict = Record<string, unknown>;

type RouteSnapshot = {
  preset: string;
  presetFilter: string;
  savedFilter: string;
  groupBy: string;
  groupValue: string;
  groupSampleLimitRaw: string | number;
  groupSortRaw: string;
  groupCollapsedRaw: string;
  groupPageRaw: string;
  groupOffsetRaw: string | number;
  groupFingerprintRaw: string;
  groupWindowIdRaw: string;
  groupWindowDigestRaw: string;
  groupWindowIdentityKeyRaw: string;
  routeSearch: string;
  routeOrder: string;
  routeActiveFilter: string;
  ctxSource: string;
};

type UseActionViewRoutePresetRuntimeOptions = {
  routeQueryMap: Ref<Record<string, unknown>>;
  pageText: (key: string, fallback: string) => string;
  showHud: Ref<boolean>;
  menuId: Ref<number | null>;
  actionId: Ref<number | null>;
  searchTerm: Ref<string>;
  sortValue: Ref<string>;
  filterValue: Ref<'all' | 'active' | 'archived'>;
  activeSavedFilterKey: Ref<string>;
  activeGroupByField: Ref<string>;
  groupWindowOffset: Ref<number>;
  groupQueryFingerprint: Ref<string>;
  groupWindowId: Ref<string>;
  groupWindowDigest: Ref<string>;
  groupWindowIdentityKey: Ref<string>;
  activeGroupSummaryKey: Ref<string>;
  activeGroupSummaryDomain: Ref<unknown[]>;
  groupSampleLimit: Ref<number>;
  groupSort: Ref<string>;
  listProfile: Ref<SceneListProfile | null>;
  collapsedGroupKeys: Ref<string[]>;
  groupPageOffsets: Ref<Record<string, number>>;
  appliedPresetLabel: Ref<string>;
  routeContextSource: Ref<string>;
  lastTrackedPreset: Ref<string>;
  resolveWorkspaceContextQuery: () => Record<string, unknown>;
  replaceCurrentRouteQuery: (query: Record<string, unknown>) => void;
  trackUsageEvent: (event: string, payload: Dict) => Promise<unknown>;
  load: () => Promise<void>;
  resolveActionViewRouteSnapshot: (query: Record<string, unknown>) => RouteSnapshot;
  resolveRoutePresetSearchTerm: (input: Dict) => string;
  resolveRoutePresetAppliedLabel: (input: Dict) => string;
  resolveRoutePresetActiveFilterValue: (routeActiveFilter: string) => 'all' | 'active' | 'archived' | '';
  resolveRoutePresetSavedFilterValue: (savedFilter: string) => string;
  resolveRoutePresetGroupWindowState: (input: Dict) => {
    activeGroupByField: string;
    groupWindowOffset: number;
    groupQueryFingerprint: string;
    groupWindowId: string;
    groupWindowDigest: string;
    groupWindowIdentityKey: string;
  };
  resolveRoutePresetGroupSummaryResetState: (groupValue: string) => {
    shouldReset: boolean;
    activeGroupSummaryKey: string;
    activeGroupSummaryDomain: unknown[];
  };
  resolveRoutePresetGroupVisualState: (input: Dict) => {
    groupSampleLimit: number;
    groupSort: string;
    collapsedList: string[];
  };
  parseGroupPageOffsets: (raw: string) => Record<string, number>;
  hasRoutePresetGroupPageStateChanged: (input: Dict) => boolean;
  resolveRoutePresetGroupPageState: (input: Dict) => { nextGroupPages: Record<string, number> };
  resolveRoutePresetTrackingState: (input: Dict) => { nextTrackedPreset: string; shouldTrackPresetApply: boolean };
  buildActionViewClearedPresetQuery: (query: Record<string, unknown>) => Record<string, unknown>;
  buildActionViewPatchedRouteQuery: (query: Record<string, unknown>, patch: Record<string, unknown>) => Record<string, unknown>;
  buildActionViewRouteSyncStatePayload: (input: Dict) => Record<string, unknown>;
  buildActionViewSyncedRouteQuery: (query: Record<string, unknown>, patch: Record<string, unknown>) => Record<string, unknown>;
  resolveRouteSyncExtra: (extra?: Record<string, unknown>) => Record<string, unknown>;
  resolveRouteSyncShouldAwaitLoad: (mode: 'fire_and_forget' | 'await') => boolean;
};

export function useActionViewRoutePresetRuntime(options: UseActionViewRoutePresetRuntimeOptions) {
  function applyRoutePreset() {
    const routeSnapshot = options.resolveActionViewRouteSnapshot(options.routeQueryMap.value);
    const preset = routeSnapshot.preset;
    const presetFilter = routeSnapshot.presetFilter;
    const savedFilter = routeSnapshot.savedFilter;
    const groupBy = routeSnapshot.groupBy;
    const groupValue = routeSnapshot.groupValue;
    const groupSampleLimitRaw = routeSnapshot.groupSampleLimitRaw;
    const groupSortRaw = routeSnapshot.groupSortRaw;
    const groupCollapsedRaw = routeSnapshot.groupCollapsedRaw;
    const groupPageRaw = routeSnapshot.groupPageRaw;
    const groupOffsetRaw = routeSnapshot.groupOffsetRaw;
    const groupFingerprintRaw = routeSnapshot.groupFingerprintRaw;
    const groupWindowIdRaw = routeSnapshot.groupWindowIdRaw;
    const groupWindowDigestRaw = routeSnapshot.groupWindowDigestRaw;
    const groupWindowIdentityKeyRaw = routeSnapshot.groupWindowIdentityKeyRaw;
    const routeSearch = routeSnapshot.routeSearch;
    const routeOrder = routeSnapshot.routeOrder;
    const routeActiveFilter = routeSnapshot.routeActiveFilter;
    const ctxSource = routeSnapshot.ctxSource;
    options.routeContextSource.value = ctxSource;
    let changed = false;
    const setIfDiff = <T>(target: { value: T }, next: T) => {
      if (target.value === next) return;
      target.value = next;
      changed = true;
    };

    const routeSearchTerm = options.resolveRoutePresetSearchTerm({
      routeSearch,
      preset,
      presetFilter,
      groupValue,
    });
    options.appliedPresetLabel.value = options.resolveRoutePresetAppliedLabel({
      preset,
      presetFilter,
      savedFilter,
      text: options.pageText,
    });
    setIfDiff(options.searchTerm, routeSearchTerm);
    if (routeOrder) {
      setIfDiff(options.sortValue, routeOrder);
    }
    const routeActiveFilterValue = options.resolveRoutePresetActiveFilterValue(routeActiveFilter);
    if (routeActiveFilterValue) setIfDiff(options.filterValue, routeActiveFilterValue);
    if (savedFilter) {
      setIfDiff(options.activeSavedFilterKey, options.resolveRoutePresetSavedFilterValue(savedFilter));
    } else {
      setIfDiff(options.activeSavedFilterKey, '');
    }
    const groupWindowState = options.resolveRoutePresetGroupWindowState({
      groupBy,
      groupOffsetRaw,
      groupFingerprintRaw,
      groupWindowIdRaw,
      groupWindowDigestRaw,
      groupWindowIdentityKeyRaw,
    });
    setIfDiff(options.activeGroupByField, groupWindowState.activeGroupByField);
    setIfDiff(options.groupWindowOffset, groupWindowState.groupWindowOffset);
    setIfDiff(options.groupQueryFingerprint, groupWindowState.groupQueryFingerprint);
    setIfDiff(options.groupWindowId, groupWindowState.groupWindowId);
    setIfDiff(options.groupWindowDigest, groupWindowState.groupWindowDigest);
    setIfDiff(options.groupWindowIdentityKey, groupWindowState.groupWindowIdentityKey);
    const groupSummaryResetState = options.resolveRoutePresetGroupSummaryResetState(groupValue);
    if (groupSummaryResetState.shouldReset) {
      options.activeGroupSummaryKey.value = groupSummaryResetState.activeGroupSummaryKey;
      options.activeGroupSummaryDomain.value = groupSummaryResetState.activeGroupSummaryDomain;
    }
    const groupVisualState = options.resolveRoutePresetGroupVisualState({
      groupSampleLimitRaw,
      groupSortRaw,
      groupCollapsedRaw,
      sampleLimits: ((options.listProfile?.value?.grouping || {}).sample_limits || []) as number[],
      defaultSampleLimit: (options.listProfile?.value?.grouping || {}).default_sample_limit as number | undefined,
      sortDirections: (((options.listProfile?.value?.grouping || {}).sort || {}).directions || []) as string[],
      defaultSortDirection: ((options.listProfile?.value?.grouping || {}).sort || {}).default_direction as string | undefined,
    });
    setIfDiff(options.groupSampleLimit, groupVisualState.groupSampleLimit);
    setIfDiff(options.groupSort, groupVisualState.groupSort);
    setIfDiff(options.collapsedGroupKeys, groupVisualState.collapsedList);
    const parsedGroupPages = options.parseGroupPageOffsets(groupPageRaw);
    const currentGroupPages = options.groupPageOffsets.value;
    const hasGroupPageStateChanged = options.hasRoutePresetGroupPageStateChanged({
      parsedGroupPages,
      currentGroupPages,
    });
    const nextGroupPageState = options.resolveRoutePresetGroupPageState({
      parsedGroupPages,
      currentGroupPages,
    });
    if (hasGroupPageStateChanged) {
      options.groupPageOffsets.value = nextGroupPageState.nextGroupPages;
      changed = true;
    }
    const trackingState = options.resolveRoutePresetTrackingState({
      preset,
      presetFilter,
      savedFilter,
      groupBy,
      lastTrackedPreset: options.lastTrackedPreset.value,
    });
    options.lastTrackedPreset.value = trackingState.nextTrackedPreset;
    if (trackingState.shouldTrackPresetApply && preset) {
      void options.trackUsageEvent('workspace.preset.apply', { preset, view: 'action' }).catch(() => {});
    }
    return changed;
  }

  function clearRoutePreset() {
    options.appliedPresetLabel.value = '';
    options.routeContextSource.value = '';
    const nextQuery = options.buildActionViewClearedPresetQuery(options.routeQueryMap.value);
    void options.trackUsageEvent('workspace.preset.clear', { view: 'action' }).catch(() => {});
    options.replaceCurrentRouteQuery(nextQuery);
  }

  function applyRoutePatchAndReload(patch: Record<string, unknown>) {
    const query = options.buildActionViewPatchedRouteQuery(options.routeQueryMap.value, patch);
    options.replaceCurrentRouteQuery(query);
    void options.load();
  }

  function syncRouteListState(extra?: Record<string, unknown>) {
    const query = options.buildActionViewSyncedRouteQuery(
      options.routeQueryMap.value,
      options.buildActionViewRouteSyncStatePayload({
        searchTerm: options.searchTerm.value,
        sortValue: options.sortValue.value,
        filterValue: options.filterValue.value,
        groupSampleLimit: options.groupSampleLimit.value,
        groupSort: options.groupSort.value,
        defaultGroupSampleLimit: options.listProfile.value?.grouping?.default_sample_limit,
        defaultGroupSort: options.listProfile.value?.grouping?.sort?.default_direction === 'asc'
          || options.listProfile.value?.grouping?.sort?.default_direction === 'desc'
          ? options.listProfile.value.grouping.sort.default_direction
          : undefined,
        collapsedGroupKeys: options.collapsedGroupKeys.value,
        groupPageOffsets: options.groupPageOffsets.value,
        activeGroupByField: options.activeGroupByField.value,
        groupWindowOffset: options.groupWindowOffset.value,
        groupQueryFingerprint: options.groupQueryFingerprint.value,
        groupWindowId: options.groupWindowId.value,
        groupWindowDigest: options.groupWindowDigest.value,
        groupWindowIdentityKey: options.groupWindowIdentityKey.value,
        extra: options.resolveRouteSyncExtra(extra),
      }),
    );
    options.replaceCurrentRouteQuery(query);
  }

  function restartLoadWithRouteSync(extra?: Record<string, unknown>) {
    syncRouteListState(extra);
    const shouldAwaitLoad = options.resolveRouteSyncShouldAwaitLoad('await');
    if (!shouldAwaitLoad) return Promise.resolve();
    return options.load();
  }

  function syncRouteStateAndReload(extra?: Record<string, unknown>) {
    syncRouteListState(extra);
    const shouldAwaitLoad = options.resolveRouteSyncShouldAwaitLoad('fire_and_forget');
    if (shouldAwaitLoad) {
      void restartLoadWithRouteSync();
      return;
    }
    void options.load();
  }

  return {
    applyRoutePreset,
    clearRoutePreset,
    applyRoutePatchAndReload,
    syncRouteListState,
    syncRouteStateAndReload,
    restartLoadWithRouteSync,
  };
}
