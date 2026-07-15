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
  rawBody?: unknown;
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

function withCurrentProjectContext(session: ReturnType<typeof useSessionStore>, payload: IntentPayload): IntentPayload {
  const intent = String(payload.intent || '').trim();
  const skip = new Set(['login', 'auth.login', 'auth.logout', 'session.bootstrap', 'sys.intents', 'project.context.search']);
  const params = (payload.params && typeof payload.params === 'object' && !Array.isArray(payload.params))
    ? { ...(payload.params as Record<string, unknown>) }
    : payload.params;
  const paramsContext = (params && typeof params === 'object' && !Array.isArray(params)
    && (params as Record<string, unknown>).context
    && typeof (params as Record<string, unknown>).context === 'object'
    && !Array.isArray((params as Record<string, unknown>).context))
    ? (params as Record<string, unknown>).context as Record<string, unknown>
    : {};
  const projectId = Number(session.projectContext?.selected?.id || 0);
  const companyId = Number(session.projectContext?.company_id || session.projectContext?.selected?.company_id || 0);
  const operationStrategy = String(
    session.projectContext?.operation_strategy || session.projectContext?.selected?.operation_strategy || '',
  ).trim();
  const isMenuListRequest = intent === 'api.data'
    && params
    && typeof params === 'object'
    && !Array.isArray(params)
    && ['list', 'read'].includes(String((params as Record<string, unknown>).op || '').trim())
    && Number(paramsContext.menu_id || 0) > 0;
  if ((!projectId && !companyId && !operationStrategy) || skip.has(intent)) {
    return payload;
  }
  const projectScopePolicy = String(
    paramsContext.project_scope_policy
      || paramsContext.projectScopePolicy
      || payload.context?.project_scope_policy
      || payload.context?.projectScopePolicy
      || '',
  ).trim().toLowerCase();
  const shouldUseProjectScope = projectScopePolicy !== 'global' && projectScopePolicy !== 'exempt';
  if (isMenuListRequest) {
    const context = {
      ...(payload.context || {}),
      ...(companyId ? { company_id: companyId } : {}),
      ...(operationStrategy ? { operation_strategy: operationStrategy } : {}),
      ...(projectScopePolicy ? { project_scope_policy: projectScopePolicy } : {}),
      ...(shouldUseProjectScope && projectId ? { current_project_id: projectId } : {}),
    };
    const paramsRecord = params as Record<string, unknown>;
    const requestContext = (paramsRecord.context && typeof paramsRecord.context === 'object' && !Array.isArray(paramsRecord.context))
      ? paramsRecord.context as Record<string, unknown>
      : {};
    paramsRecord.context = {
      ...requestContext,
      ...(companyId ? { company_id: companyId } : {}),
      ...(operationStrategy ? { operation_strategy: operationStrategy } : {}),
      ...(projectScopePolicy ? { project_scope_policy: projectScopePolicy } : {}),
      ...(shouldUseProjectScope && projectId ? { current_project_id: projectId } : {}),
    };
    if (companyId) paramsRecord.company_id = companyId;
    if (operationStrategy) paramsRecord.operation_strategy = operationStrategy;
    if (shouldUseProjectScope && projectId) {
      paramsRecord.current_project_id = projectId;
    } else {
      delete paramsRecord.current_project_id;
      delete (paramsRecord.context as Record<string, unknown>).current_project_id;
    }
    return {
      ...payload,
      context,
      params,
    };
  }
  const context = {
    ...(payload.context || {}),
    ...(companyId ? { company_id: companyId } : {}),
    ...(operationStrategy ? { operation_strategy: operationStrategy } : {}),
    ...(projectScopePolicy ? { project_scope_policy: projectScopePolicy } : {}),
    ...(shouldUseProjectScope && projectId ? { current_project_id: projectId } : {}),
  };
  if (!shouldUseProjectScope) delete context.current_project_id;
  if (params && typeof params === 'object' && !Array.isArray(params)) {
    const paramsRecord = params as Record<string, unknown>;
    const requestContext = (paramsRecord.context && typeof paramsRecord.context === 'object' && !Array.isArray(paramsRecord.context))
      ? paramsRecord.context as Record<string, unknown>
      : {};
    paramsRecord.context = {
      ...requestContext,
      ...(companyId ? { company_id: companyId } : {}),
      ...(operationStrategy ? { operation_strategy: operationStrategy } : {}),
      ...(projectScopePolicy ? { project_scope_policy: projectScopePolicy } : {}),
      ...(shouldUseProjectScope && projectId ? { current_project_id: projectId } : {}),
    };
    if (companyId) paramsRecord.company_id = companyId;
    if (operationStrategy) paramsRecord.operation_strategy = operationStrategy;
    if (shouldUseProjectScope && projectId) {
      paramsRecord.current_project_id = projectId;
    } else {
      delete paramsRecord.current_project_id;
      delete (paramsRecord.context as Record<string, unknown>).current_project_id;
    }
  }
  return {
    ...payload,
    context,
    params,
  };
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
  const effectivePayload = withCurrentProjectContext(session, payload);
  const startedAt = Date.now();
  enforceStartupChainOrThrow(session, effectivePayload);
  try {
    const response = await apiRequestRaw<IntentEnvelope<T>>('/api/v1/intent', {
      method: 'POST',
      headers: buildHeaders(effectivePayload.intent, traceId),
      body: JSON.stringify(effectivePayload),
    });
    const resolvedTrace = response.traceId || traceId;
    session.recordIntentTrace({
      traceId: resolvedTrace,
      intent: effectivePayload.intent,
      latencyMs: Date.now() - startedAt,
      writeMode: effectivePayload.intent.includes('write') || effectivePayload.intent.includes('create') ? 'write' : 'read',
    });

    const parsed = parseIntentEnvelope<T>(response.body);
    const envelopeTrace = resolveEnvelopeTraceId(parsed.meta, resolvedTrace);
    if (!parsed.ok) {
      throwEnvelopeError(effectivePayload, envelopeTrace, parsed.error);
    }
    // eslint-disable-next-line no-console
    console.info(`[trace] intent=${effectivePayload.intent} status=ok trace=${envelopeTrace}`);
    return parsed.data;
  } catch (err) {
    const errorTrace = err instanceof ApiError ? err.traceId || traceId : traceId;
    session.recordIntentTrace({
      traceId: errorTrace,
      intent: effectivePayload.intent,
      latencyMs: Date.now() - startedAt,
      writeMode: effectivePayload.intent.includes('write') || effectivePayload.intent.includes('create') ? 'write' : 'read',
    });
    // eslint-disable-next-line no-console
    if (!effectivePayload.silentErrors) {
      // eslint-disable-next-line no-console
      console.warn(`[trace] intent=${effectivePayload.intent} status=error trace=${errorTrace}`);
    }
    throw err;
  }
}

