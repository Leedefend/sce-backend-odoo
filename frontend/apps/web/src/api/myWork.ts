import { intentRequest } from './intents';
import type {
  ContractFailureMeta,
  ContractIdempotencyMeta,
  ContractReasonCount,
  ContractReasonedFailure,
} from './contractTypes';

export type MyWorkSummaryItem = {
  key: 'todo' | 'owned' | 'mentions' | 'following' | string;
  label: string;
  count: number;
  scene_key: string;
};

export type MyWorkSection = {
  key: 'todo' | 'owned' | 'mentions' | 'following' | string;
  label: string;
  scene_key: string;
};

export type MyWorkRecordItem = {
  id: number;
  title: string;
  model: string;
  record_id: number;
  deadline?: string;
  scene_key: string;
  section?: string;
  section_label?: string;
  source?: string;
  source_label?: string;
  project_name?: string;
  action_label?: string;
  action_summary?: string;
  action_key?: string;
  reason_code?: string;
  priority?: 'high' | 'medium' | 'low' | string;
  can_complete?: boolean;
  complete_action?: {
    intent?: string;
    label?: string;
    enabled?: boolean;
    source?: string;
  };
  target?: {
    kind?: 'record' | 'scene' | 'action' | string;
    scene_key?: string;
    model?: string;
    record_id?: number;
    action_id?: number;
    menu_id?: number;
    route?: string;
  };
};

export type FailureMeta = ContractFailureMeta;
export type IdempotencyMeta = ContractIdempotencyMeta;

export type MyWorkSummaryResponse = {
  generated_at: string;
  sections?: MyWorkSection[];
  summary: MyWorkSummaryItem[];
  items: MyWorkRecordItem[];
  filters?: {
    section: string;
    source: string;
    reason_code: string;
    search: string;
    filtered_count: number;
    total_before_filter: number;
    sort_by?: string;
    sort_dir?: 'asc' | 'desc' | string;
    page?: number;
    page_size?: number;
    total_pages?: number;
  };
  status?: {
    state: 'READY' | 'EMPTY' | 'FILTER_EMPTY' | string;
    reason_code: string;
    message: string;
    hint: string;
  };
  facets?: {
    source_counts?: Array<{ key: string; count: number }>;
    reason_code_counts?: Array<{ key: string; count: number }>;
    section_counts?: Array<{ key: string; count: number }>;
    section_counts_filtered?: Array<{ key: string; count: number }>;
    priority_counts?: Array<{ key: string; count: number }>;
  };
  visibility?: {
    partial_data_hidden?: boolean;
    message?: string;
    restricted_sources?: Array<{
      model: string;
      readable: boolean;
      reason: string;
    }>;
  };
};

export async function fetchMyWorkSummary(
  limit = 20,
  limitEach = 8,
  options?: {
    page?: number;
    pageSize?: number;
    sortBy?: string;
    sortDir?: 'asc' | 'desc';
    section?: string;
    source?: string;
    reasonCode?: string;
    search?: string;
  },
) {
  const params = {
    limit,
    limit_each: limitEach,
    page: options?.page ?? 1,
    page_size: options?.pageSize ?? limit,
    sort_by: options?.sortBy ?? 'id',
    sort_dir: options?.sortDir ?? 'desc',
    section: options?.section ?? 'all',
    source: options?.source ?? 'all',
    reason_code: options?.reasonCode ?? 'all',
    search: options?.search ?? '',
  };
  return intentRequest<MyWorkSummaryResponse>({
    intent: 'my.work.summary',
    params,
  });
}

export type MyWorkCompleteResult = {
  id: number;
  source: string;
  success: boolean;
  reason_code: string;
  message: string;
  done_at: string;
} & FailureMeta &
  IdempotencyMeta;

export async function completeMyWorkItem(params: {
  id: number;
  source: string;
  note?: string;
  request_id?: string;
  idempotency_key?: string;
}) {
  return intentRequest<MyWorkCompleteResult>({
    intent: 'my.work.complete',
    params,
  });
}

export type MyWorkBatchFailedItem = {
  id: number;
} & ContractReasonedFailure;

export type MyWorkCompleteBatchResult = {
  execution_mode?: 'full' | 'retry' | string;
  source: string;
  success: boolean;
  reason_code: string;
  message: string;
  done_count: number;
  failed_count: number;
  completed_ids: number[];
  failed_items: MyWorkBatchFailedItem[];
  failed_retry_ids?: number[];
  failed_groups?: Array<{
    reason_code: string;
    count: number;
    retryable_count: number;
    suggested_action?: string;
    sample_ids?: number[];
  }>;
  retry_request?: {
    intent: 'my.work.complete_batch' | string;
    params?: {
      source?: string;
      retry_ids?: number[];
      note?: string;
      request_id?: string;
    };
  } | null;
  failed_reason_summary: ContractReasonCount[];
  failed_retryable_summary?: { retryable: number; non_retryable: number };
  todo_remaining?: number;
  done_at: string;
} & IdempotencyMeta;

export async function completeMyWorkItemsBatch(params: {
  ids: number[];
  retry_ids?: number[];
  source: string;
  note?: string;
  request_id?: string;
  idempotency_key?: string;
}) {
  return intentRequest<MyWorkCompleteBatchResult>({
    intent: 'my.work.complete_batch',
    params,
  });
}
