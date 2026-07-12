import { parseMaybeJsonRecord } from '../../app/contractRuntime';
import { dictOrEmpty } from './recordUtils';
import type { FieldDescriptor } from '@sc/schema';
import type { NativeStatusbarVm, StatusbarState } from './types';

export type NativeFormStatusbarInput = {
  recordId: number;
  formView: unknown;
  fields: Record<string, FieldDescriptor>;
  formData: Record<string, unknown>;
  mainData: Record<string, unknown>;
  fieldReadonly: (field: string) => boolean;
  readonly: boolean;
  fallback: NativeStatusbarVm;
};

export function workflowActionMethodAliases(key: string): string[] {
  const normalized = String(key || '').trim();
  if (normalized === 'submit') return ['action_submit', 'action_submit_progress', 'action_confirm', 'button_confirm'];
  if (normalized === 'approve') return ['action_approval_decision', 'validate_tier', 'action_approve', 'button_approve'];
  if (normalized === 'reject') return ['action_reject', 'reject_tier', 'button_reject'];
  if (normalized === 'activate') return ['action_set_running'];
  if (normalized === 'complete') {
    return [
      'action_done',
      'action_complete',
      'action_close',
      'action_paid',
      'action_received',
      'action_register',
      'action_reconcile',
      'button_done',
    ];
  }
  if (normalized === 'cancel') return ['action_cancel', 'button_cancel'];
  if (normalized === 'reopen') return ['action_reset_draft', 'button_draft'];
  return [];
}

export function normalizeWorkflowActionRows(
  workflow: Record<string, unknown>,
  modelName: string,
): Array<Record<string, unknown>> {
  const rows = Array.isArray(workflow.availableActions) ? workflow.availableActions : [];
  return rows
    .map((raw) => (raw && typeof raw === 'object' && !Array.isArray(raw) ? raw as Record<string, unknown> : null))
    .filter((row): row is Record<string, unknown> => Boolean(row))
    .map((row) => {
      const target = parseMaybeJsonRecord(row.target);
      const method = String(row.method || target.method || '').trim();
      const key = String(row.key || method || '').trim();
      return {
        key,
        label: String(row.label || key).trim() || key,
        kind: method ? 'object' : 'client',
        level: 'header',
        selection: 'none',
        intent: String(row.intent || '').trim(),
        allowed: row.enabled !== false,
        blocked_message: String(row.blocked_message || row.message || '').trim(),
        reason_code: String(row.reason_code || row.reasonCode || '').trim(),
        target_model: String(target.model || row.model || modelName || '').trim(),
        payload: {
          method,
          context_raw: target.context_raw,
        },
        target: {
          ...target,
          method,
        },
        visible_profiles: ['edit', 'readonly'],
        source_widget_id: 'workflow.contract',
        workflow_contract_action: true,
      };
    })
    .filter((row) => String(row.key || '').trim());
}

export function workflowActionRowForMethod(
  workflow: Record<string, unknown>,
  methodName: string,
): Record<string, unknown> | null {
  const method = String(methodName || '').trim();
  if (!method) return null;
  const rows = Array.isArray(workflow.availableActions) ? workflow.availableActions : [];
  for (const raw of rows) {
    const row = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw as Record<string, unknown> : null;
    if (!row) continue;
    const target = parseMaybeJsonRecord(row.target);
    const rowMethod = String(row.method || target.method || '').trim();
    const rowKey = String(row.key || '').trim();
    const aliases = workflowActionMethodAliases(rowKey);
    if (rowMethod === method || aliases.includes(method)) return row;
  }
  return null;
}

export function isWorkflowTransitionMethod(workflow: Record<string, unknown>, methodName: string) {
  const method = String(methodName || '').trim();
  if (workflowActionRowForMethod(workflow, method)) return true;
  return ['submit', 'approve', 'reject', 'activate', 'complete', 'cancel', 'reopen']
    .some((key) => workflowActionMethodAliases(key).includes(method));
}

export function normalizeWorkflowEvidenceGateRows(workflow: Record<string, unknown>) {
  const rows = Array.isArray(workflow.evidenceGate) ? workflow.evidenceGate : [];
  const seen = new Set<string>();
  return rows
    .map((raw) => (raw && typeof raw === 'object' && !Array.isArray(raw) ? raw as Record<string, unknown> : null))
    .filter((row): row is Record<string, unknown> => Boolean(row))
    .map((row, index) => {
      const reasonCode = String(row.reasonCode || row.reason_code || `workflow_gate_${index}`).trim();
      return {
        reasonCode,
        message: String(row.message || reasonCode).trim(),
        blocking: row.blocking !== false,
        severity: String(row.severity || '').trim(),
      };
    })
    .filter((row) => {
      if (!row.message || seen.has(row.reasonCode)) return false;
      seen.add(row.reasonCode);
      return true;
    });
}

export function normalizeWorkflowPhaseStatusbar(workflow: Record<string, unknown>): NativeStatusbarVm {
  const statusbar = dictOrEmpty(workflow.statusbar);
  const current = String(statusbar.current || '').trim();
  const states = Array.isArray(statusbar.states)
    ? statusbar.states
      .map((item) => dictOrEmpty(item))
      .map((item) => ({ value: String(item.value || '').trim(), label: String(item.label || item.value || '').trim() }))
      .filter((item) => item.value && item.label)
    : [];
  if (!current || !states.length) {
    return { visible: false, field: '', current: '', states: [], reachedValues: [], readonly: true };
  }
  const currentIndex = states.findIndex((item) => String(item.value) === current);
  return {
    visible: true,
    field: String(statusbar.field || '__workflow_phase').trim() || '__workflow_phase',
    current,
    states,
    reachedValues: currentIndex >= 0 ? states.slice(0, currentIndex).map((item) => String(item.value)) : [],
    readonly: true,
  };
}

export function normalizeNativeFormStatusbar(input: NativeFormStatusbarInput): NativeStatusbarVm {
  if (!input.recordId) {
    return { visible: false, field: '', current: '', states: [], reachedValues: [], readonly: true };
  }
  const formView = dictOrEmpty(input.formView);
  const raw = dictOrEmpty(formView.statusbar);
  const field = String(raw.field || '').trim();
  const descriptor = field ? input.fields[field] : undefined;
  const rawStates = Array.isArray(raw.states) ? raw.states as Array<Record<string, unknown>> : [];
  const selectionStates = Array.isArray(descriptor?.selection)
    ? descriptor.selection.map((item) => {
      const pair = item as unknown[];
      return { value: String(pair[0] ?? ''), label: String(pair[1] ?? pair[0] ?? '') };
    })
    : [];
  const states: StatusbarState[] = (rawStates.length
    ? rawStates.map((item) => ({ value: item.value as string | number, label: String(item.label || item.value || '') }))
    : selectionStates)
    .filter((item) => String(item.value ?? '').trim() && String(item.label || '').trim());
  const rawFormStatus = input.formData[field];
  const formStatusValue = rawFormStatus === false || rawFormStatus == null ? '' : String(rawFormStatus).trim();
  const current = String(
    formStatusValue
      || (Object.prototype.hasOwnProperty.call(input.mainData, field) ? input.mainData[field] : '')
      || '',
  ).trim();
  const currentIndex = states.findIndex((item) => String(item.value) === current);
  if (!field || !states.length) return input.fallback;
  return {
    visible: true,
    field,
    current,
    states,
    reachedValues: currentIndex >= 0 ? states.slice(0, currentIndex).map((item) => String(item.value)) : [],
    readonly: Boolean(input.fieldReadonly(field) || input.readonly),
  };
}
