import { apiRequest } from './client';
import type { IntentEnvelope } from '@sc/schema';

export interface IntentPayload {
  intent: string;
  params?: Record<string, unknown>;
  context?: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

function buildHeaders(intent: string) {
  if (intent === 'login' || intent === 'auth.login') {
    return {
      'X-Anonymous-Intent': 'true',
    };
  }
  return undefined;
}

export async function intentRequest<T>(payload: IntentPayload) {
  const response = await apiRequest<IntentEnvelope<T>>('/api/v1/intent', {
    method: 'POST',
    headers: buildHeaders(payload.intent),
    body: JSON.stringify(payload),
  });

  if (response && typeof response === 'object' && 'data' in response) {
    return response.data as T;
  }

  return response as T;
}
