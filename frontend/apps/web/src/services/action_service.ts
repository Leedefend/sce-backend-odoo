import type { NavMeta } from '@sc/schema';
import type { Router } from 'vue-router';
import { useSessionStore } from '../stores/session';
import { recordTrace, digestParams, createTraceId } from './trace';

function normalizeDomain(domain: unknown) {
  return Array.isArray(domain) ? domain : [];
}

function normalizeContext(context: unknown) {
  if (context && typeof context === 'object' && !Array.isArray(context)) {
    return context as Record<string, unknown>;
  }
  return {} as Record<string, unknown>;
}

export function openAction(router: Router, action: NavMeta, menuId?: number) {
  const model = action.model ?? '';
  const viewMode = (action.view_modes?.[0] ?? 'tree').toString();
  const query = {
    menu_id: menuId?.toString(),
    action_id: action.action_id?.toString(),
    view_mode: viewMode,
  } as Record<string, string>;

  const session = useSessionStore();
  session.setActionMeta(action);

  recordTrace({
    ts: Date.now(),
    trace_id: createTraceId(),
    intent: 'action.open',
    status: 'ok',
    menu_id: menuId,
    action_id: action.action_id,
    model,
    view_mode: viewMode,
    params_digest: digestParams({ domain: normalizeDomain(action.domain), context: normalizeContext(action.context) }),
  });

  router.push({ path: `/m/${model}`, query });
}

export function openForm(router: Router, model: string, id: number, action?: NavMeta, menuId?: number) {
  const viewMode = 'form';
  const query = {
    menu_id: menuId?.toString(),
    action_id: action?.action_id?.toString(),
    view_mode: viewMode,
  } as Record<string, string>;

  recordTrace({
    ts: Date.now(),
    trace_id: createTraceId(),
    intent: 'action.open_form',
    status: 'ok',
    menu_id: menuId,
    action_id: action?.action_id,
    model,
    view_mode: viewMode,
    params_digest: digestParams({ id }),
  });

  router.push({ path: `/m/${model}/${id}`, query });
}
