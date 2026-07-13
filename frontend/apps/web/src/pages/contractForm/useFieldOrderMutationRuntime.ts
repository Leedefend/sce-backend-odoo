import type { Ref } from 'vue';
import {
  moveFieldOrderByDelta,
  moveFieldOrderRelative,
  moveFieldOrderToGroupEnd,
  normalizeFieldGroupTitle,
} from './formConfigHelpers';
import type { FormConfigAuditResult } from './types';

export function useFieldOrderMutationRuntime(params: {
  isEditable: () => boolean;
  ensureDraftStartsFromCurrentLayout: () => void;
  fieldOrderDraft: Ref<string[]>;
  fieldOrderPreviewActive: Ref<boolean>;
  currentOrderedFieldKeys: () => string[];
  fieldGroupBase: Ref<Record<string, string>>;
  fieldGroupDraft: Record<string, string>;
  fieldMoveTargetDraft: Record<string, string>;
  selectedFieldKey: Ref<string>;
  selectedFieldLabel: Ref<string>;
  selectedGroupTitleDraft: Ref<string>;
  selectedGroupTitleEdit: Ref<string>;
  selectedOrderTargetKey: Ref<string>;
  selectedOrderPlacement: Ref<'before' | 'after'>;
  draggingFieldKey: Ref<string>;
  draggingFieldLabel: Ref<string>;
  formConfigAuditResult: Ref<FormConfigAuditResult | null>;
  formDesignFieldLabel: (fieldKey: string) => string;
  appendOperation: (action: string, summary: string) => void;
  resetDropTarget: () => void;
}) {
  function moveFieldOrderTo(
    sourceFieldKey: string,
    targetFieldKey: string,
    placement: 'before' | 'after' = 'before',
    operationAction = '拖拽排序',
  ) {
    params.ensureDraftStartsFromCurrentLayout();
    const draft = moveFieldOrderRelative(params.fieldOrderDraft.value, sourceFieldKey, targetFieldKey, placement);
    if (!draft) return false;
    params.fieldOrderDraft.value = draft;
    params.fieldOrderPreviewActive.value = true;
    params.formConfigAuditResult.value = null;
    params.appendOperation(
      operationAction,
      `${params.formDesignFieldLabel(sourceFieldKey)} 调整到 ${params.formDesignFieldLabel(targetFieldKey)} ${placement === 'after' ? '后' : '前'}`,
    );
    return true;
  }

  function moveFieldOrder(fieldKey: string, delta: number) {
    if (!params.isEditable()) return;
    params.ensureDraftStartsFromCurrentLayout();
    const draft = moveFieldOrderByDelta(params.fieldOrderDraft.value, fieldKey, delta);
    if (!draft) return;
    params.fieldOrderDraft.value = draft;
    params.fieldOrderPreviewActive.value = true;
    params.formConfigAuditResult.value = null;
  }

  function moveFieldToGroupEnd(fieldKey: string, groupTitle: string) {
    const sourceFieldKey = String(fieldKey || '').trim();
    if (!sourceFieldKey) return;
    params.ensureDraftStartsFromCurrentLayout();
    const moved = moveFieldOrderToGroupEnd({
      order: params.fieldOrderDraft.value,
      fieldKey: sourceFieldKey,
      groupTitle,
      resolveFieldGroupTitle: (key) => params.fieldGroupBase.value[key] || params.fieldGroupDraft[key],
    });
    if (!moved) return;
    params.fieldOrderDraft.value = moved.order;
    params.fieldOrderPreviewActive.value = true;
    params.fieldGroupDraft[sourceFieldKey] = moved.groupTitle;
    params.fieldMoveTargetDraft[sourceFieldKey] = moved.anchorFieldKey;
    params.selectedFieldKey.value = sourceFieldKey;
    params.selectedFieldLabel.value = params.draggingFieldLabel.value || params.formDesignFieldLabel(sourceFieldKey);
    params.selectedGroupTitleDraft.value = moved.groupTitle;
    params.selectedGroupTitleEdit.value = moved.groupTitle;
    params.formConfigAuditResult.value = null;
    params.appendOperation('移动分组', `${params.formDesignFieldLabel(sourceFieldKey)} 移动到 ${moved.groupTitle}`);
  }

  function moveSelectedFormSettingsFieldToGroup(groupTitle: string) {
    const fieldKey = params.selectedFieldKey.value;
    if (!fieldKey) return;
    moveFieldToGroupEnd(fieldKey, groupTitle);
  }

  function onSelectedFormSettingsFieldGroupMoveChange(event: Event) {
    const target = event.target;
    const targetInput = target as unknown as { value?: unknown };
    const value = target && typeof targetInput.value === 'string'
      ? targetInput.value
      : '';
    moveSelectedFormSettingsFieldToGroup(value);
  }

  function moveSelectedFormSettingsFieldToOrderTarget() {
    const fieldKey = params.selectedFieldKey.value;
    const targetFieldKey = params.selectedOrderTargetKey.value;
    if (!fieldKey || !targetFieldKey || fieldKey === targetFieldKey) return;
    const moved = moveFieldOrderTo(fieldKey, targetFieldKey, params.selectedOrderPlacement.value, '调整位置');
    if (!moved) return;
    const targetGroup = normalizeFieldGroupTitle(params.fieldGroupBase.value[targetFieldKey] || params.fieldGroupDraft[targetFieldKey]);
    if (targetGroup) {
      params.fieldGroupDraft[fieldKey] = targetGroup;
      params.fieldMoveTargetDraft[fieldKey] = targetFieldKey;
      params.selectedGroupTitleDraft.value = targetGroup;
      params.selectedGroupTitleEdit.value = targetGroup;
    }
    params.selectedFieldKey.value = fieldKey;
    params.selectedFieldLabel.value = params.formDesignFieldLabel(fieldKey);
  }

  function onFieldOrderDrop(targetFieldKey: string, targetGroupTitle = '', requestedPlacement?: 'before' | 'after' | '') {
    if (!params.isEditable() || !params.draggingFieldKey.value || params.draggingFieldKey.value === targetFieldKey) return;
    const sourceFieldKey = params.draggingFieldKey.value;
    const currentOrder = params.fieldOrderDraft.value.length ? params.fieldOrderDraft.value : params.currentOrderedFieldKeys();
    const sourceIndex = currentOrder.indexOf(sourceFieldKey);
    const targetIndex = currentOrder.indexOf(targetFieldKey);
    const placement = requestedPlacement || (sourceIndex >= 0 && targetIndex >= 0 && sourceIndex < targetIndex ? 'after' : 'before');
    moveFieldOrderTo(params.draggingFieldKey.value, targetFieldKey, placement, '拖拽排序');
    const normalizedTargetGroup = normalizeFieldGroupTitle(params.fieldGroupBase.value[targetFieldKey] || params.fieldGroupDraft[targetFieldKey] || targetGroupTitle);
    if (normalizedTargetGroup) {
      params.fieldGroupDraft[sourceFieldKey] = normalizedTargetGroup;
      params.fieldMoveTargetDraft[sourceFieldKey] = targetFieldKey;
      params.selectedGroupTitleDraft.value = normalizedTargetGroup;
    }
    params.selectedFieldKey.value = sourceFieldKey;
    params.selectedFieldLabel.value = params.draggingFieldLabel.value || params.formDesignFieldLabel(sourceFieldKey);
    params.resetDropTarget();
  }

  function onFieldOrderGroupDrop(groupTitle: string) {
    if (!params.isEditable() || !params.draggingFieldKey.value) return;
    moveFieldToGroupEnd(params.draggingFieldKey.value, groupTitle);
    params.resetDropTarget();
  }

  return {
    moveFieldOrder,
    moveFieldOrderTo,
    moveFieldToGroupEnd,
    moveSelectedFormSettingsFieldToGroup,
    moveSelectedFormSettingsFieldToOrderTarget,
    onSelectedFormSettingsFieldGroupMoveChange,
    onFieldOrderDrop,
    onFieldOrderGroupDrop,
  };
}
