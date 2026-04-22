import type { NavMeta } from '@sc/schema';
import type { Router } from 'vue-router';
import { ErrorCodes } from '../app/error_codes';
import { resolveSceneFirstActionLocation, resolveSceneFirstFormOrRecordLocation } from '../app/sceneNavigation';
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
  const viewMode = Array.isArray(action.view_modes) && action.view_modes.length
    ? String(action.view_modes[0] || '')
    : '';
  const query = {
    menu_id: menuId?.toString(),
    action_id: action.action_id?.toString(),
  } as Record<string, string>;
  if (viewMode.trim()) {
    query.view_mode = viewMode;
  }

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

  const sceneLocation = resolveSceneFirstActionLocation({
    sourceQuery: query,
    actionId: action.action_id,
    menuId,
    model: model || undefined,
    viewMode: viewMode || undefined,
    extraQuery: query,
  });
  router.push(sceneLocation || {
    name: 'workbench',
    query: {
      reason: ErrorCodes.CONTRACT_CONTEXT_MISSING,
      diag: 'action_service_missing_scene_identity',
      action_id: action.action_id?.toString(),
      menu_id: menuId?.toString(),
      model: model || undefined,
      view_mode: viewMode || undefined,
    },
  });
}

export function openForm(router: Router, model: string, id: number, action?: NavMeta, menuId?: number) {
  const query = {
    menu_id: menuId?.toString(),
    action_id: action?.action_id?.toString(),
  } as Record<string, string>;
  query.view_mode = 'form';

  recordTrace({
    ts: Date.now(),
    trace_id: createTraceId(),
    intent: 'action.open_form',
    status: 'ok',
    menu_id: menuId,
    action_id: action?.action_id,
    model,
    view_mode: 'form',
    params_digest: digestParams({ id }),
  });

  const sceneLocation = resolveSceneFirstFormOrRecordLocation({
    sourceQuery: query,
    actionId: action?.action_id,
    menuId,
    model,
    recordId: id,
    viewMode: 'form',
    extraQuery: query,
  });
  router.push(sceneLocation || {
    name: 'workbench',
    query: {
      reason: ErrorCodes.CONTRACT_CONTEXT_MISSING,
      diag: 'action_service_form_missing_scene_identity',
      action_id: action?.action_id?.toString(),
      menu_id: menuId?.toString(),
      model,
      record_id: String(id),
      view_mode: 'form',
    },
  });
}
