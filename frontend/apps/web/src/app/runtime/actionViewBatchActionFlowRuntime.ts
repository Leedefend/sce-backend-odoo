import { resolveBatchActionGuard } from './actionViewBatchRuntime';

export function resolveBatchActionTargetModel(options: {
  resolvedModelRaw: unknown;
  routeModelRaw: unknown;
}): string {
  return String(options.resolvedModelRaw || options.routeModelRaw || '').trim();
}

export function resolveBatchActionDeleteMode(options: {
  contractDeleteModeRaw: unknown;
}): string {
  return String(options.contractDeleteModeRaw || 'unlink').trim().toLowerCase() || 'unlink';
}

export function resolveBatchActionGuardDecision(options: {
  targetModel: string;
  selectedCount: number;
  action: 'archive' | 'activate' | 'delete';
  hasActiveField: boolean;
  deleteMode: string;
}): { ok: boolean; reason?: string } {
  return resolveBatchActionGuard({
    targetModel: options.targetModel,
    selectedCount: options.selectedCount,
    action: options.action,
    hasActiveField: options.hasActiveField,
    deleteMode: options.deleteMode,
  });
}

export function resolveBatchDeleteExecutionSeed(options: {
  selectedIds: number[];
  buildIfMatchMap: (ids: number[]) => Record<number, string>;
  buildIdempotencyKey: (action: string, ids: number[], extra: Record<string, unknown>) => string;
}): {
  requestAction: 'unlink';
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
} {
  return {
    requestAction: 'unlink',
    ifMatchMap: options.buildIfMatchMap(options.selectedIds),
    idempotencyKey: options.buildIdempotencyKey('delete', options.selectedIds, { delete_mode: 'unlink' }),
  };
}

export function resolveBatchStandardExecutionSeed(options: {
  action: 'archive' | 'activate' | 'delete';
  selectedIds: number[];
  activeField: string;
  activeValue: boolean;
  buildIfMatchMap: (ids: number[]) => Record<number, string>;
  buildIdempotencyKey: (action: string, ids: number[], extra: Record<string, unknown>) => string;
}): {
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
} {
  const extra = String(options.activeField || '').trim()
    ? { [options.activeField]: options.activeValue }
    : {};
  return {
    ifMatchMap: options.buildIfMatchMap(options.selectedIds),
    idempotencyKey: options.buildIdempotencyKey(options.action, options.selectedIds, extra),
  };
}
