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
    done_at: string;
  }>({
    intent: 'my.work.complete',
    params,
  });
}
