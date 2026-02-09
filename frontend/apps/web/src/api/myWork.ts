import { intentRequest } from './intents';

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
  action_label?: string;
  action_key?: string;
  reason_code?: string;
};

export type FailureMeta = {
  retryable?: boolean;
  error_category?: string;
  suggested_action?: string;
};

export type IdempotencyMeta = {
  request_id?: string;
  idempotency_key?: string;
  idempotency_fingerprint?: string;
  idempotent_replay?: boolean;
  replay_window_expired?: boolean;
  idempotency_replay_reason_code?: string;
  replay_from_audit_id?: number;
  replay_original_trace_id?: string;
  replay_age_ms?: number;
  replay_supported?: boolean;
  idempotency_deduplicated?: boolean;
  trace_id?: string;
};

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
  return intentRequest<MyWorkSummaryResponse>({
    intent: 'my.work.summary',
    params: {
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
    },
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
  reason_code: string;
  message: string;
  trace_id?: string;
} & FailureMeta;

export type MyWorkCompleteBatchResult = {
  source: string;
  success: boolean;
  reason_code: string;
  message: string;
  done_count: number;
  failed_count: number;
  completed_ids: number[];
  failed_items: MyWorkBatchFailedItem[];
  failed_retry_ids?: number[];
  failed_reason_summary: Array<{ reason_code: string; count: number }>;
  failed_retryable_summary?: { retryable: number; non_retryable: number };
  done_at: string;
} & IdempotencyMeta;

export async function completeMyWorkItemsBatch(params: {
  ids: number[];
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
