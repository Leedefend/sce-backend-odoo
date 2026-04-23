type Dict = Record<string, unknown>;

export function resolveLoadListTotalApplyState(options: {
  resultData: Dict;
  readTotalFromListResultFn: (data: Dict) => number;
}): {
  listTotalCount: number;
} {
  return {
    listTotalCount: options.readTotalFromListResultFn(options.resultData),
  };
}

export function resolveLoadGroupSummaryApplyState(options: {
  resultData: Dict;
  emptyLabel: string;
  maxItems: number;
  buildGroupKey: (value: unknown) => string;
  resolveLoadSuccessGroupSummaryStateFn: (input: {
    groupSummaryRaw: unknown;
    emptyLabel: string;
    maxItems: number;
    buildGroupKey: (value: unknown) => string;
  }) => Array<Record<string, unknown>>;
}): {
  groupSummaryItems: Array<Record<string, unknown>>;
} {
  return {
    groupSummaryItems: options.resolveLoadSuccessGroupSummaryStateFn({
      groupSummaryRaw: options.resultData.group_summary,
      emptyLabel: options.emptyLabel,
      maxItems: options.maxItems,
      buildGroupKey: options.buildGroupKey,
    }),
  };
}

export function resolveLoadGroupedRowsApplyState(options: {
  resultData: Dict;
  groupPaging: Dict;
  groupSampleLimit: number;
  groupPageOffsets: Record<string, number>;
  emptyLabel: string;
  maxItems: number;
  buildGroupKey: (value: unknown) => string;
  normalizeGroupPageOffset: (raw: unknown) => number;
  resolveLoadSuccessGroupedRowsStateFn: (input: {
    resultDataRaw: unknown;
    groupPagingRaw: unknown;
    groupSampleLimit: number;
    groupPageOffsets: Record<string, number>;
    emptyLabel: string;
    maxItems: number;
    buildGroupKey: (value: unknown) => string;
    normalizeGroupPageOffset: (raw: unknown) => number;
  }) => Array<Record<string, unknown>>;
}): {
  groupedRows: Array<Record<string, unknown>>;
} {
  return {
    groupedRows: options.resolveLoadSuccessGroupedRowsStateFn({
      resultDataRaw: options.resultData,
      groupPagingRaw: options.groupPaging,
      groupSampleLimit: options.groupSampleLimit,
      groupPageOffsets: options.groupPageOffsets,
      emptyLabel: options.emptyLabel,
      maxItems: options.maxItems,
      buildGroupKey: options.buildGroupKey,
      normalizeGroupPageOffset: options.normalizeGroupPageOffset,
    }),
  };
}

export function resolveLoadFinalizeApplyState(options: {
  routeGroupValueRaw: unknown;
  activeGroupSummaryKey: string;
  groupSummaryItems: Array<Record<string, unknown>>;
  selectedIds: number[];
  records: Array<Record<string, unknown>>;
  contractColumns: string[];
  resolveLoadFinalizeSummaryKeyStateFn: (input: {
    currentActiveKey: string;
    routeGroupValueRaw: unknown;
    summaryItems: Array<Record<string, unknown>>;
  }) => string;
  resolveLoadFinalizeSelectedIdsStateFn: (input: {
    selectedIds: number[];
    records: Array<Record<string, unknown>>;
  }) => number[];
  resolveLoadFinalizeColumnsStateFn: (input: { contractColumns: string[] }) => string[];
  resolveLoadFinalizeStatusStateFn: (input: { recordsLength: number }) => { error: string; recordsLength: number };
}): {
  activeGroupSummaryKey: string;
  selectedIds: number[];
  columns: string[];
  statusInput: { error: string; recordsLength: number };
} {
  const statusInput = options.resolveLoadFinalizeStatusStateFn({ recordsLength: options.records.length });
  return {
    activeGroupSummaryKey: options.resolveLoadFinalizeSummaryKeyStateFn({
      currentActiveKey: options.activeGroupSummaryKey,
      routeGroupValueRaw: options.routeGroupValueRaw,
      summaryItems: options.groupSummaryItems,
    }),
    selectedIds: options.resolveLoadFinalizeSelectedIdsStateFn({
      selectedIds: options.selectedIds,
      records: options.records,
    }),
    columns: options.resolveLoadFinalizeColumnsStateFn({ contractColumns: options.contractColumns }),
    statusInput,
  };
}

export function resolveLoadTraceApplyState(options: {
  resultMetaTraceIdRaw: unknown;
  resultTraceIdRaw: unknown;
  currentTraceId: string;
  currentLastTraceId: string;
  startedAt: number;
  resolveLoadFinalizeTraceTimingStateFn: (input: {
    metaTraceId: unknown;
    traceIdRaw: unknown;
    currentTraceId: string;
    currentLastTraceId: string;
    startedAt: number;
  }) => {
    traceId: string;
    lastTraceId: string;
    lastLatencyMs: number;
  };
}): {
  traceId: string;
  lastTraceId: string;
  lastLatencyMs: number;
} {
  return options.resolveLoadFinalizeTraceTimingStateFn({
    metaTraceId: options.resultMetaTraceIdRaw,
    traceIdRaw: options.resultTraceIdRaw,
    currentTraceId: options.currentTraceId,
    currentLastTraceId: options.currentLastTraceId,
    startedAt: options.startedAt,
  });
}
