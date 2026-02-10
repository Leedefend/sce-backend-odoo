import { apiRequestRaw, ApiError } from './client';
import type { IntentEnvelope } from '@sc/schema';
import { useSessionStore } from '../stores/session';
import { parseIntentEnvelope, type IntentEnvelopeError } from './envelope';

export interface IntentPayload {
  intent: string;
  params?: unknown;
  context?: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

export interface IntentRawResult<T> {
  data: T;
  meta: Record<string, unknown>;
  traceId: string;
  ok: boolean;
  error?: IntentEnvelopeError;
  hasEnvelope: boolean;
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

function resolveEnvelopeTraceId(meta: Record<string, unknown>, fallback: string): string {
  const trace = meta.trace_id;
  if (typeof trace === 'string' && trace.trim()) return trace.trim();
  const traceAlias = meta.traceId;
  if (typeof traceAlias === 'string' && traceAlias.trim()) return traceAlias.trim();
  return fallback;
}

function throwEnvelopeError(
  payload: IntentPayload,
  traceId: string,
  parsedError?: IntentEnvelopeError,
): never {
  const message = parsedError?.message || `intent failed: ${payload.intent}`;
  const reasonCode = parsedError?.reason_code || parsedError?.code || 'INTENT_FAILED';
  const hint = parsedError?.hint;
  const kind = parsedError?.kind || parsedError?.error_category || 'contract';
  throw new ApiError(message, 400, parsedError?.trace_id || traceId, {
    reasonCode,
    hint,
    kind,
    errorCategory: parsedError?.error_category,
    retryable: parsedError?.retryable,
    suggestedAction: parsedError?.suggested_action,
  });
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

    const parsed = parseIntentEnvelope<T>(response.body);
    const envelopeTrace = resolveEnvelopeTraceId(parsed.meta, resolvedTrace);
    if (!parsed.ok) {
      throwEnvelopeError(payload, envelopeTrace, parsed.error);
    }
    return parsed.data;
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

  const parsed = parseIntentEnvelope<T>(response.body);
  const envelopeTrace = resolveEnvelopeTraceId(parsed.meta, resolvedTrace);
  if (!parsed.ok) {
    throwEnvelopeError(payload, envelopeTrace, parsed.error);
  }
  const result: IntentRawResult<T> = {
    data: parsed.data,
    meta: parsed.meta,
    traceId: resolvedTrace,
    ok: true,
    error: parsed.error,
    hasEnvelope: parsed.hasEnvelope,
  };
  return result;
}
