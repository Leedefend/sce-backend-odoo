import { intentRequest } from './intents';
import type { ApiDataListResult, ApiDataReadResult } from '@sc/schema';

export async function listRecords(params: {
  model: string;
  fields?: string[] | '*';
  domain?: unknown[];
  limit?: number;
  offset?: number;
  order?: string;
  context?: Record<string, unknown>;
}) {
  return intentRequest<ApiDataListResult>({
    intent: 'api.data',
    params: {
      op: 'list',
      model: params.model,
      fields: params.fields ?? ['id', 'name'],
      domain: params.domain ?? [],
      limit: params.limit ?? 40,
      offset: params.offset ?? 0,
      order: params.order ?? '',
      context: params.context ?? {},
    },
  });
}

export async function readRecord(params: {
  model: string;
  ids: number[];
  fields?: string[] | '*';
  context?: Record<string, unknown>;
}) {
  return intentRequest<ApiDataReadResult>({
    intent: 'api.data',
    params: {
      op: 'read',
      model: params.model,
      ids: params.ids,
      fields: params.fields ?? ['id', 'name'],
      context: params.context ?? {},
    },
  });
}
