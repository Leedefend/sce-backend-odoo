import type { ActionViewGroupSummaryItem } from './actionViewLoadResultRuntime';
import {
  reconcileActionViewSelectedIds,
  resolveActionViewActiveGroupSummaryKey,
} from './actionViewLoadResultRuntime';
import { resolveLoadSuccessLatencyMs, resolveLoadSuccessStatusInput, resolveLoadSuccessTraceState } from './actionViewLoadSuccessRuntime';
import { resolveLoadTraceIdentity } from './actionViewLoadErrorRuntime';

export function resolveLoadFinalizeSummaryKeyState(options: {
  currentActiveKey: string;
  routeGroupValueRaw: unknown;
  summaryItems: ActionViewGroupSummaryItem[];
}): string {
  return resolveActionViewActiveGroupSummaryKey({
    currentActiveKey: options.currentActiveKey,
    routeGroupValueRaw: options.routeGroupValueRaw,
    summaryItems: options.summaryItems,
  });
}

export function resolveLoadFinalizeSelectedIdsState(options: {
  selectedIds: number[];
  records: Array<Record<string, unknown>>;
}): number[] {
  return reconcileActionViewSelectedIds({
    selectedIds: options.selectedIds,
    records: options.records,
  });
}

export function resolveLoadFinalizeColumnsState(options: {
  contractColumns: string[];
}): string[] {
  return [...options.contractColumns];
}

export function resolveLoadFinalizeStatusState(options: {
  recordsLength: number;
}): {
  error: string;
  recordsLength: number;
} {
  return resolveLoadSuccessStatusInput({
    recordsLength: options.recordsLength,
  });
}

export function resolveLoadFinalizeTraceTimingState(options: {
  metaTraceId: unknown;
  traceIdRaw: unknown;
  currentTraceId: string;
  currentLastTraceId: string;
  startedAt: number;
}): {
  traceId: string;
  lastTraceId: string;
  lastLatencyMs: number;
} {
  const resolvedTraceId = resolveLoadTraceIdentity({
    metaTraceId: options.metaTraceId,
    traceId: options.traceIdRaw,
  });
  const traceState = resolveLoadSuccessTraceState({
    resolvedTraceId,
    currentTraceId: options.currentTraceId,
    currentLastTraceId: options.currentLastTraceId,
  });
  return {
    traceId: traceState.traceId,
    lastTraceId: traceState.lastTraceId,
    lastLatencyMs: resolveLoadSuccessLatencyMs({
      startedAt: options.startedAt,
    }),
  };
}
