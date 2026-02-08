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

export type MyWorkSummaryResponse = {
  generated_at: string;
  sections?: MyWorkSection[];
  summary: MyWorkSummaryItem[];
  items: MyWorkRecordItem[];
  facets?: {
    source_counts?: Array<{ key: string; count: number }>;
    reason_code_counts?: Array<{ key: string; count: number }>;
    section_counts?: Array<{ key: string; count: number }>;
  };
};

export async function fetchMyWorkSummary(limit = 20, limitEach = 8) {
  return intentRequest<MyWorkSummaryResponse>({
    intent: 'my.work.summary',
    params: { limit, limit_each: limitEach },
  });
}

export async function completeMyWorkItem(params: { id: number; source: string; note?: string }) {
  return intentRequest<{
    id: number;
    source: string;
    success: boolean;
    reason_code: string;
    message: string;
    retryable?: boolean;
    error_category?: string;
    suggested_action?: string;
    done_at: string;
  }>({
    intent: 'my.work.complete',
    params,
  });
}

export async function completeMyWorkItemsBatch(params: { ids: number[]; source: string; note?: string }) {
  return intentRequest<{
    source: string;
    success: boolean;
    reason_code: string;
    message: string;
    done_count: number;
    failed_count: number;
    completed_ids: number[];
    failed_items: Array<{ id: number; reason_code: string; message: string }>;
    failed_reason_summary: Array<{ reason_code: string; count: number }>;
    done_at: string;
  }>({
    intent: 'my.work.complete_batch',
    params,
  });
}
