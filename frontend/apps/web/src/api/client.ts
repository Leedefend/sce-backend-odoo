import { config } from '../config';
import { useSessionStore } from '../stores/session';
import { resolveConfiguredDb, resolveLoginRoutingDb } from '../services/dbContext';
import { currentContextEpoch, currentContextSignal } from '../app/contextEpoch';

type UnknownObject = Record<string, unknown>;

interface AppInitIntentPayload {
  intent?: string;
  params?: {
    root_xmlid?: string;
  };
}

interface AppInitDiagnosticResponse {
  nav?: unknown;
  meta?: unknown;
  user?: unknown;
}

export class ApiError extends Error {
  status: number;
  traceId?: string;
  reasonCode?: string;
  hint?: string;
  kind?: string;
  errorCategory?: string;
  retryable?: boolean;
  suggestedAction?: string;
  details?: Record<string, unknown>;

  constructor(
    message: string,
    status: number,
    traceId?: string,
    options?: {
      reasonCode?: string;
      hint?: string;
      kind?: string;
      errorCategory?: string;
      retryable?: boolean;
      suggestedAction?: string;
      details?: Record<string, unknown>;
    },
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.traceId = traceId;
    this.reasonCode = options?.reasonCode;
    this.hint = options?.hint;
    this.kind = options?.kind;
    this.errorCategory = options?.errorCategory;
    this.retryable = options?.retryable;
    this.suggestedAction = options?.suggestedAction;
    this.details = options?.details;
  }
}

