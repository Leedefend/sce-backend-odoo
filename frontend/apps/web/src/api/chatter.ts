import { intentRequest } from './intents';
import type { ContractReasonCode } from './contractTypes';

export interface ChatterTimelineEntry {
  key: string;
  type: 'message' | 'attachment' | 'activity' | 'audit';
  typeLabel: string;
  title: string;
  meta: string;
  body: string;
  at?: string;
  id?: number;
  reason_code?: ContractReasonCode;
  attachment?: {
    id?: number;
    name?: string;
    mimetype?: string;
  };
}

export interface ChatterTimelineResponse {
  items: ChatterTimelineEntry[];
  counts?: {
    messages?: number;
    attachments?: number;
    activities?: number;
    audit?: number;
    total?: number;
  };
}

export async function postChatterMessage(params: {
  model: string;
  res_id: number;
  body: string;
  subject?: string;
  mode?: 'message' | 'note';
}) {
  return intentRequest<{ result: { message_id: number } }>({
    intent: 'chatter.post',
    params: {
      model: params.model,
      res_id: params.res_id,
      body: params.body,
      subject: params.subject,
      mode: params.mode,
    },
  });
}

export async function scheduleChatterActivity(params: {
  model: string;
  res_id: number;
  summary: string;
  note?: string;
  date_deadline?: string;
  activity_type_xmlid?: string;
}) {
  return intentRequest<{ result: { activity_id: number } }>({
    intent: 'chatter.activity.schedule',
    params: {
      model: params.model,
      res_id: params.res_id,
      summary: params.summary,
      note: params.note,
      date_deadline: params.date_deadline,
      activity_type_xmlid: params.activity_type_xmlid,
    },
  });
}

export async function fetchChatterTimeline(params: {
  model: string;
  res_id: number;
  limit?: number;
  include_audit?: boolean;
}) {
  return intentRequest<ChatterTimelineResponse>({
    intent: 'chatter.timeline',
    params: {
      model: params.model,
      res_id: params.res_id,
      limit: params.limit ?? 40,
      include_audit: params.include_audit ?? true,
    },
  });
}
