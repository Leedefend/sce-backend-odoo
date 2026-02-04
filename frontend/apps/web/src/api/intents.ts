import { apiRequestRaw, ApiError } from './client';
import type { IntentEnvelope } from '@sc/schema';
import { useSessionStore } from '../stores/session';

export interface IntentPayload {
  intent: string;
  params?: unknown;
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
  const session = useSessionStore();
  const startedAt = Date.now();
  try {
    const response = await apiRequestRaw<IntentEnvelope<T>>('/api/v1/intent', {
      method: 'POST',
      headers: buildHeaders(payload.intent, traceId),
      body: JSON.stringify(payload),
    });
    const resolvedTrace = response.traceId || traceId;
    session.recordIntentTrace({
      traceId: resolvedTrace,
      intent: payload.intent,
      latencyMs: Date.now() - startedAt,
      writeMode: payload.intent.includes('write') || payload.intent.includes('create') ? 'write' : 'read',
    });

    // eslint-disable-next-line no-console
    console.info(`[trace] intent=${payload.intent} status=ok trace=${resolvedTrace}`);

    if (response.body && typeof response.body === 'object' && 'data' in response.body) {
      return response.body.data as T;
    }

    return response.body as T;
  } catch (err) {
    const errorTrace = err instanceof ApiError ? err.traceId || traceId : traceId;
    session.recordIntentTrace({
      traceId: errorTrace,
      intent: payload.intent,
      latencyMs: Date.now() - startedAt,
      writeMode: payload.intent.includes('write') || payload.intent.includes('create') ? 'write' : 'read',
    });
    // eslint-disable-next-line no-console
    console.warn(`[trace] intent=${payload.intent} status=error trace=${errorTrace}`);
    throw err;
  }
}

export async function intentRequestRaw<T>(payload: IntentPayload) {
  const traceId = generateTraceId();
  const session = useSessionStore();
  const startedAt = Date.now();
  const response = await apiRequestRaw<IntentEnvelope<T>>('/api/v1/intent', {
    method: 'POST',
    headers: buildHeaders(payload.intent, traceId),
    body: JSON.stringify(payload),
  });
  const resolvedTrace = response.traceId || traceId;
  session.recordIntentTrace({
    traceId: resolvedTrace,
    intent: payload.intent,
    latencyMs: Date.now() - startedAt,
    writeMode: payload.intent.includes('write') || payload.intent.includes('create') ? 'write' : 'read',
  });

  if (response.body && typeof response.body === 'object' && 'data' in response.body) {
    return { data: response.body.data as T, meta: response.body.meta || {}, traceId: resolvedTrace };
  }

  return { data: response.body as T, meta: {}, traceId: resolvedTrace };
}
