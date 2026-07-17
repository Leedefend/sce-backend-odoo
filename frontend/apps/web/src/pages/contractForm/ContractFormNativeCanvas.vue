<template>
  <section v-if="showDefaultSectionTitle" class="native-default-section-head">
    <h3>基本信息</h3>
  </section>
  <section
    v-if="useNativeFormTree"
    class="contract-form-canvas-shell"
    data-form-canvas
    :class="{ 'contract-form-designer-canvas': designerMode }"
    aria-label="表单配置画布"
  >
    <header v-if="designerMode" class="contract-form-canvas-head">
      <div>
        <strong>表单画布</strong>
        <span>{{ selectedFieldRowLabel ? `正在编辑：${selectedFieldRowLabel}` : '点选字段后在右侧调整属性' }}</span>
      </div>
      <em>{{ rootColumns }} 栏布局</em>
    </header>
    <NativeFormTreeRenderer
      :key="layoutVisibilityRevision"
      class="contract-form-canvas-body"
      :nodes="layoutNodes"
      :field-schemas-for-nodes="fieldSchemasForNodes"
      :is-node-visible="isNodeVisible"
      :button-label-resolver="buttonLabelResolver"
      :native-action-handler="nativeActionHandler"
      :native-action-state-resolver="nativeActionStateResolver"
      :relation-adapter="relationAdapter"
      :field-actions="fieldActions"
      :field-order-editable="fieldOrderEditable"
      :field-order-index="fieldOrderIndex"
      :field-order-count="fieldOrderCount"
      :field-order-dragging-key="fieldOrderDraggingKey"
      :field-order-drop-target-key="fieldOrderDropTargetKey"
      :field-order-drop-placement="fieldOrderDropPlacement"
      :field-config-editable="fieldConfigEditable"
      :field-selection-mode="fieldSelectionMode"
      :selected-field-key="selectedFieldKey"
      :columns="rootColumns"
      @field-change="emit('field-change', $event)"
      @field-action="emit('field-action', $event)"
      @field-order-move="emit('field-order-move', $event)"
      @field-order-drag-start="emit('field-order-drag-start', $event)"
      @field-order-drag-over="emit('field-order-drag-over', $event)"
      @field-order-drag-leave="emit('field-order-drag-leave', $event)"
      @field-order-drop="emit('field-order-drop', $event)"
      @field-order-group-drop="emit('field-order-group-drop', $event)"
      @field-order-drag-end="emit('field-order-drag-end', $event)"
      @field-label-change="emit('field-label-change', $event)"
      @field-add-after="emit('field-add-after', $event)"
      @field-select="emit('field-select', $event)"
      @group-rename="emit('group-rename', $event)"
      @group-add-field="emit('group-add-field', $event)"
      @native-action="emit('native-action', $event)"
    >
      <template #readonly="{ field }">
        <span class="contract-readonly-value">
          <FieldValue :value="field.value" :field="field.descriptor" />
        </span>
      </template>
      <template #chatter>
        <NativeCollaborationPanel
          v-if="showCollaborationPanel"
          v-bind="collaborationPanelProps"
          v-on="collaborationPanelListeners"
        />
      </template>
    </NativeFormTreeRenderer>
  </section>
</template>

<script setup lang="ts">
import FieldValue from '../../components/FieldValue.vue';
import NativeFormTreeRenderer, { type NativeFormLayoutNode } from '../../components/template/NativeFormTreeRenderer.vue';
import type {
  FormSectionFieldAction,
  FormSectionFieldActionPayload,
  FormSectionFieldChange,
  FormSectionFieldSchema,
} from '../../components/template/formSection.types';
import type { RelationFieldAdapter } from '../../components/template/relationField.types';
import NativeCollaborationPanel, {
  type NativeCollaborationPanelListeners,
  type NativeCollaborationPanelProps,
} from './NativeCollaborationPanel.vue';

type NativeColumns = 1 | 2 | 3;
type FieldOrderPlacement = 'before' | 'after' | '';

defineProps<{
  showDefaultSectionTitle: boolean;
  useNativeFormTree: boolean;
  designerMode: boolean;
  selectedFieldRowLabel: string;
  rootColumns: NativeColumns;
  layoutVisibilityRevision: number;
  layoutNodes: NativeFormLayoutNode[];
  fieldSchemasForNodes: (nodes: NativeFormLayoutNode[]) => FormSectionFieldSchema[];
  isNodeVisible: (node: NativeFormLayoutNode) => boolean;
  buttonLabelResolver: (node: NativeFormLayoutNode) => string | undefined;
  nativeActionHandler: (payload: Record<string, unknown>) => void | Promise<void>;
  nativeActionStateResolver: (payload: Record<string, unknown>) => { disabled?: boolean; title?: string } | null | undefined;
  relationAdapter: RelationFieldAdapter;
  fieldActions: (field: FormSectionFieldSchema) => FormSectionFieldAction[];
  fieldOrderEditable: boolean;
  fieldOrderIndex: (field: FormSectionFieldSchema) => number;
  fieldOrderCount: number;
  fieldOrderDraggingKey: string;
  fieldOrderDropTargetKey: string;
  fieldOrderDropPlacement: FieldOrderPlacement;
  fieldConfigEditable: boolean;
  fieldSelectionMode: boolean;
  selectedFieldKey: string;
  showCollaborationPanel: boolean;
  collaborationPanelProps: NativeCollaborationPanelProps;
  collaborationPanelListeners: NativeCollaborationPanelListeners;
}>();

const emit = defineEmits<{
  'field-change': [payload: FormSectionFieldChange];
  'field-action': [payload: FormSectionFieldActionPayload];
  'field-order-move': [payload: { field: FormSectionFieldSchema; delta: number }];
  'field-order-drag-start': [payload: { field: FormSectionFieldSchema; event: DragEvent }];
  'field-order-drag-over': [payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: FieldOrderPlacement }];
  'field-order-drag-leave': [payload: { field: FormSectionFieldSchema; groupTitle?: string }];
  'field-order-drop': [payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: FieldOrderPlacement }];
  'field-order-group-drop': [payload: { groupTitle: string; groupIndex: number }];
  'field-order-drag-end': [payload: { field: FormSectionFieldSchema }];
  'field-label-change': [payload: { field: FormSectionFieldSchema; label: string }];
  'field-add-after': [payload: { field: FormSectionFieldSchema; groupTitle: string }];
  'field-select': [payload: { field: FormSectionFieldSchema; groupTitle: string }];
  'group-rename': [payload: { oldTitle: string; newTitle: string }];
  'group-add-field': [payload: { groupTitle: string }];
  'native-action': [payload: Record<string, unknown>];
}>();
</script>
