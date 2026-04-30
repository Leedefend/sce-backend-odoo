type Dict = Record<string, unknown>;
type StatusInput = { error: string; recordsLength: number };

type ApplyLoadSuccessOptions = {
  result: Dict;
  contractColumns: string[];
  baseDomain: unknown[];
  requestContext: Dict;
  requestContextRaw: string;
  startedAt: number;
  routeQueryMap: Dict;
  routeGroupValueRaw: unknown;
  activeGroupByField: string;
  groupSampleLimit: number;
  searchTerm: string;
  sortLabel: string;
  pageMode: string;
  hasActiveField: boolean;
  activeField: string;
  resolvedModel: string;
  resolveEffectiveFilterDomainRaw: () => string;
  pageText: (key: string, fallback: string) => string;
  fetchScopedTotal: (input: Dict) => Promise<number>;
  fetchProjectScopeMetrics: (input: Dict) => Promise<Array<Record<string, unknown>>>;
  restartLoadWithRouteSync: (patch: Dict) => Promise<void>;
  syncRouteListState: (patch: Dict) => void;
  normalizeGroupedRouteState: () => void;
  hydrateGroupedRowsByOffset: () => void | Promise<void>;
  deriveListStatus: (statusInput: StatusInput) => 'idle' | 'loading' | 'ok' | 'empty' | 'error';
  readTotalFromListResult: (resultDataRaw: unknown) => number | null;
  buildGroupKey: (groupByField: string, groupValue: unknown) => string;
  normalizeGroupPageOffset: (value: unknown) => number;
  resolveActionViewGroupPagingState: (input: Dict) => {
    resultData: Dict;
    groupPaging: Dict;
    effectiveGroupOffset: number;
    responseGroupFingerprint: string;
  };
  resolveGroupPagingIdentityApplyState: (input: Dict) => {
    groupWindowOffset: number;
    groupWindowId: string;
    groupQueryFingerprint: string;
    groupWindowDigest: string;
    groupWindowIdentityKey: string;
  };
  resolveActionViewRouteSnapshot: (queryMap: Dict) => Dict;
  resolveLoadGroupRouteSyncPlan: (input: Dict) => { resetPatch?: Dict; syncPatches?: Dict[] };
  resolveLoadRouteResetApplyState: (input: Dict) => {
    shouldReset: boolean;
    patch?: Dict;
    groupWindowOffset: number;
    groupPageOffsets: Record<string, number>;
    collapsedGroupKeys: string[];
  };
  resolveLoadGroupRouteSyncPatch: (input: Dict) => Dict;
  resolveLoadRouteSyncApplyState: (input: Dict) => { shouldSync: boolean; patch?: Dict };
  resolveLoadListTotalApplyState: (input: Dict) => { listTotalCount: number | null };
  resolveLoadSuccessProjectScopeApplyState: (input: Dict) => Promise<Dict>;
  resolveProjectScopeApplyState: (input: Dict) => {
    projectScopeTotals: Record<string, number>;
    projectScopeMetrics: Array<Record<string, unknown>>;
  };
  resolveLoadSuccessRecordsState: (input: Dict) => Array<Record<string, unknown>>;
  resolveLoadGroupSummaryApplyState: (input: Dict) => {
    groupSummaryItems: Array<Record<string, unknown>>;
  };
  resolveLoadSuccessGroupSummaryState: (input: Dict) => Array<Record<string, unknown>>;
  resolveLoadSuccessWindowApplyState: (input: Dict) => Dict;
  resolveWindowMetricsApplyState: (input: Dict) => {
    groupWindowCount: number;
    groupWindowStart: number;
    groupWindowEnd: number;
    groupWindowTotal: number;
    groupWindowNextOffset: number;
    groupWindowPrevOffset: number;
  };
  resolveLoadGroupedRowsApplyState: (input: Dict) => {
    groupedRows: Array<Record<string, unknown>>;
  };
  resolveLoadSuccessGroupedRowsState: (input: Dict) => Array<Record<string, unknown>>;
  resolveLoadFinalizeApplyState: (input: Dict) => {
    activeGroupSummaryKey: string;
    selectedIds: number[];
    columns: string[];
    statusInput: StatusInput;
  };
  resolveLoadFinalizeSummaryKeyState: (input: Dict) => string;
  resolveLoadFinalizeSelectedIdsState: (input: Dict) => number[];
  resolveLoadFinalizeColumnsState: (input: Dict) => string[];
  resolveLoadFinalizeStatusState: (input: Dict) => StatusInput;
  resolveLoadTraceApplyState: (input: Dict) => {
    traceId: string;
    lastTraceId: string;
    lastLatencyMs: number | null;
  };
  resolveLoadFinalizeTraceTimingState: (input: Dict) => {
    traceId: string;
    lastTraceId: string;
    lastLatencyMs: number | null;
  };
  groupWindowOffsetRef: { value: number };
  groupWindowIdRef: { value: string };
  groupQueryFingerprintRef: { value: string };
  groupWindowDigestRef: { value: string };
  groupWindowIdentityKeyRef: { value: string };
  groupPageOffsetsRef: { value: Record<string, number> };
  collapsedGroupKeysRef: { value: string[] };
  listTotalCountRef: { value: number | null };
  projectScopeTotalsRef: { value: Record<string, number> };
  projectScopeMetricsRef: { value: Array<Record<string, unknown>> };
  recordsRef: { value: Array<Record<string, unknown>> };
  groupSummaryItemsRef: { value: Array<Record<string, unknown>> };
  groupWindowCountRef: { value: number };
  groupWindowStartRef: { value: number };
  groupWindowEndRef: { value: number };
  groupWindowTotalRef: { value: number };
  groupWindowNextOffsetRef: { value: number };
  groupWindowPrevOffsetRef: { value: number };
  groupedRowsRef: { value: Array<Record<string, unknown>> };
  activeGroupSummaryKeyRef: { value: string };
  selectedIdsRef: { value: number[] };
  columnsRef: { value: string[] };
  statusRef: { value: 'idle' | 'loading' | 'ok' | 'empty' | 'error' };
  traceIdRef: { value: string };
  lastTraceIdRef: { value: string };
  lastLatencyMsRef: { value: number | null };
};

