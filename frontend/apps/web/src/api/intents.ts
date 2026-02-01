import { apiRequest } from './client';
import type { IntentEnvelope } from '@sc/schema';

export interface IntentPayload {
  intent: string;
  params?: Record<string, unknown>;
  context?: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

function buildHeaders(intent: string, traceId: string) {
  const headers: Record<string, string> = {
    'X-Trace-Id': traceId,
  };
  if (intent === 'login' || intent === 'auth.login') {
    headers['X-Anonymous-Intent'] = 'true';
  }
  return headers;
}

function generateTraceId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `trace_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export async function intentRequest<T>(payload: IntentPayload) {
  const traceId = generateTraceId();
  try {
    const response = await apiRequest<IntentEnvelope<T>>('/api/v1/intent', {
      method: 'POST',
      headers: buildHeaders(payload.intent, traceId),
      body: JSON.stringify(payload),
    });

    // eslint-disable-next-line no-console
    console.info(`[trace] intent=${payload.intent} status=ok trace=${traceId}`);

    if (response && typeof response === 'object' && 'data' in response) {
      return response.data as T;
    }

    return response as T;
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn(`[trace] intent=${payload.intent} status=error trace=${traceId}`);
    throw err;
  }
}
