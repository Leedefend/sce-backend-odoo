export function resolveLoadCatchListApplyState(options: {
  catchState: { listTotalCount: number };
}): {
  listTotalCount: number;
} {
  return {
    listTotalCount: options.catchState.listTotalCount,
  };
}

export function resolveLoadCatchScopeApplyState(options: {
  catchState: {
    projectScopeTotals: Record<string, number>;
    projectScopeMetrics: Record<string, unknown>;
  };
}): {
  projectScopeTotals: Record<string, number>;
  projectScopeMetrics: Record<string, unknown>;
} {
  return {
    projectScopeTotals: options.catchState.projectScopeTotals,
    projectScopeMetrics: options.catchState.projectScopeMetrics,
  };
}

export function resolveLoadCatchTraceStatusApplyState(options: {
  catchState: {
    traceId: string;
    statusInput: { error: string; recordsLength: number };
  };
  deriveListStatusFn: (input: { error: string; recordsLength: number }) => string;
}): {
  traceId: string;
  lastTraceId: string;
  status: string;
} {
  return {
    traceId: options.catchState.traceId,
    lastTraceId: options.catchState.traceId,
    status: options.deriveListStatusFn(options.catchState.statusInput),
  };
}

export function resolveLoadCatchLatencyApplyState(options: {
  catchState: { lastLatencyMs: number };
}): {
  lastLatencyMs: number;
} {
  return {
    lastLatencyMs: options.catchState.lastLatencyMs,
  };
}
