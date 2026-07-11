import { buildEntryTargetRouteTarget } from '../routeQuery';

export type ContractActionSelection = 'none' | 'single' | 'multi';

export type ContractActionResponseNavigation = {
  nextActionId: number | null;
  entryTarget: Record<string, unknown> | null;
  query?: Record<string, unknown>;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function toPositiveInt(value: unknown): number {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

function resolveEntryTargetActionId(entryTarget: Record<string, unknown> | null): number {
  if (!entryTarget) return 0;
  const refs = asRecord(entryTarget.compatibility_refs);
  const recordEntry = asRecord(entryTarget.record_entry);
  return toPositiveInt(refs.action_id || recordEntry.action_id);
}

export function resolveContractActionOpenNavigation(options: {
  actionId?: number | null;
  url?: string | null;
}): {
  kind: 'action' | 'url' | 'none';
  actionId: number | null;
  url: string;
} {
  const actionId = Number(options.actionId || 0);
  if (actionId > 0) {
    return { kind: 'action', actionId, url: '' };
  }
  const url = String(options.url || '').trim();
  if (url) {
    return { kind: 'url', actionId: null, url };
  }
  return { kind: 'none', actionId: null, url: '' };
}

export function resolveContractActionExecIds(options: {
  selectedIds: number[];
  contextRecordId: number | null;
}): number[] {
  if (options.selectedIds.length) return options.selectedIds;
  if (options.contextRecordId && options.contextRecordId > 0) return [options.contextRecordId];
  return [];
}

export function resolveContractActionSelectionMessage(options: {
  selection: ContractActionSelection;
  selectedCount: number;
}): 'select_single' | 'select_multi' | null {
  if (options.selection === 'none') return null;
  if (options.selectedCount > 0) return null;
  return options.selection === 'single' ? 'select_single' : 'select_multi';
}

export function buildContractActionButtonRequest(options: {
  model: string;
  recordId: number;
  methodName?: string | null;
  actionKey: string;
  kind?: string | null;
  context?: Record<string, unknown>;
}): {
  model: string;
  res_id: number;
  button: { name: string; type: string };
  context?: Record<string, unknown>;
} {
  return {
    model: options.model,
    res_id: options.recordId,
    button: {
      name: String(options.methodName || options.actionKey || '').trim(),
      type: String(options.kind || 'object').trim() || 'object',
    },
    context: options.context,
  };
}

export function resolveContractActionRunIds(execIds: number[]): number[] {
  return execIds.length ? execIds : [0];
}

export function resolveContractActionMissingOpenTargetMessage(text: (key: string, fallback: string) => string): string {
  return text('batch_msg_contract_action_missing_action_id', '页面操作缺少目标页面，无法打开');
}

export function resolveContractActionRequiresRecordContextMessage(text: (key: string, fallback: string) => string): string {
  return text('batch_msg_action_requires_record_context', '当前操作需要先选择记录，无法直接执行');
}

export function resolveContractActionMissingModelMessage(text: (key: string, fallback: string) => string): string {
  return text('batch_msg_contract_action_missing_model', '页面操作缺少业务对象，无法执行');
}

export function resolveContractActionDoneMessage(options: {
  successCount: number;
  failureCount: number;
  text: (key: string, fallback: string) => string;
}): string {
  return `${options.text('batch_msg_contract_action_done_prefix', '页面操作执行完成：成功 ')}${options.successCount}${options.text('batch_msg_contract_action_done_middle', '，失败 ')}${options.failureCount}`;
}

export function buildContractActionRouteTarget(options: {
  nextActionId?: number | null;
  entryTarget?: Record<string, unknown> | null;
  carryQuery: Record<string, unknown>;
  responseQuery?: Record<string, unknown> | null;
  menuId: number;
  keepSceneRoute: boolean;
  routePath: string;
}): {
  path?: string;
  name?: string;
  params?: { actionId: number };
  query: Record<string, unknown>;
} {
  const entryTarget = options.entryTarget && typeof options.entryTarget === 'object'
    ? options.entryTarget
    : null;
  const entryTargetType = String(entryTarget?.type || '').trim();
  const sceneKey = String(entryTarget?.scene_key || '').trim();
  const entryTargetActionId = resolveEntryTargetActionId(entryTarget);
  const nextActionId = toPositiveInt(options.nextActionId) || entryTargetActionId;
  const query = {
    ...options.carryQuery,
    ...(options.responseQuery || {}),
    menu_id: options.menuId || undefined,
    action_id: nextActionId || undefined,
  };
  if (entryTargetType && (sceneKey || entryTargetType === 'compatibility')) {
    return buildEntryTargetRouteTarget(entryTarget, {
      query,
      menuId: options.menuId,
      actionId: nextActionId,
      keepSceneRoute: options.keepSceneRoute,
      routePath: options.routePath,
    });
  }
  if (options.keepSceneRoute) {
    return { path: options.routePath, query };
  }
  return {
    name: 'action',
    params: { actionId: nextActionId },
    query,
  };
}

export function resolveContractActionSelectionBlockMessage(options: {
  selection: ContractActionSelection;
  selectedCount: number;
  text: (key: string, fallback: string) => string;
}): string {
  const selectionMessage = resolveContractActionSelectionMessage({
    selection: options.selection,
    selectedCount: options.selectedCount,
  });
  if (!selectionMessage) return '';
  return selectionMessage === 'select_single'
    ? options.text('batch_msg_select_single_before_run', '请选择 1 条记录后再执行')
    : options.text('batch_msg_select_records_before_run', '请先选择记录后再执行');
}

export function resolveContractActionResponseNavigation(responseRaw: unknown): ContractActionResponseNavigation {
  const response = asRecord(responseRaw);
  const result = asRecord(response.result);
  const effect = asRecord(response.effect);
  const effectTarget = asRecord(effect.target);
  const rawAction = asRecord(result.raw_action);
  const entryTarget = asRecord(
    result.entry_target
      || rawAction.entry_target
      || effectTarget.entry_target,
  );
  const normalizedEntryTarget = String(entryTarget.type || '').trim() ? entryTarget : null;
  const actionId = toPositiveInt(
    result.action_id
      || rawAction.action_id
      || rawAction.id
      || effectTarget.action_id
      || resolveEntryTargetActionId(normalizedEntryTarget),
  );
  const domainRaw = String(result.domain_raw || rawAction.domain_raw || effectTarget.domain_raw || '').trim();
  const contextRaw = String(result.context_raw || rawAction.context_raw || effectTarget.context_raw || '').trim();
  return {
    nextActionId: actionId || null,
    entryTarget: normalizedEntryTarget,
    query: {
      domain_raw: domainRaw || undefined,
      context_raw: contextRaw || undefined,
    },
  };
}

export function resolveContractActionResponseActionId(responseRaw: unknown): number | null {
  return resolveContractActionResponseNavigation(responseRaw).nextActionId;
}

export function shouldNavigateContractAction(options: {
  nextActionId?: number | null;
  entryTarget?: Record<string, unknown> | null;
}): boolean {
  if (options.entryTarget && String(options.entryTarget.type || '').trim()) return true;
  return typeof options.nextActionId === 'number' && options.nextActionId > 0;
}

export function resolveContractActionCounters(options: {
  successCount: number;
  failureCount: number;
  ok: boolean;
}): {
  successCount: number;
  failureCount: number;
} {
  if (options.ok) {
    return {
      successCount: options.successCount + 1,
      failureCount: options.failureCount,
    };
  }
  return {
    successCount: options.successCount,
    failureCount: options.failureCount + 1,
  };
}
