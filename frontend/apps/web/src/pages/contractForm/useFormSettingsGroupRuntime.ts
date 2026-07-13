import type { Ref } from 'vue';
import type { FieldDescriptor } from '@sc/schema';
import type { NativeFormLayoutNode } from '../../components/template/NativeFormTreeRenderer.vue';
import {
  fieldGroupTitleMatches,
  normalizeFieldGroupTitle,
} from './formConfigHelpers';
import { nativeFieldLabel } from './nativeLayoutUtils';
import type { FormConfigAuditResult } from './types';

export function useFormSettingsGroupRuntime(params: {
  busy: () => boolean;
  nativeFormLayoutNodes: () => NativeFormLayoutNode[];
  contractFields: () => Record<string, FieldDescriptor>;
  currentOrderedFieldKeys: () => string[];
  effectiveFieldGroupTitle: (fieldKey: string) => string;
  formDesignFieldLabel: (fieldKey: string) => string;
  contractFieldLabel: (fieldKey: string) => string;
  fieldGroupDraft: Record<string, string>;
  selectedGroupTitleDraft: Ref<string>;
  selectedGroupTitleEdit: Ref<string>;
  formConfigAuditResult: Ref<FormConfigAuditResult | null>;
  contractModeFeedback: Ref<string>;
  appendOperation: (action: string, summary: string) => void;
}) {
  function fieldsInNativeGroup(groupTitle: string) {
    const out = new Map<string, string>();
    const targetTitle = String(groupTitle || '').trim();
    const walk = (nodes: NativeFormLayoutNode[], activeGroup = '') => {
      nodes.forEach((node) => {
        const type = String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
        const title = String(node?.string || node?.label || '').trim();
        const nextGroup = title && ['group', 'page'].includes(type) ? title : activeGroup;
        const name = String(node?.name || '').trim();
        if (type === 'field' && name && nextGroup === targetTitle) {
          const descriptor = params.contractFields()[name];
          out.set(name, nativeFieldLabel(node, descriptor, params.contractFieldLabel));
        }
        (['children', 'pages', 'tabs', 'nodes', 'items'] as const).forEach((key) => {
          const children = node?.[key];
          if (Array.isArray(children)) walk(children as NativeFormLayoutNode[], nextGroup);
        });
      });
    };
    walk(params.nativeFormLayoutNodes());
    return Array.from(out.entries()).map(([fieldKey, label]) => ({ fieldKey, label }));
  }

  function fieldsInConfiguredGroup(groupTitle: string) {
    const targetTitle = normalizeFieldGroupTitle(groupTitle);
    if (!targetTitle) return [];
    const rows = params.currentOrderedFieldKeys()
      .filter((fieldKey) => fieldGroupTitleMatches(params.effectiveFieldGroupTitle(fieldKey), targetTitle))
      .map((fieldKey) => ({ fieldKey, label: params.formDesignFieldLabel(fieldKey) }));
    return rows.length ? rows : fieldsInNativeGroup(targetTitle);
  }

  async function onContractInlineGroupRename(payload: { oldTitle: string; newTitle: string }) {
    const oldTitle = String(payload.oldTitle || '').trim();
    const newTitle = String(payload.newTitle || '').trim();
    if (!oldTitle || !newTitle || oldTitle === newTitle || params.busy()) return;
    const fields = fieldsInConfiguredGroup(oldTitle);
    if (!fields.length) return;
    fields.forEach((row) => {
      params.fieldGroupDraft[row.fieldKey] = newTitle;
    });
    params.selectedGroupTitleDraft.value = newTitle;
    params.selectedGroupTitleEdit.value = newTitle;
    params.formConfigAuditResult.value = null;
    params.appendOperation('修改分组名称', `${oldTitle} 改为 ${newTitle}`);
    params.contractModeFeedback.value = '分组名称已调整，保存表单设置后生效';
  }

  return {
    fieldsInConfiguredGroup,
    fieldsInNativeGroup,
    onContractInlineGroupRename,
  };
}
