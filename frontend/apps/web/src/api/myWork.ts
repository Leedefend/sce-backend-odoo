import { intentRequest } from './intents';

export type MyWorkSummaryItem = {
  key: 'todo' | 'owned' | 'mentions' | 'following' | string;
  label: string;
  count: number;
  scene_key: string;
};

export type MyWorkRecordItem = {
  id: number;
  title: string;
  model: string;
  record_id: number;
  deadline?: string;
  scene_key: string;
};

export type MyWorkSummaryResponse = {
  generated_at: string;
  summary: MyWorkSummaryItem[];
  items: MyWorkRecordItem[];
};

export async function fetchMyWorkSummary(limit = 20) {
  return intentRequest<MyWorkSummaryResponse>({
    intent: 'my.work.summary',
    params: { limit },
  });
}
