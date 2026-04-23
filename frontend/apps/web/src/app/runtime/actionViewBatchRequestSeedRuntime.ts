type BatchRequest = {
  model: string;
  ids: number[];
  action: string;
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
  context: Record<string, unknown>;
  assigneeId?: number;
};

export function resolveBatchSeedSortedIds(ids: number[]): number[] {
  return [...ids].sort((a, b) => a - b);
}

export function resolveBatchIdempotencyPayload(options: {
  model: string;
  action: string;
  ids: number[];
  extra?: Record<string, unknown>;
}): Record<string, unknown> {
  return {
    model: options.model,
    action: options.action,
    ids: resolveBatchSeedSortedIds(options.ids),
    extra: options.extra || {},
  };
}

export function resolveBatchIdempotencyKey(options: {
  payload: Record<string, unknown>;
}): string {
  return `batch:${JSON.stringify(options.payload)}`;
}

export function resolveBatchActionLastRequestState(options: {
  model: string;
  ids: number[];
  action: string;
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
  context: Record<string, unknown>;
}): BatchRequest {
  return {
    model: options.model,
    ids: [...options.ids],
    action: options.action,
    ifMatchMap: options.ifMatchMap,
    idempotencyKey: options.idempotencyKey,
    context: options.context,
  };
}

export function resolveBatchAssignLastRequestState(options: {
  model: string;
  ids: number[];
  assigneeId: number;
  ifMatchMap: Record<number, string>;
  idempotencyKey: string;
  context: Record<string, unknown>;
}): BatchRequest {
  return {
    model: options.model,
    ids: [...options.ids],
    action: 'assign',
    assigneeId: options.assigneeId,
    ifMatchMap: options.ifMatchMap,
    idempotencyKey: options.idempotencyKey,
    context: options.context,
  };
}
