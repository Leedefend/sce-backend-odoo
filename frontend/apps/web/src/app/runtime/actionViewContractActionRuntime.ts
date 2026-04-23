export type ContractActionSelection = 'none' | 'single' | 'multi';

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
  return text('batch_msg_contract_action_missing_action_id', '契约动作缺少 action_id，无法打开目标页面');
}

export function resolveContractActionRequiresRecordContextMessage(text: (key: string, fallback: string) => string): string {
  return text('batch_msg_action_requires_record_context', '当前动作需要记录上下文，暂不支持无记录执行');
}

export function resolveContractActionMissingModelMessage(text: (key: string, fallback: string) => string): string {
  return text('batch_msg_contract_action_missing_model', '契约动作缺少 model，无法执行');
}

export function resolveContractActionDoneMessage(options: {
  successCount: number;
  failureCount: number;
  text: (key: string, fallback: string) => string;
}): string {
  return `${options.text('batch_msg_contract_action_done_prefix', '契约动作执行完成：成功 ')}${options.successCount}${options.text('batch_msg_contract_action_done_middle', '，失败 ')}${options.failureCount}`;
}

export function buildContractActionRouteTarget(options: {
  nextActionId: number;
  carryQuery: Record<string, unknown>;
  menuId: number;
  keepSceneRoute: boolean;
  routePath: string;
}): {
  path?: string;
  name?: string;
  params?: { actionId: number };
  query: Record<string, unknown>;
} {
  const query = {
    ...options.carryQuery,
    menu_id: options.menuId || undefined,
    action_id: options.nextActionId,
  };
  if (options.keepSceneRoute) {
    return { path: options.routePath, query };
  }
  return {
    name: 'action',
    params: { actionId: options.nextActionId },
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

export function resolveContractActionResponseActionId(responseRaw: unknown): number | null {
  const response = responseRaw && typeof responseRaw === 'object'
    ? (responseRaw as Record<string, unknown>)
    : {};
  const result = response.result && typeof response.result === 'object'
    ? (response.result as Record<string, unknown>)
    : {};
  const actionId = Number(result.action_id || 0);
  return actionId > 0 ? actionId : null;
}

export function shouldNavigateContractAction(options: {
  nextActionId: number | null;
}): boolean {
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
