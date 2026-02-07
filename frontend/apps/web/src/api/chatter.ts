import { intentRequest } from './intents';

export interface ChatterTimelineEntry {
  key: string;
  type: 'message' | 'attachment' | 'audit';
  typeLabel: string;
  title: string;
  meta: string;
  body: string;
  at?: string;
  id?: number;
  reason_code?: string;
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
    audit?: number;
    total?: number;
  };
}

export async function postChatterMessage(params: {
  model: string;
  res_id: number;
  body: string;
  subject?: string;
}) {
  return intentRequest<{ result: { message_id: number } }>({
    intent: 'chatter.post',
    params: {
      model: params.model,
      res_id: params.res_id,
      body: params.body,
      subject: params.subject,
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
