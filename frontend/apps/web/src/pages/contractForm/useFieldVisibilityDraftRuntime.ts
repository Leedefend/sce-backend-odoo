import type { Ref } from 'vue';
import type { FormConfigAuditResult } from './types';

export function useFieldVisibilityDraftRuntime(params: {
  fieldVisibilityDraft: Record<string, boolean>;
  fieldVisibilityDirty: Ref<boolean>;
  fieldVisibilityDirtyKeys: Record<string, boolean>;
  formConfigAuditResult: Ref<FormConfigAuditResult | null>;
  contractModeFeedback: Ref<string>;
  selectedFieldKey: () => string;
  suggestedHiddenRows: () => Array<{ fieldKey: string }>;
  formDesignFieldLabel: (fieldKey: string) => string;
  appendOperation: (action: string, summary: string) => void;
}) {
  function onFieldVisibilityDraftChange(fieldKey: string, value: string) {
    params.fieldVisibilityDraft[fieldKey] = value === 'show';
    params.fieldVisibilityDirtyKeys[fieldKey] = true;
    params.fieldVisibilityDirty.value = true;
    params.formConfigAuditResult.value = null;
    params.appendOperation(value === 'show' ? '显示字段' : '隐藏字段', `${params.formDesignFieldLabel(fieldKey)} 设置为${value === 'show' ? '显示' : '隐藏'}`);
    params.contractModeFeedback.value = '字段显示设置已调整，保存后生效';
  }

  function onSelectedFormSettingsFieldVisibilityChange(value: string) {
    const fieldKey = params.selectedFieldKey();
    if (!fieldKey) return;
    onFieldVisibilityDraftChange(fieldKey, value);
  }

  function hideSuggestedInternalFields() {
    const rows = params.suggestedHiddenRows();
    if (!rows.length) return;
    rows.forEach((row) => {
      params.fieldVisibilityDraft[row.fieldKey] = false;
      params.fieldVisibilityDirtyKeys[row.fieldKey] = true;
    });
    params.fieldVisibilityDirty.value = true;
    params.formConfigAuditResult.value = null;
    params.appendOperation('批量隐藏字段', `隐藏 ${rows.length} 个系统字段`);
    params.contractModeFeedback.value = `已标记隐藏 ${rows.length} 个系统字段，保存后生效`;
  }

  return {
    hideSuggestedInternalFields,
    onFieldVisibilityDraftChange,
    onSelectedFormSettingsFieldVisibilityChange,
  };
}
