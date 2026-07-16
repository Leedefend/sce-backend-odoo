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
  action_label?: string;
  action_key?: string;
  reason_code?: string;
  priority?: 'high' | 'medium' | 'low' | string;
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
  product_workspace?: ProductMyWorkWorkspace;
};

export type ProductMyWorkAction = {
  key: string;
  label: string;
  intent: string;
  params: { id?: number; action?: string };
  requires_reason?: boolean;
  reason_label?: string;
  reason_help?: string;
  next_state?: string;
  presentation?: {
    tier?: 'primary' | 'secondary' | 'overflow' | string;
    semantic?: 'default' | 'destructive' | string;
    requires_confirmation?: boolean;
    requires_reason?: boolean;
  };
};

export type ProductMyWorkMoney = {
  value: number | null;
  currency: string;
  currency_symbol?: string;
  digits?: number;
};

export type ProductMyWorkFact = {
  key: string;
  label: string;
  value?: string;
  display_role?: 'text' | 'money' | 'datetime' | string;
  money?: ProductMyWorkMoney;
};

export type ProductMyWorkItem = {
  key: string;
  section: 'todo' | 'initiated' | 'completed' | string;
  business_type: string;
  record: { label: string };
  state: { key: string; label: string };
  initiated_at?: string;
  updated_at?: string;
  facts: ProductMyWorkFact[];
  search_text: string;
  sort_values: Record<string, string | number | null>;
  actions: ProductMyWorkAction[];
  completed_event?: { code?: string; label?: string; at?: string };
  target: { route: string; model: string; record_id: number; action_xmlid?: string; menu_xmlid?: string };
  source_authority: string;
};

export type ProductMyWorkWorkspace = {
  version: string;
  query_scope: { user_id: number; company_ids: number[]; project_id?: number };
  sections: Array<{ key: string; label: string; count: number; items: ProductMyWorkItem[] }>;
  counts: Record<string, number>;
  total: number;
  completed_unavailable_reason?: string;
  presentation: {
    description: string;
    search_label: string;
    search_placeholder: string;
    default_sort: string;
    sort_options: Array<{ key: string; label: string; kind: 'text_desc' | 'text_asc' | 'number_desc' | 'number_asc' | string }>;
    quick_links: Array<{ key: string; label: string; detail?: string; route: string }>;
  };
  source_authority: string;
};

export async function executeProductMyWorkAction(action: ProductMyWorkAction, reason = '') {
  return intentRequest<{ success?: boolean; message?: string }>({
    intent: action.intent,
    params: {
      ...action.params,
      ...(action.requires_reason ? { reason } : {}),
    },
  });
}

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
    product_workspace: true,
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
