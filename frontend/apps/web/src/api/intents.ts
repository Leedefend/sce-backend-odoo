import { apiRequestRaw, ApiError } from './client';
import type { IntentEnvelope } from '@sc/schema';
import { useSessionStore } from '../stores/session';
import { parseIntentEnvelope, type IntentEnvelopeError } from './envelope';

export interface IntentPayload {
  intent: string;
  params?: unknown;
  context?: Record<string, unknown>;
  meta?: Record<string, unknown>;
  silentErrors?: boolean;
}

export interface IntentRawResult<T> {
  data: T;
  meta: Record<string, unknown>;
  traceId: string;
  ok: boolean;
  error?: IntentEnvelopeError;
  hasEnvelope: boolean;
}

const STARTUP_CHAIN_ALLOWED_INTENTS = new Set([
  'login',
  'auth.login',
  'auth.logout',
  'system.init',
  'app.init',
  'session.bootstrap',
  'sys.intents',
  'scene.health',
]);

function canBypassStartupChain(payload: IntentPayload): boolean {
  const meta = payload.meta;
  if (!meta || typeof meta !== 'object') return false;
  return Boolean((meta as Record<string, unknown>).startup_chain_bypass === true);
}

function enforceStartupChainOrThrow(session: ReturnType<typeof useSessionStore>, payload: IntentPayload): void {
  const intent = String(payload.intent || '').trim();
  if (!intent) return;
  if (!session.token) return;
  if (session.initStatus === 'ready') return;
  if (STARTUP_CHAIN_ALLOWED_INTENTS.has(intent)) return;
  if (canBypassStartupChain(payload)) return;
  throw new ApiError('startup chain required: run system.init before other intents', 409, undefined, {
    reasonCode: 'STARTUP_CHAIN_REQUIRED',
    hint: 'Allowed before init: login/auth.login/auth.logout/session.bootstrap/system.init/scene.health',
    kind: 'contract',
  });
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

function cloneRecord(input: unknown): Record<string, unknown> {
  return input && typeof input === 'object' && !Array.isArray(input)
    ? { ...(input as Record<string, unknown>) }
    : {};
}

function applyEditionRuntimeContext(
  session: ReturnType<typeof useSessionStore>,
  payload: IntentPayload,
): IntentPayload {
  const intent = String(payload.intent || '').trim();
  if (!intent || intent === 'login' || intent === 'auth.login') {
    return payload;
  }
  const requestedEditionKey = String(session.requestedEditionKey || 'standard').trim() || 'standard';
  const effectiveEditionKey = String(session.effectiveEditionKey || requestedEditionKey || 'standard').trim() || 'standard';
  const params = cloneRecord(payload.params);
  const context = cloneRecord(payload.context);
  const meta = cloneRecord(payload.meta);
  const routedEditionKey = intent === 'system.init' ? requestedEditionKey : effectiveEditionKey;
  if (!String(params.edition_key || '').trim()) {
    params.edition_key = routedEditionKey;
  }
  context.edition_runtime_v1 = {
    requested_edition_key: requestedEditionKey,
    effective_edition_key: effectiveEditionKey,
    routed_edition_key: String(params.edition_key || routedEditionKey).trim() || routedEditionKey,
  };
  meta.edition_runtime_v1 = {
    requested_edition_key: requestedEditionKey,
    effective_edition_key: effectiveEditionKey,
  };
  return {
    ...payload,
    params,
    context,
    meta,
  };
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

function shouldRetryIntentRequest(payload: IntentPayload, error: unknown, attempt: number): boolean {
  if (!(error instanceof ApiError)) return false;
  if (attempt >= 2) return false;
  const intent = String(payload.intent || '').trim();
  if (!['system.init', 'app.init', 'release.operator.surface'].includes(intent)) return false;
  return [0, 502, 503, 504].includes(Number(error.status || 0));
}

async function requestIntentEnvelope<T>(
  runtimePayload: IntentPayload,
  traceId: string,
): Promise<{ response: Awaited<ReturnType<typeof apiRequestRaw<IntentEnvelope<T>>>>; resolvedTrace: string }> {
  let lastError: unknown;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await apiRequestRaw<IntentEnvelope<T>>('/api/v1/intent', {
        method: 'POST',
        headers: buildHeaders(runtimePayload.intent, traceId),
        body: JSON.stringify(runtimePayload),
      });
      return {
        response,
        resolvedTrace: response.traceId || traceId,
      };
    } catch (error) {
      lastError = error;
      if (!shouldRetryIntentRequest(runtimePayload, error, attempt)) {
        throw error;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 1200 * (attempt + 1)));
    }
  }
  throw lastError;
}

export async function intentRequest<T>(payload: IntentPayload) {
  const traceId = generateTraceId();
  const session = useSessionStore();
  const startedAt = Date.now();
  const runtimePayload = applyEditionRuntimeContext(session, payload);
  enforceStartupChainOrThrow(session, runtimePayload);
  try {
    const { response, resolvedTrace } = await requestIntentEnvelope<T>(runtimePayload, traceId);
    session.recordIntentTrace({
      traceId: resolvedTrace,
      intent: runtimePayload.intent,
      latencyMs: Date.now() - startedAt,
      writeMode: runtimePayload.intent.includes('write') || runtimePayload.intent.includes('create') ? 'write' : 'read',
    });

    const parsed = parseIntentEnvelope<T>(response.body);
    const envelopeTrace = resolveEnvelopeTraceId(parsed.meta, resolvedTrace);
    if (!parsed.ok) {
      throwEnvelopeError(runtimePayload, envelopeTrace, parsed.error);
    }
    // eslint-disable-next-line no-console
    console.info(`[trace] intent=${runtimePayload.intent} status=ok trace=${envelopeTrace}`);
    return parsed.data;
  } catch (err) {
    const errorTrace = err instanceof ApiError ? err.traceId || traceId : traceId;
    session.recordIntentTrace({
      traceId: errorTrace,
      intent: runtimePayload.intent,
      latencyMs: Date.now() - startedAt,
      writeMode: runtimePayload.intent.includes('write') || runtimePayload.intent.includes('create') ? 'write' : 'read',
    });
    // eslint-disable-next-line no-console
    if (!runtimePayload.silentErrors) {
      // eslint-disable-next-line no-console
      console.warn(`[trace] intent=${runtimePayload.intent} status=error trace=${errorTrace}`);
    }
    throw err;
  }
}

export async function intentRequestRaw<T>(payload: IntentPayload) {
  const traceId = generateTraceId();
  const session = useSessionStore();
  const startedAt = Date.now();
  const runtimePayload = applyEditionRuntimeContext(session, payload);
  enforceStartupChainOrThrow(session, runtimePayload);
  const { response, resolvedTrace } = await requestIntentEnvelope<T>(runtimePayload, traceId);
  session.recordIntentTrace({
    traceId: resolvedTrace,
    intent: runtimePayload.intent,
    latencyMs: Date.now() - startedAt,
    writeMode: runtimePayload.intent.includes('write') || runtimePayload.intent.includes('create') ? 'write' : 'read',
  });

  const parsed = parseIntentEnvelope<T>(response.body);
  const envelopeTrace = resolveEnvelopeTraceId(parsed.meta, resolvedTrace);
  if (!parsed.ok) {
    throwEnvelopeError(runtimePayload, envelopeTrace, parsed.error);
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