export function useActionViewLoadSuccessRuntime() {
  async function applyLoadSuccess(options: ApplyLoadSuccessOptions): Promise<void> {
    const pagingState = options.resolveActionViewGroupPagingState({
      resultDataRaw: options.result.data,
      fallbackGroupWindowOffset: options.groupWindowOffsetRef.value,
    });
    const groupPaging = pagingState.groupPaging;
    const effectiveGroupOffset = pagingState.effectiveGroupOffset;
    const responseGroupFingerprint = pagingState.responseGroupFingerprint;
    const groupIdentityState = options.resolveGroupPagingIdentityApplyState({
      pagingState,
      responseGroupFingerprint,
    });
    options.groupWindowOffsetRef.value = groupIdentityState.groupWindowOffset;
    options.groupWindowIdRef.value = groupIdentityState.groupWindowId;
    options.groupQueryFingerprintRef.value = groupIdentityState.groupQueryFingerprint;
    options.groupWindowDigestRef.value = groupIdentityState.groupWindowDigest;
    options.groupWindowIdentityKeyRef.value = groupIdentityState.groupWindowIdentityKey;

    const routeSnapshot = options.resolveActionViewRouteSnapshot(options.routeQueryMap);
    const routeSyncPlan = options.resolveLoadGroupRouteSyncPlan({
      activeGroupByField: options.activeGroupByField,
      effectiveGroupOffset,
      routeSnapshot,
      responseGroupFingerprint,
      groupWindowId: options.groupWindowIdRef.value,
      groupWindowDigest: options.groupWindowDigestRef.value,
      groupWindowIdentityKey: options.groupWindowIdentityKeyRef.value,
    });
    const routeResetState = options.resolveLoadRouteResetApplyState({
      resetPatch: routeSyncPlan.resetPatch,
    });
    if (routeResetState.shouldReset && routeResetState.patch) {
      options.groupWindowOffsetRef.value = routeResetState.groupWindowOffset;
      options.groupPageOffsetsRef.value = routeResetState.groupPageOffsets;
      options.collapsedGroupKeysRef.value = routeResetState.collapsedGroupKeys;
      await options.restartLoadWithRouteSync(routeResetState.patch);
      return;
    }

    const syncPatch = options.resolveLoadGroupRouteSyncPatch({ syncPatches: routeSyncPlan.syncPatches });
    const routeSyncState = options.resolveLoadRouteSyncApplyState({ syncPatch });
    if (routeSyncState.shouldSync && routeSyncState.patch) {
      options.syncRouteListState(routeSyncState.patch);
    }

    const resultData = pagingState.resultData;
    const listTotalState = options.resolveLoadListTotalApplyState({ resultData, readTotalFromListResultFn: options.readTotalFromListResult });
    options.listTotalCountRef.value = listTotalState.listTotalCount;

    const projectScopeState = await options.resolveLoadSuccessProjectScopeApplyState({
      pageMode: options.pageMode,
      hasActiveField: options.hasActiveField,
      activeField: options.activeField,
      model: options.resolvedModel,
      baseDomain: options.baseDomain,
      domainRaw: options.resolveEffectiveFilterDomainRaw(),
      context: options.requestContext,
      contextRaw: options.requestContextRaw,
      searchTerm: options.searchTerm,
      order: options.sortLabel,
      fetchScopedTotal: options.fetchScopedTotal,
      fetchProjectScopeMetrics: options.fetchProjectScopeMetrics,
    });
    const projectScopeApplyState = options.resolveProjectScopeApplyState({ projectScopeState });
    options.projectScopeTotalsRef.value = projectScopeApplyState.projectScopeTotals;
    options.projectScopeMetricsRef.value = projectScopeApplyState.projectScopeMetrics;

    options.recordsRef.value = options.resolveLoadSuccessRecordsState({ resultDataRaw: resultData });
    const groupSummaryState = options.resolveLoadGroupSummaryApplyState({
      resultData,
      emptyLabel: options.pageText('group_label_unset', '未设置'),
      maxItems: 12,
      buildGroupKey: options.buildGroupKey,
      resolveLoadSuccessGroupSummaryStateFn: options.resolveLoadSuccessGroupSummaryState,
    });
    options.groupSummaryItemsRef.value = groupSummaryState.groupSummaryItems;

    const windowState = options.resolveLoadSuccessWindowApplyState({
      groupPagingRaw: groupPaging,
      effectiveGroupOffset,
      summaryLength: options.groupSummaryItemsRef.value.length,
    });
    const windowMetricsState = options.resolveWindowMetricsApplyState({ windowState });
    options.groupWindowCountRef.value = windowMetricsState.groupWindowCount;
    options.groupWindowStartRef.value = windowMetricsState.groupWindowStart;
    options.groupWindowEndRef.value = windowMetricsState.groupWindowEnd;
    options.groupWindowTotalRef.value = windowMetricsState.groupWindowTotal;
    options.groupWindowNextOffsetRef.value = windowMetricsState.groupWindowNextOffset;
    options.groupWindowPrevOffsetRef.value = windowMetricsState.groupWindowPrevOffset;

    const groupedRowsState = options.resolveLoadGroupedRowsApplyState({
      resultData,
      groupPaging,
      groupSampleLimit: options.groupSampleLimit,
      groupPageOffsets: options.groupPageOffsetsRef.value,
      emptyLabel: options.pageText('group_label_unset', '未设置'),
      maxItems: 12,
      buildGroupKey: options.buildGroupKey,
      normalizeGroupPageOffset: options.normalizeGroupPageOffset,
      resolveLoadSuccessGroupedRowsStateFn: options.resolveLoadSuccessGroupedRowsState,
    });
    options.groupedRowsRef.value = groupedRowsState.groupedRows;

    options.normalizeGroupedRouteState();
    void options.hydrateGroupedRowsByOffset();

    const finalizeState = options.resolveLoadFinalizeApplyState({
      routeGroupValueRaw: options.routeGroupValueRaw,
      activeGroupSummaryKey: options.activeGroupSummaryKeyRef.value,
      groupSummaryItems: options.groupSummaryItemsRef.value,
      selectedIds: options.selectedIdsRef.value,
      records: options.recordsRef.value,
      contractColumns: options.contractColumns,
      resolveLoadFinalizeSummaryKeyStateFn: options.resolveLoadFinalizeSummaryKeyState,
      resolveLoadFinalizeSelectedIdsStateFn: options.resolveLoadFinalizeSelectedIdsState,
      resolveLoadFinalizeColumnsStateFn: options.resolveLoadFinalizeColumnsState,
      resolveLoadFinalizeStatusStateFn: options.resolveLoadFinalizeStatusState,
    });
    options.activeGroupSummaryKeyRef.value = finalizeState.activeGroupSummaryKey;
    options.selectedIdsRef.value = finalizeState.selectedIds;
    options.columnsRef.value = finalizeState.columns;
    options.statusRef.value = options.deriveListStatus(finalizeState.statusInput);

    const resultMeta = (options.result.meta || {}) as Dict;
    const traceTimingState = options.resolveLoadTraceApplyState({
      resultMetaTraceIdRaw: resultMeta.trace_id,
      resultTraceIdRaw: options.result.traceId,
      currentTraceId: options.traceIdRef.value,
      currentLastTraceId: options.lastTraceIdRef.value,
      startedAt: options.startedAt,
      resolveLoadFinalizeTraceTimingStateFn: options.resolveLoadFinalizeTraceTimingState,
    });
    options.traceIdRef.value = traceTimingState.traceId;
    options.lastTraceIdRef.value = traceTimingState.lastTraceId;
    options.lastLatencyMsRef.value = traceTimingState.lastLatencyMs;
  }

  return {
    applyLoadSuccess,
  };
}
