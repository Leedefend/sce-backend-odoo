import { config } from '../config';
import { useSessionStore } from '../stores/session';

export class ApiError extends Error {
  status: number;
  traceId?: string;

  constructor(message: string, status: number, traceId?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.traceId = traceId;
  }
}

function generateTraceId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `trace_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}) {
  const session = useSessionStore();
  const headers = new Headers(options.headers ?? {});
  const existingTrace = headers.get('x-trace-id');
  const traceId = existingTrace || generateTraceId();

  headers.set('Content-Type', 'application/json');
  headers.set('x-trace-id', traceId);
  headers.set('x-tenant', config.tenant);

  // 总是设置X-Odoo-DB头，即使config.odooDb为空也使用默认值
  const dbHeader = config.odooDb || 'sc_demo';
  headers.set('X-Odoo-DB', dbHeader);

  if (session.token) {
    headers.set('Authorization', `Bearer ${session.token}`);
  }

  const debugIntent =
    import.meta.env.DEV ||
    localStorage.getItem('DEBUG_INTENT') === '1' ||
    new URLSearchParams(window.location.search).get('debug') === '1';

  // A2: 网络级别校验 - 针对 app.init 请求
  let appInitPayload: any | null = null;
  let isAppInitRequest = false;
  if (path === '/api/intent' && options.body && typeof options.body === 'string') {
    try {
      appInitPayload = JSON.parse(options.body);
      isAppInitRequest = appInitPayload?.intent === 'app.init';
    } catch {
      isAppInitRequest = false;
    }
  }

  if (isAppInitRequest && debugIntent && appInitPayload) {
    console.group('[A2] app.init 网络诊断快照');
    console.log('Request URL:', `${config.apiBaseUrl}${path}`);
    console.log('Request Headers:');
    console.log('  Authorization:', headers.has('Authorization') ? '存在' : '不存在');
    console.log('  X-Odoo-DB:', headers.get('X-Odoo-DB'));
    console.log('Request Payload:');
    console.log('  intent:', appInitPayload.intent);
    console.log('  params.root_xmlid:', appInitPayload.params?.root_xmlid);
    console.groupEnd();
  }

  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  // A2: 响应诊断 - 针对 app.init 请求
  if (isAppInitRequest && debugIntent) {
    const responseClone = response.clone();
    try {
      const responseBody = await responseClone.json();
      console.group('[A2] app.init 响应诊断快照');
      console.log('Response Status:', response.status);
      console.log('Response Headers:');
      console.log('  Content-Type:', response.headers.get('Content-Type'));
      console.log('Response Body (精简):');
      
      // 提取关键信息
      const diagnosticSnapshot = {
        nav: {
          root_xmlid: responseBody.nav?.root_xmlid || 'N/A',
          items_count: Array.isArray(responseBody.nav) ? responseBody.nav.length : 'N/A',
          first_8_items: Array.isArray(responseBody.nav) ? 
            responseBody.nav.slice(0, 8).map((item: any, index: number) => ({
              index,
              name: item.name,
              xmlid: item.xmlid || 'N/A',
              id: item.id || 'N/A'
            })) : 'N/A'
        },
        meta: responseBody.meta || 'N/A',
        user: responseBody.user ? { id: responseBody.user.id, name: responseBody.user.name } : 'N/A'
      };
      console.log(JSON.stringify(diagnosticSnapshot, null, 2));
      console.groupEnd();
    } catch (error) {
      console.warn('[A2] 无法解析响应:', error);
    }
  }

  if (response.status === 401) {
    session.clearSession();
    const redirect = encodeURIComponent(`${window.location.pathname}${window.location.search}`);
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = `/login?redirect=${redirect}`;
    }
    throw new ApiError('unauthorized', 401);
  }

  if (!response.ok) {
    let message = `request failed: ${response.status}`;
    let traceId: string | undefined;
    try {
      const body = await response.json();
      message = body?.error?.message || body?.message || message;
      traceId = body?.meta?.trace_id || body?.meta?.traceId || body?.trace_id;
    } catch {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }
    throw new ApiError(message, response.status, traceId);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
