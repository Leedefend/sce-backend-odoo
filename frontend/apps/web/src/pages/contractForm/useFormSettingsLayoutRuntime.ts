import type { Ref } from 'vue';
import {
  normalizeLowCodeColumns,
  normalizeLowCodeFieldSize,
} from './fieldUtils';
import {
  lowCodeFieldSizeLabel,
  normalizeFieldGroupTitle,
} from './formConfigHelpers';
import type { FormConfigAuditResult, FormConfigOperationLogEntry, LowCodeFieldSize } from './types';

type LowCodeColumns = 1 | 2 | 3;

export function useFormSettingsLayoutRuntime(params: {
  formLayoutColumnsBase: Ref<LowCodeColumns>;
  formLayoutColumnsDraft: Ref<LowCodeColumns>;
  formLayoutDirty: Ref<boolean>;
  formConfigAuditResult: Ref<FormConfigAuditResult | null>;
  groupVisibilityBase: Ref<Record<string, boolean>>;
  groupVisibilityDraft: Record<string, boolean>;
  groupColumnsBase: Ref<Record<string, LowCodeColumns>>;
  groupColumnsDraft: Record<string, LowCodeColumns>;
  groupLayoutDirtyKeys: Record<string, boolean>;
  fieldSizeBase: Ref<Record<string, LowCodeFieldSize>>;
  fieldSizeDraft: Record<string, LowCodeFieldSize>;
  fieldLayoutDirtyKeys: Record<string, boolean>;
  fieldOrderDraft: Ref<string[]>;
  fieldOrderPreviewActive: Ref<boolean>;
  fieldGroupBase: Ref<Record<string, string>>;
  fieldGroupSavedBase: Ref<Record<string, string>>;
  fieldGroupDraft: Record<string, string>;
  fieldMoveTargetDraft: Record<string, string>;
  fieldVisibilityBase: Ref<Record<string, boolean>>;
  fieldVisibilityDraft: Record<string, boolean>;
  fieldVisibilityDirty: Ref<boolean>;
  fieldVisibilityDirtyKeys: Record<string, boolean>;
  contractModeFeedback: Ref<string>;
  currentDesignFieldKeys: () => string[];
  visibilityDraftFieldKeys: () => string[];
  baseFieldRows: () => Array<{ fieldKey: string; actions: Array<{ checked?: boolean; value?: string }> }>;
  currentGroupOptions: () => string[];
  groupNavigatorItems: () => Array<{ title: string }>;
  selectedGroupTitle: () => string;
  selectedFieldKey: () => string;
  effectiveGroupVisible: (key: string) => boolean;
  effectiveGroupColumns: (key: string) => LowCodeColumns;
  effectiveFieldSize: (fieldKey: string) => LowCodeFieldSize;
  formDesignFieldLabel: (fieldKey: string) => string;
  appendOperation: (action: string, summary: string, status?: FormConfigOperationLogEntry['status']) => void;
  markPendingOperations: (status: 'saved' | 'reverted') => void;
}) {
  function baseGroupVisible(key: string) {
    return Object.prototype.hasOwnProperty.call(params.groupVisibilityBase.value, key)
      ? params.groupVisibilityBase.value[key] !== false
      : true;
  }

  function draftGroupVisible(key: string, fallback = baseGroupVisible(key)) {
    return Object.prototype.hasOwnProperty.call(params.groupVisibilityDraft, key)
      ? params.groupVisibilityDraft[key] !== false
      : fallback;
  }

  function updateGroupLayoutDirty(key: string, columns: LowCodeColumns, visible = draftGroupVisible(key)) {
    const baseColumns = params.groupColumnsBase.value[key] || params.formLayoutColumnsBase.value;
    const baseVisible = baseGroupVisible(key);
    if (columns === baseColumns && visible === baseVisible) {
      delete params.groupLayoutDirtyKeys[key];
    } else {
      params.groupLayoutDirtyKeys[key] = true;
    }
  }

  function onFormLayoutColumnsChange(event: Event) {
    const target = event.target as HTMLSelectElement | null;
    const previousColumns = params.formLayoutColumnsDraft.value;
    const columns = normalizeLowCodeColumns(target?.value, params.formLayoutColumnsDraft.value);
    if (columns === params.formLayoutColumnsDraft.value) return;
    const groupTitles = new Set<string>();
    params.currentGroupOptions().forEach((title) => {
      const key = normalizeFieldGroupTitle(title);
      if (key) groupTitles.add(key);
    });
    params.groupNavigatorItems().forEach((item) => {
      const key = normalizeFieldGroupTitle(item.title);
      if (key) groupTitles.add(key);
    });
    Object.keys(params.groupColumnsBase.value).forEach((key) => {
      const normalized = normalizeFieldGroupTitle(key);
      if (normalized) groupTitles.add(normalized);
    });
    Object.keys(params.groupColumnsDraft).forEach((key) => {
      const normalized = normalizeFieldGroupTitle(key);
      if (normalized) groupTitles.add(normalized);
    });
    params.formLayoutColumnsDraft.value = columns;
    groupTitles.forEach((key) => {
      const baseColumns = params.groupColumnsBase.value[key] || previousColumns;
      const draftColumns = params.groupColumnsDraft[key] || baseColumns;
      if (draftColumns !== previousColumns) return;
      params.groupColumnsDraft[key] = columns;
      updateGroupLayoutDirty(key, columns, draftGroupVisible(key));
    });
    params.formLayoutDirty.value = columns !== params.formLayoutColumnsBase.value;
    params.formConfigAuditResult.value = null;
    params.appendOperation('调整页面列数', `页面调整为 ${columns} 栏`);
  }

  function onSelectedFormSettingsGroupVisibilityChange(value: string) {
    const key = normalizeFieldGroupTitle(params.selectedGroupTitle());
    if (!key) return;
    const visible = value !== 'hide';
    if (params.effectiveGroupVisible(key) === visible) return;
    params.groupVisibilityDraft[key] = visible;
    updateGroupLayoutDirty(
      key,
      params.groupColumnsDraft[key] || params.groupColumnsBase.value[key] || params.formLayoutColumnsBase.value,
      visible,
    );
    params.formConfigAuditResult.value = null;
    params.appendOperation(visible ? '显示分组' : '隐藏分组', `${key} 设置为${visible ? '显示' : '隐藏'}`);
  }

  function onSelectedFormSettingsGroupColumnsChange(event: Event) {
    const key = normalizeFieldGroupTitle(params.selectedGroupTitle());
    if (!key) return;
    const target = event.target as HTMLSelectElement | null;
    const columns = normalizeLowCodeColumns(target?.value, params.effectiveGroupColumns(key));
    if (params.effectiveGroupColumns(key) === columns) return;
    params.groupColumnsDraft[key] = columns;
    updateGroupLayoutDirty(key, columns, draftGroupVisible(key));
    params.formConfigAuditResult.value = null;
    params.appendOperation('调整分组列数', `${key} 调整为 ${columns} 栏`);
  }

  function onSelectedFormSettingsFieldSizeChange(event: Event) {
    const fieldKey = params.selectedFieldKey();
    if (!fieldKey) return;
    const target = event.target as HTMLSelectElement | null;
    const size = normalizeLowCodeFieldSize(target?.value);
    if (params.effectiveFieldSize(fieldKey) === size) return;
    params.fieldSizeDraft[fieldKey] = size;
    if (size === (params.fieldSizeBase.value[fieldKey] || 'normal')) {
      delete params.fieldLayoutDirtyKeys[fieldKey];
    } else {
      params.fieldLayoutDirtyKeys[fieldKey] = true;
    }
    params.formConfigAuditResult.value = null;
    params.appendOperation('调整字段尺寸', `${params.formDesignFieldLabel(fieldKey)} 设置为${lowCodeFieldSizeLabel(size)}`);
  }

  function resetContractFieldOrder() {
    params.fieldOrderDraft.value = params.currentDesignFieldKeys();
    params.fieldOrderPreviewActive.value = false;
    Object.keys(params.fieldGroupDraft).forEach((key) => delete params.fieldGroupDraft[key]);
    Object.keys(params.fieldMoveTargetDraft).forEach((key) => delete params.fieldMoveTargetDraft[key]);
    Object.entries({ ...params.fieldGroupBase.value, ...params.fieldGroupSavedBase.value }).forEach(([key, value]) => {
      if (value) params.fieldGroupDraft[key] = value;
    });
    params.formLayoutColumnsDraft.value = params.formLayoutColumnsBase.value;
    Object.keys(params.groupVisibilityDraft).forEach((key) => delete params.groupVisibilityDraft[key]);
    Object.entries(params.groupVisibilityBase.value).forEach(([key, value]) => {
      params.groupVisibilityDraft[key] = value;
    });
    Object.keys(params.groupColumnsDraft).forEach((key) => delete params.groupColumnsDraft[key]);
    Object.entries(params.groupColumnsBase.value).forEach(([key, value]) => {
      params.groupColumnsDraft[key] = value;
    });
    Object.keys(params.fieldSizeDraft).forEach((key) => delete params.fieldSizeDraft[key]);
    Object.entries(params.fieldSizeBase.value).forEach(([key, value]) => {
      params.fieldSizeDraft[key] = value;
    });
    params.formLayoutDirty.value = false;
    Object.keys(params.groupLayoutDirtyKeys).forEach((key) => delete params.groupLayoutDirtyKeys[key]);
    Object.keys(params.fieldLayoutDirtyKeys).forEach((key) => delete params.fieldLayoutDirtyKeys[key]);
    params.visibilityDraftFieldKeys().forEach((fieldKey) => {
      if (Object.prototype.hasOwnProperty.call(params.fieldVisibilityBase.value, fieldKey)) {
        params.fieldVisibilityDraft[fieldKey] = params.fieldVisibilityBase.value[fieldKey];
        return;
      }
      const row = params.baseFieldRows().find((item) => item.fieldKey === fieldKey);
      const selected = row?.actions.find((action) => Boolean(action.checked));
      params.fieldVisibilityDraft[fieldKey] = selected ? selected.value === 'show' : true;
    });
    params.fieldVisibilityDirty.value = false;
    Object.keys(params.fieldVisibilityDirtyKeys).forEach((key) => {
      delete params.fieldVisibilityDirtyKeys[key];
    });
    params.formConfigAuditResult.value = null;
    params.markPendingOperations('reverted');
    params.appendOperation('放弃表单调整', '撤销当前页面未保存的表单配置调整', 'done');
    params.contractModeFeedback.value = '';
  }

  return {
    onFormLayoutColumnsChange,
    onSelectedFormSettingsGroupVisibilityChange,
    onSelectedFormSettingsGroupColumnsChange,
    onSelectedFormSettingsFieldSizeChange,
    resetContractFieldOrder,
  };
}
