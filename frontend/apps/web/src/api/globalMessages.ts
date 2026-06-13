import { intentRequest } from './intents';

export interface GlobalMessageItem {
  id: number;
  body: string;
  author_id: number;
  author_name: string;
  recipient_partner_ids: number[];
  recipient_names: string[];
  conversation_key?: string;
  conversation_title?: string;
  date: string;
  is_outgoing: boolean;
}

export interface GlobalMessageConversation {
  key: string;
  title: string;
  participant_partner_ids: number[];
  participant_user_ids: number[];
  latest_message: GlobalMessageItem;
  latest_message_id: number;
  latest_date: string;
  unread_count: number;
}

export async function fetchGlobalConversations(params: {
  limit?: number;
} = {}) {
  return intentRequest<{ items: GlobalMessageConversation[]; total_unread?: number }>({
    intent: 'global.message.conversations',
    params: {
      limit: params.limit ?? 30,
    },
  });
}

export async function fetchGlobalMessages(params: {
  limit?: number;
  since_id?: number;
  conversation_key?: string;
}) {
  return intentRequest<{ items: GlobalMessageItem[]; latest_id?: number }>({
    intent: 'global.message.inbox',
    params: {
      limit: params.limit ?? 40,
      since_id: params.since_id || undefined,
      conversation_key: params.conversation_key || undefined,
    },
  });
}

export async function sendGlobalMessage(params: {
  recipient_user_ids: number[];
  body: string;
}) {
  return intentRequest<{ result: { message_id: number; success: boolean } }>({
    intent: 'global.message.send',
    params: {
      recipient_user_ids: params.recipient_user_ids,
      body: params.body,
    },
  });
}

export async function markGlobalMessagesRead(params: {
  conversation_key?: string;
  message_ids?: number[];
}) {
  return intentRequest<{ result: { updated: number } }>({
    intent: 'global.message.read',
    params: {
      conversation_key: params.conversation_key || undefined,
      message_ids: params.message_ids || undefined,
    },
  });
}
