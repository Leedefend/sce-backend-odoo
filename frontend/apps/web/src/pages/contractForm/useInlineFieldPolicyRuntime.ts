import type { Ref } from 'vue';
import { intentRequest } from '../../api/intents';
import { FORM_FIELD_CONFIG_INTENTS } from '../../app/businessConfigBoundaries';
import { normalizeFieldGroupTitle } from './formConfigHelpers';
import { applyFormRuntimeStatusEvent } from './runtimeStateApplier';
import type { BusyKind, FormConfigOperationLogEntry, UiStatus } from './types';

export function useInlineFieldPolicyRuntime(params: {
  busy: () => boolean;
  busyKind: Ref<BusyKind>;
  errorMessage: Ref<string>;
  status: Ref<UiStatus>;
  contractModeFeedback: Ref<string>;
  lowCodeApplyBaseParams: () => Record<string, unknown>;
  contractFieldSequence: (fieldKey: string) => number;
  formDesignFieldLabel: (fieldKey: string) => string;
  appendOperation: (action: string, summary: string, status?: FormConfigOperationLogEntry['status']) => void;
  reload: () => Promise<void>;
}) {
  async function setInlineFieldPolicy(fieldKey: string, policyParams: Record<string, unknown>) {
    const base = params.lowCodeApplyBaseParams();
    if (!fieldKey || params.busy()) return;
    const label = String(policyParams.label || '').trim();
    const groupTitle = normalizeFieldGroupTitle(policyParams.group_title);
    params.busyKind.value = 'action';
    try {
      await intentRequest({
        intent: FORM_FIELD_CONFIG_INTENTS.policySet,
        params: {
          ...base,
          field_name: fieldKey,
          sequence: params.contractFieldSequence(fieldKey),
          ...policyParams,
        },
        context: { view: 'form' },
      });
      if (label) {
        params.appendOperation('修改字段名称', `${params.formDesignFieldLabel(fieldKey)} 改为 ${label}`, 'done');
      }
      if (groupTitle) {
        params.appendOperation('移动分组', `${label || params.formDesignFieldLabel(fieldKey)} 移动到 ${groupTitle}`, 'done');
      }
      params.contractModeFeedback.value = '字段配置已更新';
      await params.reload();
    } catch (err) {
      applyFormRuntimeStatusEvent(params, {
        kind: 'status',
        transaction: 'inlinePolicy',
        status: 'error',
        errorMessage: err instanceof Error ? err.message : '字段显示规则更新失败',
      });
    } finally {
      params.busyKind.value = null;
    }
  }

  async function onContractInlineFieldLabelChange(payload: { field: { name?: unknown }; label: string }) {
    const fieldKey = String(payload.field.name || '').trim();
    const label = String(payload.label || '').trim();
    if (!fieldKey || !label) return;
    await setInlineFieldPolicy(fieldKey, { label });
  }

  return {
    onContractInlineFieldLabelChange,
    setInlineFieldPolicy,
  };
}