export async function intentRequestRaw<T>(payload: IntentPayload) {
  const traceId = generateTraceId();
  const session = useSessionStore();
  const effectivePayload = withCurrentProjectContext(session, payload);
  const startedAt = Date.now();
  enforceStartupChainOrThrow(session, effectivePayload);
  const response = await apiRequestRaw<IntentEnvelope<T>>('/api/v1/intent', {
    method: 'POST',
    headers: buildHeaders(effectivePayload.intent, traceId),
    body: JSON.stringify(effectivePayload),
  });
  const resolvedTrace = response.traceId || traceId;
  session.recordIntentTrace({
    traceId: resolvedTrace,
    intent: effectivePayload.intent,
    latencyMs: Date.now() - startedAt,
    writeMode: effectivePayload.intent.includes('write') || effectivePayload.intent.includes('create') ? 'write' : 'read',
  });

  const parsed = parseIntentEnvelope<T>(response.body);
  const envelopeTrace = resolveEnvelopeTraceId(parsed.meta, resolvedTrace);
  if (!parsed.ok) {
    throwEnvelopeError(effectivePayload, envelopeTrace, parsed.error);
  }
  const result: IntentRawResult<T> = {
    data: parsed.data,
    meta: parsed.meta,
    traceId: resolvedTrace,
    ok: true,
    error: parsed.error,
    hasEnvelope: parsed.hasEnvelope,
    rawBody: response.body,
  };
  return result;
}
