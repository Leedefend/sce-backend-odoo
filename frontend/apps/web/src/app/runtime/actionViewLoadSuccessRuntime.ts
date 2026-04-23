export function resolveLoadSuccessProjectScopeState(options: {
  totals: unknown;
  metrics: unknown;
}): {
  projectScopeTotals: unknown;
  projectScopeMetrics: unknown;
} {
  return {
    projectScopeTotals: options.totals,
    projectScopeMetrics: options.metrics,
  };
}

export function resolveLoadSuccessWindowState(options: {
  groupWindowCount: number;
  groupWindowStart: number;
  groupWindowEnd: number;
  groupWindowTotal: number;
  groupWindowNextOffset: number;
  groupWindowPrevOffset: number;
}): {
  groupWindowCount: number;
  groupWindowStart: number;
  groupWindowEnd: number;
  groupWindowTotal: number;
  groupWindowNextOffset: number;
  groupWindowPrevOffset: number;
} {
  return {
    groupWindowCount: options.groupWindowCount,
    groupWindowStart: options.groupWindowStart,
    groupWindowEnd: options.groupWindowEnd,
    groupWindowTotal: options.groupWindowTotal,
    groupWindowNextOffset: options.groupWindowNextOffset,
    groupWindowPrevOffset: options.groupWindowPrevOffset,
  };
}

export function resolveLoadSuccessStatusInput(options: {
  recordsLength: number;
}): {
  error: string;
  recordsLength: number;
} {
  return {
    error: '',
    recordsLength: options.recordsLength,
  };
}

export function resolveLoadSuccessTraceState(options: {
  resolvedTraceId: string;
  currentTraceId: string;
  currentLastTraceId: string;
}): {
  traceId: string;
  lastTraceId: string;
} {
  if (!options.resolvedTraceId) {
    return {
      traceId: options.currentTraceId,
      lastTraceId: options.currentLastTraceId,
    };
  }
  return {
    traceId: options.resolvedTraceId,
    lastTraceId: options.resolvedTraceId,
  };
}

export function resolveLoadSuccessLatencyMs(options: {
  startedAt: number;
}): number {
  return Date.now() - options.startedAt;
}

