import type { ContractAction } from './types';

export type FormActionExecutionPlan =
  | { kind: 'disabled' }
  | { kind: 'local_mode'; mode: string; toggle: boolean }
  | { kind: 'save'; refreshPolicy?: ContractAction['refreshPolicy'] }
  | { kind: 'cancel' }
  | { kind: 'open_action'; actionId: number; target?: string; domainRaw?: string }
  | { kind: 'open_url'; url: string; target?: string }
  | { kind: 'open_missing_target' }
  | {
    kind: 'scene_mutation';
    actionKey: string;
    mutation: NonNullable<ContractAction['mutation']>;
    recordId: number | null;
    model: string;
    context?: Record<string, unknown>;
    refreshPolicy?: ContractAction['refreshPolicy'];
  }
  | {
    kind: 'record_button';
    model: string;
    recordId: number;
    methodName: string;
    buttonType: 'object' | 'server';
    context?: Record<string, unknown>;
    refreshPolicy?: ContractAction['refreshPolicy'];
  }
  | { kind: 'unsupported' };

export async function collectActionParams(
  action: ContractAction,
  onMissingReason: () => void,
): Promise<Record<string, unknown> | null> {
  const required = new Set((action.requiredParams || []).map((item) => item.toLowerCase()));
  if (!action.requiresReason && !required.has('reason')) return {};
  const reason = window.prompt(`${action.label || '操作'}原因`)?.trim() || '';
  if (reason) return { reason };
  onMissingReason();
  return null;
}

export function buildFormActionExecutionPlan(params: {
  action: ContractAction;
  modelName: string;
  recordId: number | null;
}): FormActionExecutionPlan {
  const { action } = params;
  if (!action.enabled) return { kind: 'disabled' };
  if (action.intent === 'ui.local_mode' || action.intent === 'ui.mode' || action.clientMode) {
    return { kind: 'local_mode', mode: action.clientMode, toggle: true };
  }
  const actionKey = String(action.key || '').trim().toLowerCase();
  if (actionKey === 'submit_intake' || actionKey === 'save_draft') {
    return { kind: 'save', refreshPolicy: action.refreshPolicy };
  }
  if (actionKey === 'cancel' && !action.methodName) {
    return { kind: 'cancel' };
  }
  if (action.kind === 'open') {
    if (action.actionId) {
      return {
        kind: 'open_action',
        actionId: action.actionId,
        target: action.target || undefined,
        domainRaw: action.domainRaw || undefined,
      };
    }
    if (action.url) {
      return {
        kind: 'open_url',
        url: action.url,
        target: action.target || undefined,
      };
    }
    return { kind: 'open_missing_target' };
  }
  if (action.mutation) {
    return {
      kind: 'scene_mutation',
      actionKey: action.key || '',
      mutation: action.mutation,
      recordId: params.recordId,
      model: action.targetModel || params.modelName,
      context: action.context,
      refreshPolicy: action.refreshPolicy,
    };
  }
  if ((action.kind === 'object' || action.kind === 'server') && action.methodName && params.recordId) {
    return {
      kind: 'record_button',
      model: action.targetModel || params.modelName,
      recordId: params.recordId,
      methodName: action.methodName,
      buttonType: action.kind === 'server' ? 'server' : 'object',
      context: action.context,
      refreshPolicy: action.refreshPolicy,
    };
  }
  return { kind: 'unsupported' };
}
