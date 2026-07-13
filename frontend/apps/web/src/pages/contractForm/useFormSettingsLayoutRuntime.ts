import type { Ref } from 'vue';
import {
  normalizeLowCodeColumns,
  normalizeLowCodeFieldSize,
} from './fieldUtils';
import {
  lowCodeFieldSizeLabel,
  normalizeFieldGroupTitle,
} from './formConfigHelpers';
import type { FormConfigAuditResult, LowCodeFieldSize } from './types';

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
  currentGroupOptions: () => string[];
  groupNavigatorItems: () => Array<{ title: string }>;
  selectedGroupTitle: () => string;
  selectedFieldKey: () => string;
  effectiveGroupVisible: (key: string) => boolean;
  effectiveGroupColumns: (key: string) => LowCodeColumns;
  effectiveFieldSize: (fieldKey: string) => LowCodeFieldSize;
  formDesignFieldLabel: (fieldKey: string) => string;
  appendOperation: (action: string, summary: string) => void;
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

  return {
    onFormLayoutColumnsChange,
    onSelectedFormSettingsGroupVisibilityChange,
    onSelectedFormSettingsGroupColumnsChange,
    onSelectedFormSettingsFieldSizeChange,
  };
}
