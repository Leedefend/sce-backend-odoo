export interface TraceEvent {
  ts: number;
  trace_id: string;
  intent: string;
  status: 'ok' | 'error';
  event_type?: 'intent' | 'suggested_action';
  menu_id?: number;
  action_id?: number;
  model?: string;
  view_mode?: string;
  params_digest?: string;
  suggested_action_kind?: string;
  suggested_action_raw?: string;
  suggested_action_success?: boolean;
}

const STORAGE_KEY = 'sc_frontend_traces_v0_3';
const MAX_ENTRIES = 200;
const TRACE_UPDATE_EVENT = 'sc:trace-updated';

export function recordTrace(event: TraceEvent) {
  const list = getTraceLog();
  list.unshift({ ...event, event_type: event.event_type || 'intent' });
  const sliced = list.slice(0, MAX_ENTRIES);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sliced));
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(TRACE_UPDATE_EVENT));
  }
}

export function getTraceUpdateEventName() {
  return TRACE_UPDATE_EVENT;
}

export function recordSuggestedActionTrace(event: {
  trace_id?: string;
  kind: string;
  raw: string;
  success: boolean;
}) {
  recordTrace({
    ts: Date.now(),
    trace_id: event.trace_id || createTraceId(),
    intent: 'suggested_action.run',
    status: event.success ? 'ok' : 'error',
    event_type: 'suggested_action',
    suggested_action_kind: event.kind,
    suggested_action_raw: event.raw,
    suggested_action_success: event.success,
  });
}

export function getLatestSuggestedActionTrace(): TraceEvent | null {
  const list = getTraceLog();
  for (const item of list) {
    if (item.event_type === 'suggested_action') {
      return item;
    }
  }
  return null;
}

export function createTraceId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID();
  }
  return `trace_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

export function getTraceLog(): TraceEvent[] {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return [];
  }
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function digestParams(params: Record<string, unknown>) {
  try {
    return JSON.stringify(params);
  } catch {
    return '';
  }
}
