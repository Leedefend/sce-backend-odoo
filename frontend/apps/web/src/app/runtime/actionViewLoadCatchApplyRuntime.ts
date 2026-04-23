type LoadCatchState = {
  listTotalCount: number | null;
  projectScopeTotals: unknown;
  projectScopeMetrics: unknown;
  traceId: string;
  lastTraceId: string;
  statusError: string;
  statusRecordsLength: number;
  lastLatencyMs: number;
};

export function resolveLoadCatchListTotalState(options: {
  catchState: LoadCatchState;
}): number | null {
  return options.catchState.listTotalCount;
}

export function resolveLoadCatchProjectScopeState(options: {
  catchState: LoadCatchState;
}): {
  projectScopeTotals: unknown;
  projectScopeMetrics: unknown;
} {
  return {
    projectScopeTotals: options.catchState.projectScopeTotals,
    projectScopeMetrics: options.catchState.projectScopeMetrics,
  };
}

export function resolveLoadCatchTraceApplyState(options: {
  catchState: LoadCatchState;
}): {
  traceId: string;
  lastTraceId: string;
} {
  return {
    traceId: options.catchState.traceId,
    lastTraceId: options.catchState.lastTraceId,
  };
}

export function resolveLoadCatchStatusApplyInput(options: {
  catchState: LoadCatchState;
}): {
  error: string;
  recordsLength: number;
} {
  return {
    error: options.catchState.statusError,
    recordsLength: options.catchState.statusRecordsLength,
  };
}

export function resolveLoadCatchLatencyState(options: {
  catchState: LoadCatchState;
}): number {
  return options.catchState.lastLatencyMs;
}
