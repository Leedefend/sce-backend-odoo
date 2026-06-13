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
  activity?: {
    id?: number;
    assignee_user_id?: number;
    assignee_name?: string;
    deadline?: string;
    activity_type?: string;
    can_complete?: boolean;
    can_cancel?: boolean;
  };
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

export interface CollaborationUserOption {
  id: number;
  name: string;
  login?: string;
  email?: string;
  partner_id?: number;
  partner_name?: string;
}

export async function postChatterMessage(params: {
  model: string;
  res_id: number;
  body: string;
  subject?: string;
  mode?: 'message' | 'note';
  mention_user_ids?: number[];
}) {
  return intentRequest<{ result: { message_id: number } }>({
    intent: 'chatter.post',
    params: {
      model: params.model,
      res_id: params.res_id,
      body: params.body,
      subject: params.subject,
      mode: params.mode,
      mention_user_ids: params.mention_user_ids,
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
  user_id?: number;
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
      user_id: params.user_id,
    },
  });
}

export async function updateChatterActivity(params: {
  model: string;
  res_id: number;
  activity_id: number;
  action: 'done' | 'cancel';
  note?: string;
}) {
  return intentRequest<{ result: { activity_id: number; action: string } }>({
    intent: 'chatter.activity.update',
    params: {
      model: params.model,
      res_id: params.res_id,
      activity_id: params.activity_id,
      action: params.action,
      note: params.note,
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

export async function searchCollaborationUsers(params: {
  query?: string;
  limit?: number;
}) {
  return intentRequest<{ items: CollaborationUserOption[] }>({
    intent: 'collaboration.users.search',
    params: {
      query: params.query || '',
      limit: params.limit ?? 20,
    },
  });
}
