import { intentRequest, intentRequestRaw } from './intents';
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
  search_term?: string;
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
    search_term: params.search_term,
    context: params.context ?? {},
  };
  return intentRequest<ApiDataListResult>({
    intent: 'api.data',
    params: payload,
  });
}

export async function listRecordsRaw(params: {
  model: string;
  fields?: string[] | '*';
  domain?: unknown[];
  limit?: number;
  offset?: number;
  order?: string;
  search_term?: string;
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
    search_term: params.search_term,
    context: params.context ?? {},
  };
  return intentRequestRaw<ApiDataListResult>({
    intent: 'api.data',
    params: payload,
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
    params: payload,
  });
}

export async function readRecordRaw(params: {
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
  return intentRequestRaw<ApiDataReadResult>({
    intent: 'api.data',
    params: payload,
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

export async function unlinkRecord(params: {
  model: string;
  ids: number[];
  context?: Record<string, unknown>;
}) {
  return intentRequest<{ ids: number[] }>({
    intent: 'api.data.unlink',
    params: {
      model: params.model,
      ids: params.ids,
      context: params.context ?? {},
    },
  });
}

export type ApiDataWriteContract = {
  id: number;
  model: string;
  written_fields: string[];
  values: Record<string, unknown>;
};

export type ApiDataExportCsvResult = {
  file_name: string;
  mime_type: string;
  content_b64: string;
  count: number;
  fields: string[];
};

export type ApiDataBatchItemResult = {
  id: number;
  ok: boolean;
  reason_code: string;
  message: string;
};

export type ApiDataBatchResult = {
  model: string;
  action: string;
  values: Record<string, unknown>;
  requested_ids: number[];
  succeeded: number;
  failed: number;
  results: ApiDataBatchItemResult[];
};

export async function writeRecordV6(params: {
  model: string;
  id: number;
  values: Record<string, unknown>;
  context?: Record<string, unknown>;
}) {
  return intentRequest<ApiDataWriteContract>({
    intent: 'api.data.write',
    params: {
      model: params.model,
      id: params.id,
      values: params.values,
      context: params.context ?? {},
    },
  });
}

export async function writeRecordV6Raw(params: {
  model: string;
  id: number;
  values: Record<string, unknown>;
  context?: Record<string, unknown>;
  ifMatch?: string;
}) {
  return intentRequestRaw<ApiDataWriteContract>({
    intent: 'api.data.write',
    params: {
      model: params.model,
      id: params.id,
      values: params.values,
      context: params.context ?? {},
      if_match: params.ifMatch,
    },
  });
}

export async function exportRecordsCsv(params: {
  model: string;
  fields?: string[] | '*';
  domain?: unknown[];
  ids?: number[];
  order?: string;
  limit?: number;
  context?: Record<string, unknown>;
}) {
  return intentRequest<ApiDataExportCsvResult>({
    intent: 'api.data',
    params: {
      op: 'export_csv',
      model: params.model,
      fields: params.fields ?? ['id', 'name'],
      domain: params.domain ?? [],
      ids: params.ids ?? [],
      order: params.order ?? '',
      limit: params.limit ?? 2000,
      context: params.context ?? {},
    },
  });
}

export async function batchUpdateRecords(params: {
  model: string;
  ids: number[];
  action?: 'archive' | 'activate' | 'assign' | string;
  assigneeId?: number;
  vals?: Record<string, unknown>;
  context?: Record<string, unknown>;
}) {
  return intentRequest<ApiDataBatchResult>({
    intent: 'api.data.batch',
    params: {
      model: params.model,
      ids: params.ids,
      action: params.action ?? '',
      assignee_id: params.assigneeId,
      vals: params.vals ?? {},
      context: params.context ?? {},
    },
  });
}
