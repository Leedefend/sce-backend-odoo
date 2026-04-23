type LoadErrorState = {
  message: string;
  recordsLength: number;
};

export function resolveLoadMissingActionIdErrorState(): LoadErrorState {
  return {
    message: 'Action id missing',
    recordsLength: 0,
  };
}

export function resolveLoadMissingContractViewTypeErrorState(): LoadErrorState {
  return {
    message: 'missing contract view_type',
    recordsLength: 0,
  };
}

export function resolveLoadMissingTreeColumnsErrorState(options: {
  viewMode: string;
  contractColumns: string[];
}): LoadErrorState | null {
  if (options.viewMode !== 'tree') return null;
  if (options.contractColumns.length > 0) return null;
  return {
    message: 'missing contract columns for list/tree view',
    recordsLength: 0,
  };
}

export function resolveLoadTraceIdentity(options: {
  metaTraceId?: unknown;
  traceId?: unknown;
}): string {
  const metaTrace = String(options.metaTraceId || '').trim();
  if (metaTrace) return metaTrace;
  return String(options.traceId || '').trim();
}

export function resolveLoadCatchState(options: {
  errorMessage: string;
  traceId: string;
  startedAt: number;
}): {
  listTotalCount: null;
  projectScopeTotals: null;
  projectScopeMetrics: null;
  traceId: string;
  lastTraceId: string;
  statusError: string;
  statusRecordsLength: number;
  lastLatencyMs: number;
} {
  return {
    listTotalCount: null,
    projectScopeTotals: null,
    projectScopeMetrics: null,
    traceId: options.traceId,
    lastTraceId: options.traceId,
    statusError: options.errorMessage,
    statusRecordsLength: 0,
    lastLatencyMs: Date.now() - options.startedAt,
  };
}

