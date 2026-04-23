import { resolveBatchAssignGuard } from './actionViewBatchRuntime';

export function resolveBatchAssignTargetModel(options: {
  resolvedModelRaw: unknown;
  routeModelRaw: unknown;
}): string {
  return String(options.resolvedModelRaw || options.routeModelRaw || '').trim();
}

export function resolveBatchAssignGuardDecision(options: {
  targetModel: string;
  selectedCount: number;
  hasAssigneeField: boolean;
  assigneeId: number;
}): { ok: boolean; reason?: string } {
  return resolveBatchAssignGuard({
    targetModel: options.targetModel,
    selectedCount: options.selectedCount,
    hasAssigneeField: options.hasAssigneeField,
    assigneeId: options.assigneeId,
  });
}

export function resolveBatchAssignExecutionSeed(options: {
  selectedIds: number[];
  assigneeId: number;
  buildIfMatchMap: (ids: number[]) => Record<number, string>;
  buildIdempotencyKey: (action: string, ids: number[], extra: Record<string, unknown>) => string;
}): {
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
} {
  return {
    ifMatchMap: options.buildIfMatchMap(options.selectedIds),
    idempotencyKey: options.buildIdempotencyKey('assign', options.selectedIds, { assignee_id: options.assigneeId }),
  };
}

export function resolveBatchAssignAssigneeLabel(options: {
  assigneeId: number;
  assigneeOptions: Array<{ id: number; name: string }>;
}): string {
  return options.assigneeOptions.find((opt) => opt.id === options.assigneeId)?.name || `#${options.assigneeId}`;
}

export function resolveBatchAssignFailureMessage(text: (key: string, fallback?: string) => string): string {
  return text('batch_msg_assign_failed', '批量指派失败');
}
