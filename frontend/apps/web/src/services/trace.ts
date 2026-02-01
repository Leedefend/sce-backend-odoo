export interface TraceEvent {
  ts: number;
  trace_id: string;
  intent: string;
  status: 'ok' | 'error';
  menu_id?: number;
  action_id?: number;
  model?: string;
  view_mode?: string;
  params_digest?: string;
}

const STORAGE_KEY = 'sc_frontend_traces_v0_3';
const MAX_ENTRIES = 200;

export function recordTrace(event: TraceEvent) {
  const list = getTraceLog();
  list.unshift(event);
  const sliced = list.slice(0, MAX_ENTRIES);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sliced));
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