function generateTraceId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `trace_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function extractTraceIdFromBody(body: unknown) {
  if (!body || typeof body !== 'object') {
    return undefined;
  }
  const raw = body as {
    meta?: { trace_id?: string; traceId?: string };
    trace_id?: string;
    traceId?: string;
  };
  return raw.meta?.trace_id || raw.meta?.traceId || raw.trace_id || raw.traceId;
}

function resolveTraceId(response: Response, body: unknown, fallback: string) {
  const headerTrace =
    response.headers.get('x-trace-id') ||
    response.headers.get('x-request-id') ||
    response.headers.get('x-odoo-trace-id');
  return headerTrace || extractTraceIdFromBody(body) || fallback;
}

function asObject(value: unknown): UnknownObject | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  return value as UnknownObject;
}

function resolveApiPath(path: string, dbHeader: string) {
  const raw = String(path || '').trim() || '/';
  // Force db query on intent endpoint to avoid multi-db ambiguity.
  if (!raw.startsWith('/api/v1/intent')) return raw;
  if (!dbHeader) return raw;
  const hasDb = /(?:\?|&)db=/.test(raw);
  if (hasDb) return raw;
  return `${raw}${raw.includes('?') ? '&' : '?'}db=${encodeURIComponent(dbHeader)}`;
}

async function apiRequestRawUncoalesced<T>(path: string, options: RequestInit = {}) {
  const session = useSessionStore();
  const headers = new Headers(options.headers ?? {});
  const existingTrace = headers.get('x-trace-id');
  const traceId = existingTrace || generateTraceId();

  headers.set('Content-Type', 'application/json');
  headers.set('x-trace-id', traceId);
  headers.set('x-tenant', config.tenant);

  const isIntentEndpoint = String(path || '').trim().startsWith('/api/v1/intent');
  let intentName = '';
  if (isIntentEndpoint && options.body && typeof options.body === 'string') {
    try {
      const parsed = JSON.parse(options.body) as { intent?: string };
      intentName = String(parsed?.intent || '').trim();
    } catch {
      intentName = '';
    }
  }
  const isAnonymousIntent = intentName === 'login' || intentName === 'auth.login' || intentName === 'session.bootstrap' || intentName === 'sys.intents';
  const loginRoutingDb = intentName === 'login' || intentName === 'auth.login' ? resolveLoginRoutingDb() : '';
  const sessionDb = String(session.sessionDb || '').trim();
  const dbHeader = loginRoutingDb || (session.token && sessionDb ? sessionDb : resolveConfiguredDb(String(config.odooDb || '').trim()));
  if (dbHeader) {
    headers.set('X-Odoo-DB', dbHeader);
  }
  if (isAnonymousIntent) {
    headers.set('X-Anonymous-Intent', '1');
  }
  if (session.token && !isAnonymousIntent) {
    headers.set('Authorization', `Bearer ${session.token}`);
  }

  const debugIntent =
    localStorage.getItem('DEBUG_INTENT') === '1' ||
    new URLSearchParams(window.location.search).get('debug') === '1';

  // A2: 网络级别校验 - 针对 system.init 请求
  const resolvedPath = resolveApiPath(path, dbHeader);

  let appInitPayload: AppInitIntentPayload | null = null;
  let isAppInitRequest = false;
  if (resolvedPath.startsWith('/api/v1/intent') && options.body && typeof options.body === 'string') {
    try {
      appInitPayload = JSON.parse(options.body) as AppInitIntentPayload;
      const initIntent = String(appInitPayload?.intent || '').trim();
      isAppInitRequest = initIntent === 'system.init' || initIntent === 'app.init';
    } catch {
      isAppInitRequest = false;
    }
  }

  if (isAppInitRequest && debugIntent && appInitPayload) {
    console.group('[A2] system.init 网络诊断快照');
    console.log('Request URL:', `${config.apiBaseUrl}${resolvedPath}`);
    console.log('Request Headers:');
    console.log('  Authorization:', headers.has('Authorization') ? '存在' : '不存在');
    console.log('  X-Odoo-DB:', headers.get('X-Odoo-DB'));
    console.log('Request Payload:');
    console.log('  intent:', appInitPayload.intent);
    console.log('  params.root_xmlid:', appInitPayload.params?.root_xmlid);
    console.groupEnd();
  }

  const requestedCreds = options.credentials;
  if (requestedCreds && requestedCreds !== 'omit' && import.meta.env.DEV) {
    console.warn(`[SPA API] Forcing credentials=omit (requested: ${requestedCreds})`);
  }

  let response: Response;
  try {
    response = await fetch(`${config.apiBaseUrl}${resolvedPath}`, {
      ...options,
      headers,
      signal: options.signal || currentContextSignal(),
      // Portal shell authentication is token-based; do not send Odoo session cookies
      // to avoid cross-origin session/auth side effects.
      credentials: 'omit',
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Network request failed';
    throw new ApiError(message, 0, traceId, {
      reasonCode: 'NETWORK_ERROR',
      hint: 'Check network connectivity and API service status.',
      kind: 'network',
    });
  }

  // A2: 响应诊断 - 针对 system.init 请求
  if (isAppInitRequest && debugIntent) {
    const responseClone = response.clone();
    try {
      const responseBody = (await responseClone.json()) as AppInitDiagnosticResponse;
      console.group('[A2] system.init 响应诊断快照');
      console.log('Response Status:', response.status);
      console.log('Response Headers:');
      console.log('  Content-Type:', response.headers.get('Content-Type'));
      console.log('Response Body (精简):');

      // 提取关键信息
      const navList = Array.isArray(responseBody.nav) ? responseBody.nav : null;
      const diagnosticSnapshot = {
        nav: {
          root_xmlid: asObject(responseBody.nav)?.root_xmlid || 'N/A',
          items_count: navList ? navList.length : 'N/A',
          first_8_items: navList
            ? navList.slice(0, 8).map((item, index: number) => {
                const node = asObject(item);
                return {
                  index,
                  name: node?.name ?? 'N/A',
                  xmlid: node?.xmlid ?? 'N/A',
                  id: node?.id ?? 'N/A',
                };
              })
            : 'N/A',
        },
        meta: responseBody.meta || 'N/A',
        user: (() => {
          const user = asObject(responseBody.user);
          return user ? { id: user.id, name: user.name } : 'N/A';
        })(),
      };
      console.log(JSON.stringify(diagnosticSnapshot, null, 2));
      console.groupEnd();
    } catch (error) {
      console.warn('[A2] 无法解析响应:', error);
    }
  }

  if (response.status === 401) {
    session.clearSession();
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login?reason=session_expired';
    }
    throw new ApiError('unauthorized', 401, traceId, {
      reasonCode: 'AUTH_401',
      hint: 'Login session expired. Please sign in again.',
      kind: 'auth',
    });
  }

  if (!response.ok) {
    let message = `request failed: ${response.status}`;
    let traceIdFromBody: string | undefined;
    let body: unknown;
    let reasonCode: string | undefined;
    let hint: string | undefined;
    let kind: string | undefined;
    let errorCategory: string | undefined;
    let retryable: boolean | undefined;
    let suggestedAction: string | undefined;
    let details: Record<string, unknown> | undefined;
    try {
      const jsonProbe = response.clone();
      body = await jsonProbe.json();
      const payload = body as {
        error?: {
          message?: string;
          code?: string;
          reason_code?: string;
          hint?: string;
          kind?: string;
          error_category?: string;
          retryable?: boolean;
          suggested_action?: string;
          details?: Record<string, unknown>;
        };
        message?: string;
        code?: string;
        reason_code?: string;
        hint?: string;
        kind?: string;
        error_category?: string;
        retryable?: boolean;
        suggested_action?: string;
        details?: Record<string, unknown>;
      };
      message = payload?.error?.message || payload?.message || message;
      reasonCode = payload?.error?.reason_code || payload?.reason_code || payload?.error?.code || payload?.code;
      hint = payload?.error?.hint || payload?.hint;
      kind = payload?.error?.kind || payload?.kind;
      errorCategory = payload?.error?.error_category || payload?.error_category;
      retryable =
        typeof payload?.error?.retryable === 'boolean'
          ? payload.error.retryable
          : typeof payload?.retryable === 'boolean'
          ? payload.retryable
          : undefined;
      suggestedAction = payload?.error?.suggested_action || payload?.suggested_action;
      details = payload?.error?.details || payload?.details;
      traceIdFromBody = extractTraceIdFromBody(body);
    } catch {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }
    const resolvedTrace = resolveTraceId(response, body, traceId);
    throw new ApiError(message, response.status, traceIdFromBody || resolvedTrace, {
      reasonCode,
      hint,
      kind: kind || 'http',
      errorCategory,
      retryable,
      suggestedAction,
      details,
    });
  }

  if (response.status === 204) {
    return { body: undefined as T, traceId };
  }

  const body = (await response.json()) as T;
  const resolvedTrace = resolveTraceId(response, body, traceId);
  return { body, traceId: resolvedTrace };
}

const idempotentRequests = new Map<string, Promise<{ body: unknown; traceId?: string }>>();

function idempotentIntentKey(path: string, options: RequestInit): string {
  if (!String(path || '').startsWith('/api/v1/intent') || options.method !== 'POST' || typeof options.body !== 'string') return '';
  try {
    const payload = JSON.parse(options.body) as { intent?: string; params?: Record<string, unknown> };
    const intent = String(payload.intent || '').trim();
    const op = String(payload.params?.op || '').trim();
    const idempotent = intent === 'ui.contract.v2'
      || intent === 'chatter.timeline'
      || (intent === 'api.data' && ['read', 'list', 'search'].includes(op));
    if (!idempotent) return '';
    const session = useSessionStore();
    const params = payload.params || {};
    const context = (params.context && typeof params.context === 'object' && !Array.isArray(params.context))
      ? params.context as Record<string, unknown>
      : {};
    const semanticRequest = {
      intent,
      op,
      model: params.model,
      ids: params.ids,
      fields: params.fields,
      domain: params.domain,
      action_id: params.action_id,
      menu_id: params.menu_id,
      record_id: params.record_id,
      render_profile: params.render_profile,
      surface: params.surface,
      res_id: params.res_id,
      limit: params.limit,
      company_id: params.company_id || context.company_id,
      current_project_id: params.current_project_id || context.current_project_id,
      operation_strategy: params.operation_strategy || context.operation_strategy,
      project_scope_policy: context.project_scope_policy,
    };
    return `${session.sessionDb}|${session.token || ''}|${currentContextEpoch()}|${JSON.stringify(semanticRequest)}`;
  } catch {
    return '';
  }
}

export async function apiRequestRaw<T>(path: string, options: RequestInit = {}) {
  const key = idempotentIntentKey(path, options);
  if (!key) return apiRequestRawUncoalesced<T>(path, options);
  const existing = idempotentRequests.get(key);
  if (existing) return existing as Promise<{ body: T; traceId?: string }>;
  const request = apiRequestRawUncoalesced<T>(path, options);
  idempotentRequests.set(key, request as Promise<{ body: unknown; traceId?: string }>);
  try {
    return await request;
  } catch (error) {
    if (idempotentRequests.get(key) === request) idempotentRequests.delete(key);
    throw error;
  } finally {
    // Coalesce only truly concurrent reads. A resolved response must never act
    // as a business-data TTL cache because mutations require an immediate
    // authoritative reread of state and monetary facts.
    if (idempotentRequests.get(key) === request) idempotentRequests.delete(key);
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}) {
  const response = await apiRequestRaw<T>(path, options);
  return response.body as T;
}
