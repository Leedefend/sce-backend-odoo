import { intentRequest } from './intents';
import type {
  ApiDataListResult,
  ApiDataReadResult,
  ApiDataListRequest,
  ApiDataReadRequest,
} from '@sc/schema';

export async function listRecords(params: {
  model: string;
  fields?: string[] | '*';
  domain?: unknown[];
  limit?: number;
  offset?: number;
  order?: string;
  context?: Record<string, unknown>;
}) {
  const payload: ApiDataListRequest = {
    op: 'list',
    model: params.model,
    fields: params.fields ?? ['id', 'name'],
    domain: params.domain ?? [],
    limit: params.limit ?? 40,
    offset: params.offset ?? 0,
    order: params.order ?? '',
    context: params.context ?? {},
  };
  return intentRequest<ApiDataListResult>({
    intent: 'api.data',
    params: payload as Record<string, unknown>,
  });
}

export async function readRecord(params: {
  model: string;
  ids: number[];
  fields?: string[] | '*';
  context?: Record<string, unknown>;
}) {
  const payload: ApiDataReadRequest = {
    op: 'read',
    model: params.model,
    ids: params.ids,
    fields: params.fields ?? ['id', 'name'],
    context: params.context ?? {},
  };
  return intentRequest<ApiDataReadResult>({
    intent: 'api.data',
    params: payload as Record<string, unknown>,
  });
}

export async function createRecord(params: {
  model: string;
  vals: Record<string, unknown>;
  context?: Record<string, unknown>;
}) {
  return intentRequest<{ id: number }>({
    intent: 'api.data',
    params: {
      op: 'create',
      model: params.model,
      vals: params.vals,
      context: params.context ?? {},
    },
  });
}

export async function writeRecord(params: {
  model: string;
  ids: number[];
  vals: Record<string, unknown>;
  context?: Record<string, unknown>;
}) {
  return intentRequest<{ ids: number[] }>({
    intent: 'api.data',
    params: {
      op: 'write',
      model: params.model,
      ids: params.ids,
      vals: params.vals,
      context: params.context ?? {},
    },
  });
}
