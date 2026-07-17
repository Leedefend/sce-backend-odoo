/* eslint-disable vue/no-dupe-keys */
<template>
  <div class="native-form-tree">
    <template v-for="(node, index) in visibleNodes" :key="nodeKey(node, index)">
      <section
        v-if="isContainerNode(node)"
        :class="containerClass(node)"
        :data-group-title="containerPolicyTitle(node, index)"
        @dragover.prevent
        @drop.prevent.stop="emitGroupFieldOrderDrop(node, $event, index)"
        @mouseup.self="emitGroupFieldOrderPointerDrop(node, index)"
      >
        <header v-if="containerTitle(node)" class="native-container-head">
          <input
            v-if="fieldConfigEditable && isEditableGroupNode(node)"
            class="native-container-title-editor"
            type="text"
            :value="containerTitle(node)"
            :aria-label="`${containerTitle(node)}区域名称`"
            @change="emitGroupRename(node, ($event.target as HTMLInputElement).value)"
            @keydown.enter.prevent="emitGroupRename(node, ($event.target as HTMLInputElement).value)"
          />
          <h3 v-else>{{ containerTitle(node) }}</h3>
        </header>
        <div
          v-else-if="fieldOrderEditable && nodeType(node) === 'group'"
          class="native-container-drop-strip"
          :data-group-title="containerPolicyTitle(node, index)"
          data-drop-zone="field-group"
          @dragover.prevent.stop
          @drop.prevent.stop="emitGroupFieldOrderDrop(node, $event, index)"
          @mouseup.stop="emitGroupFieldOrderPointerDrop(node, index)"
        >
          <span v-if="fieldOrderDraggingKey">拖到这里加入此分组</span>
        </div>
        <p v-if="nodeText(node)" class="native-static-text">{{ nodeText(node) }}</p>

        <template v-if="nodeType(node) === 'notebook'">
          <div class="native-tabs">
            <button
              v-for="(page, pageIndex) in notebookPages(node)"
              :key="nodeKey(page, pageIndex)"
              type="button"
              class="native-tab"
              :class="{ 'native-tab--active': pageIndex === activePageIndex }"
              @click="activePageIndex = pageIndex"
            >
              {{ containerTitle(page) || `页签 ${pageIndex + 1}` }}
            </button>
          </div>
          <div class="native-tab-panel">
            <NativeFormTreeRenderer
              :nodes="activeNotebookChildren(node)"
              :field-schemas-for-nodes="fieldSchemasForNodes"
              :is-node-visible="isNodeVisible"
              :button-label-resolver="buttonLabelResolver"
              :native-action-handler="nativeActionHandler"
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
              :columns="nodeColumns(node)"
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
                <slot name="readonly" :field="field" />
              </template>
              <template #chatter="{ node: chatterNode }">
                <slot name="chatter" :node="chatterNode" />
              </template>
            </NativeFormTreeRenderer>
          </div>
        </template>

        <template v-else-if="nodeType(node) === 'h1' && titleFieldForNode(node)">
          <div class="native-title-row">
            <button
              v-if="titleFieldForNode(node)?.favoriteToggle"
              type="button"
              class="native-title-favorite"
              :class="{ 'native-title-favorite--active': titleFieldForNode(node)?.favoriteToggle?.active }"
              :aria-label="titleFieldForNode(node)?.favoriteToggle?.label"
              :aria-pressed="titleFieldForNode(node)?.favoriteToggle?.active"
              :title="titleFieldForNode(node)?.favoriteToggle?.label"
              :disabled="titleFieldForNode(node)?.favoriteToggle?.readonly"
              @click="emitTitleFavoriteToggle(titleFieldForNode(node))"
            >
              <ScIcon :name="titleFieldForNode(node)?.favoriteToggle?.active ? 'star' : 'star-outline'" :size="18" />
            </button>
            <input
              v-if="!titleFieldForNode(node)?.readonly"
              class="native-title-input"
              type="text"
              :value="titleFieldValue(titleFieldForNode(node))"
              :aria-label="titleFieldForNode(node)?.label"
              @input="emitTitleFieldChange(titleFieldForNode(node), ($event.target as HTMLInputElement).value)"
            />
            <h1 v-else class="native-title-text">{{ titleFieldValue(titleFieldForNode(node)) || titleFieldForNode(node)?.label }}</h1>
          </div>
          <NativeFormTreeRenderer
            v-if="containerChildren(node).length"
            :nodes="containerChildren(node)"
            :field-schemas-for-nodes="fieldSchemasForNodes"
            :is-node-visible="isNodeVisible"
            :button-label-resolver="buttonLabelResolver"
            :native-action-handler="nativeActionHandler"
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
            :columns="nodeColumns(node)"
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
              <slot name="readonly" :field="field" />
            </template>
            <template #chatter="{ node: chatterNode }">
              <slot name="chatter" :node="chatterNode" />
            </template>
          </NativeFormTreeRenderer>
        </template>

        <template v-else>
          <FormSection
            v-if="fieldSchemasForNodes(fieldChildren(node)).length"
            :title="fieldSectionTitle(node, index)"
            :columns="nodeColumns(node)"
            :fields="fieldSchemasForNodes(fieldChildren(node))"
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
            :field-group-title="containerPolicyTitle(node, index)"
            tone="core"
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
          >
            <template #readonly="{ field }">
              <slot name="readonly" :field="field" />
            </template>
          </FormSection>
          <div v-if="buttonChildren(node).length" :class="nativeActionsClass(node)">
            <button
              v-for="(buttonNode, buttonIndex) in visibleActionButtons(node)"
              :key="nodeKey(buttonNode, buttonIndex)"
              type="button"
              :class="nativeActionButtonClass(buttonNode)"
              :disabled="nativeActionDisabled(buttonNode)"
              :title="nativeActionTitle(buttonNode)"
              @click.stop.prevent="emitNativeAction(buttonNode)"
            >
              <span v-if="buttonIcon(buttonNode)" :class="['native-action-icon', buttonIcon(buttonNode)]" aria-hidden="true" />
              <span class="native-action-label">{{ buttonLabel(buttonNode) }}</span>
            </button>
            <div v-if="overflowActionButtons(node).length" class="native-action-more">
              <button
                type="button"
                class="native-action-btn native-action-btn--smart native-action-btn--more"
                :aria-expanded="isMoreOpen(node)"
                @click="toggleMore(node)"
              >
                <span class="native-action-label">更多</span>
              </button>
              <div v-if="isMoreOpen(node)" class="native-action-more-menu" role="menu">
                <button
                  v-for="(buttonNode, buttonIndex) in overflowActionButtons(node)"
                  :key="`more-${nodeKey(buttonNode, buttonIndex)}`"
                  type="button"
                  class="native-action-more-item"
                  role="menuitem"
                  :disabled="nativeActionDisabled(buttonNode)"
                  :title="nativeActionTitle(buttonNode)"
                  @click.stop.prevent="emitNativeAction(buttonNode); closeMore(node)"
                >
                  <span v-if="buttonIcon(buttonNode)" :class="['native-action-icon', buttonIcon(buttonNode)]" aria-hidden="true" />
                  <span class="native-action-label">{{ buttonLabel(buttonNode) }}</span>
                </button>
              </div>
            </div>
          </div>
          <template v-for="(widgetNode, widgetIndex) in widgetChildren(node)" :key="nodeKey(widgetNode, widgetIndex)">
            <div v-if="widgetName(widgetNode) === 'web_ribbon'" class="native-ribbon" :class="widgetClass(widgetNode)">
              {{ widgetTitle(widgetNode) }}
            </div>
          </template>
          <NativeFormTreeRenderer
            v-if="containerChildren(node).length"
            :nodes="containerChildren(node)"
            :field-schemas-for-nodes="fieldSchemasForNodes"
            :is-node-visible="isNodeVisible"
            :button-label-resolver="buttonLabelResolver"
            :native-action-handler="nativeActionHandler"
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
            :columns="nodeColumns(node)"
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
              <slot name="readonly" :field="field" />
            </template>
            <template #chatter="{ node: chatterNode }">
              <slot name="chatter" :node="chatterNode" />
            </template>
          </NativeFormTreeRenderer>
        </template>
      </section>

      <FormSection
        v-else-if="nodeType(node) === 'field' && fieldSchemasForNodes([node]).length"
        :title="fieldSectionTitle(node)"
        :columns="nodeColumns(node)"
        :fields="fieldSchemasForNodes([node])"
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
        tone="core"
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
      >
        <template #readonly="{ field }">
          <slot name="readonly" :field="field" />
        </template>
      </FormSection>

      <div v-else-if="nodeType(node) === 'button'" :class="nativeActionsClass(node)">
        <button
          type="button"
          :class="nativeActionButtonClass(node)"
          :disabled="nativeActionDisabled(node)"
          :title="nativeActionTitle(node)"
          @click.stop.prevent="emitNativeAction(node)"
        >
          <span v-if="buttonIcon(node)" :class="['native-action-icon', buttonIcon(node)]" aria-hidden="true" />
          <span class="native-action-label">{{ buttonLabel(node) }}</span>
        </button>
      </div>

      <div v-else-if="nodeType(node) === 'widget' && widgetName(node) === 'web_ribbon'" class="native-ribbon" :class="widgetClass(node)">
        {{ widgetTitle(node) }}
      </div>

      <slot v-else-if="nodeType(node) === 'chatter'" name="chatter" :node="node" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import FormSection from './FormSection.vue';
import ScIcon from '../design-system/ScIcon.vue';
import type {
  FormSectionFieldAction,
  FormSectionFieldActionPayload,
  FormSectionFieldChange,
  FormSectionFieldSchema,
} from './formSection.types';
import type { RelationFieldAdapter } from './relationField.types';

defineOptions({ name: 'NativeFormTreeRenderer' });

export type NativeFormLayoutNode = {
  type?: string;
  containerType?: string;
  name?: string;
  string?: string;
  label?: string;
  displayLabel?: string;
  semanticTitle?: string;
  text?: string;
  cols?: number;
  columns?: number;
  widget?: string;
  visible?: boolean;
  class?: string;
  className?: string;
  field_size?: string;
  fieldSize?: string;
  size?: string;
  attributes?: Record<string, unknown>;
  fieldInfo?: Record<string, unknown>;
  field_info?: Record<string, unknown>;
  buttonType?: string;
  action?: Record<string, unknown> | null;
  modifiers?: Record<string, unknown>;
  invisible?: unknown;
  readonly?: unknown;
  required?: unknown;
  children?: NativeFormLayoutNode[];
  pages?: NativeFormLayoutNode[];
  tabs?: NativeFormLayoutNode[];
  nodes?: NativeFormLayoutNode[];
  items?: NativeFormLayoutNode[];
  widgetList?: NativeFormLayoutNode[];
};

const props = withDefaults(defineProps<{
  nodes: NativeFormLayoutNode[];
  fieldSchemasForNodes: (nodes: NativeFormLayoutNode[]) => FormSectionFieldSchema[];
  isNodeVisible?: (node: NativeFormLayoutNode) => boolean;
  buttonLabelResolver?: (node: NativeFormLayoutNode) => string | undefined;
  nativeActionHandler?: (payload: Record<string, unknown>) => void | Promise<void>;
  nativeActionStateResolver?: (payload: Record<string, unknown>) => { disabled?: boolean; title?: string } | null | undefined;
  relationAdapter?: RelationFieldAdapter;
  fieldActions?: (field: FormSectionFieldSchema) => FormSectionFieldAction[];
  fieldOrderEditable?: boolean;
  fieldOrderIndex?: (field: FormSectionFieldSchema) => number;
  fieldOrderCount?: number;
  fieldOrderDraggingKey?: string;
  fieldOrderDropTargetKey?: string;
  fieldOrderDropPlacement?: 'before' | 'after' | '';
  fieldConfigEditable?: boolean;
  fieldSelectionMode?: boolean;
  selectedFieldKey?: string;
  columns?: 1 | 2 | 3;
}>(), {
  columns: 2,
  isNodeVisible: () => true,
  nativeActionHandler: undefined,
  nativeActionStateResolver: undefined,
  relationAdapter: undefined,
  fieldActions: undefined,
  fieldOrderEditable: false,
  fieldOrderIndex: undefined,
  fieldOrderCount: 0,
  fieldOrderDraggingKey: '',
  fieldOrderDropTargetKey: '',
  fieldOrderDropPlacement: '',
  fieldConfigEditable: false,
  fieldSelectionMode: false,
  selectedFieldKey: '',
});

const emit = defineEmits<{
  (event: 'field-change', payload: FormSectionFieldChange): void;
  (event: 'field-action', payload: FormSectionFieldActionPayload): void;
  (event: 'field-order-move', payload: { field: FormSectionFieldSchema; delta: number }): void;
  (event: 'field-order-drag-start', payload: { field: FormSectionFieldSchema; event: DragEvent }): void;
  (event: 'field-order-drag-over', payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: 'before' | 'after' | '' }): void;
  (event: 'field-order-drag-leave', payload: { field: FormSectionFieldSchema; groupTitle?: string }): void;
  (event: 'field-order-drop', payload: { field: FormSectionFieldSchema; groupTitle?: string; placement?: 'before' | 'after' | '' }): void;
  (event: 'field-order-group-drop', payload: { groupTitle: string; groupIndex: number }): void;
  (event: 'field-order-drag-end', payload: { field: FormSectionFieldSchema }): void;
  (event: 'field-label-change', payload: { field: FormSectionFieldSchema; label: string }): void;
  (event: 'field-add-after', payload: { field: FormSectionFieldSchema; groupTitle: string }): void;
  (event: 'field-select', payload: { field: FormSectionFieldSchema; groupTitle: string }): void;
  (event: 'group-rename', payload: { oldTitle: string; newTitle: string }): void;
  (event: 'group-add-field', payload: { groupTitle: string }): void;
  (event: 'native-action', payload: Record<string, unknown>): void;
}>();

const activePageIndex = ref(0);
const openMoreKeys = ref<Record<string, boolean>>({});
const SMART_BUTTON_DIRECT_LIMIT = 4;
const visibleNodes = computed(() => (props.nodes || []).filter((node) => isNodeRenderable(node)));

function isNodeRenderable(node: NativeFormLayoutNode) {
  return props.isNodeVisible(node);
}

function nodeType(node: NativeFormLayoutNode) {
  return String(node?.type || (node as { containerType?: string })?.containerType || '').trim().toLowerCase();
}

function nodeKey(node: NativeFormLayoutNode, index: number) {
  return `${nodeType(node) || 'node'}-${String(node?.name || node?.string || node?.label || index)}`;
}

function containerTitle(node: NativeFormLayoutNode) {
  const type = nodeType(node);
  if (type === 'group') return '';
  const raw = String(node?.string || node?.label || '').trim();
  if (!raw) return '';
  const structural = new Set(['header', 'sheet', 'container', 'div', 'span', 'h1', 'h2', 'h3']);
  if (structural.has(type)) return '';
  const lowered = raw.toLowerCase();
  if (structural.has(lowered) || lowered === type) return '';
  return raw;
}

function isReadablePolicyTitle(value: unknown) {
  const text = String(value || '').trim();
  if (!text) return false;
  if (['group', 'page', 'notebook', 'sheet', 'container'].includes(text.toLowerCase())) return false;
  if (/^[a-z][a-z0-9_:. -]*$/i.test(text) && /[_:.]/.test(text)) return false;
  return true;
}

function containerPolicyTitle(node: NativeFormLayoutNode, index = 0) {
  const raw = String(node?.string || node?.label || '').trim();
  if (isReadablePolicyTitle(raw)) return raw;
  if (nodeType(node) === 'group' && fieldChildren(node).length) return `默认分组 ${index + 1}`;
  return '';
}

function nodeText(node: NativeFormLayoutNode) {
  return String(node?.text || '').trim();
}

function isContainerNode(node: NativeFormLayoutNode) {
  return ['header', 'sheet', 'group', 'notebook', 'page', 'container', 'div', 'span', 'h1', 'h2', 'h3'].includes(nodeType(node));
}

function rawChildren(node: NativeFormLayoutNode) {
  const rows: NativeFormLayoutNode[] = [];
  for (const key of ['children', 'pages', 'tabs', 'nodes', 'items'] as const) {
    const value = node?.[key];
    if (Array.isArray(value)) rows.push(...value);
  }
  return rows;
}

function fieldChildren(node: NativeFormLayoutNode) {
  return rawChildren(node).filter((child) => nodeType(child) === 'field' && isNodeRenderable(child));
}

function titleFieldForNode(node: NativeFormLayoutNode) {
  return props.fieldSchemasForNodes(fieldChildren(node))[0];
}

function titleFieldValue(field?: FormSectionFieldSchema) {
  if (!field) return '';
  return String(field.inputValue ?? field.value ?? '').trim();
}

function emitTitleFieldChange(field: FormSectionFieldSchema | undefined, value: string) {
  if (!field) return;
  emit('field-change', {
    name: field.name,
    type: field.type,
    widget: field.widget,
    value,
    descriptor: field.descriptor,
  });
}

function emitTitleFavoriteToggle(field: FormSectionFieldSchema | undefined) {
  const favorite = field?.favoriteToggle;
  if (!favorite || favorite.readonly) return;
  emit('field-change', {
    name: favorite.name,
    type: 'boolean',
    value: !favorite.active,
    descriptor: favorite.descriptor,
  });
}

function buttonChildren(node: NativeFormLayoutNode) {
  return rawChildren(node).filter((child) => nodeType(child) === 'button' && isNodeRenderable(child));
}

function visibleActionButtons(node: NativeFormLayoutNode) {
  const children = buttonChildren(node);
  if (!isSmartActionGroup(node)) return children;
  const smartButtons = children.filter((child) => isSmartButtonNode(child));
  if (smartButtons.length <= SMART_BUTTON_DIRECT_LIMIT) return children;
  let smartSeen = 0;
  return children.filter((child) => {
    if (!isSmartButtonNode(child)) return true;
    smartSeen += 1;
    return smartSeen <= SMART_BUTTON_DIRECT_LIMIT;
  });
}

function overflowActionButtons(node: NativeFormLayoutNode) {
  const children = buttonChildren(node);
  if (!isSmartActionGroup(node)) return [];
  const smartButtons = children.filter((child) => isSmartButtonNode(child));
  if (smartButtons.length <= SMART_BUTTON_DIRECT_LIMIT) return [];
  return smartButtons.slice(SMART_BUTTON_DIRECT_LIMIT);
}

function widgetChildren(node: NativeFormLayoutNode) {
  return rawChildren(node).filter((child) => nodeType(child) === 'widget' && isNodeRenderable(child));
}

function containerChildren(node: NativeFormLayoutNode) {
  return rawChildren(node).filter((child) => !['field', 'button', 'widget'].includes(nodeType(child)));
}

function notebookPages(node: NativeFormLayoutNode) {
  const pages = rawChildren(node).filter((child) => nodeType(child) === 'page');
  return pages.length ? pages : rawChildren(node);
}

function activeNotebookChildren(node: NativeFormLayoutNode) {
  const page = notebookPages(node)[activePageIndex.value] || notebookPages(node)[0];
  return page ? rawChildren(page) : [];
}

function fieldSectionTitle(node?: NativeFormLayoutNode, index = 0) {
  if (node && nodeType(node) === 'group') return containerPolicyTitle(node, index);
  const semanticTitle = String(node?.semanticTitle || '').trim();
  if (semanticTitle) return semanticTitle;
  return node ? containerTitle(node) : '';
}

function normalizeColumns(value: unknown): 1 | 2 | 3 {
  const columns = Number(value);
  if (columns === 1 || columns === 2 || columns === 3) return columns;
  return 2;
}

function nodeColumns(node?: NativeFormLayoutNode): 1 | 2 | 3 {
  const attrs = node ? nodeAttributes(node) : {};
  const layoutNode = node as { cols?: unknown; columns?: unknown } | undefined;
  return normalizeColumns(attrs.col ?? attrs.columns ?? layoutNode?.cols ?? layoutNode?.columns ?? props.columns);
}

function isEditableGroupNode(node: NativeFormLayoutNode) {
  return ['group', 'page'].includes(nodeType(node));
}

function emitGroupRename(node: NativeFormLayoutNode, rawTitle: string) {
  const oldTitle = containerTitle(node);
  const newTitle = String(rawTitle || '').trim();
  if (!props.fieldConfigEditable || !oldTitle || !newTitle || oldTitle === newTitle) return;
  emit('group-rename', { oldTitle, newTitle });
}

function emitGroupFieldOrderDrop(node: NativeFormLayoutNode, event: DragEvent, index = 0) {
  if (!props.fieldOrderEditable || !props.fieldOrderDraggingKey) return;
  const target = event.target;
  const targetElement = target as unknown as { closest?: (selector: string) => unknown };
  const closest = target && typeof targetElement.closest === 'function'
    ? targetElement.closest.bind(target)
    : null;
  if (closest?.('.field')) return;
  const groupTitle = containerPolicyTitle(node, index);
  if (!groupTitle) return;
  emit('field-order-group-drop', { groupTitle, groupIndex: index });
}

function emitGroupFieldOrderPointerDrop(node: NativeFormLayoutNode, index = 0) {
  if (!props.fieldOrderEditable || !props.fieldOrderDraggingKey) return;
  const groupTitle = containerPolicyTitle(node, index);
  if (!groupTitle) return;
  emit('field-order-group-drop', { groupTitle, groupIndex: index });
  emit('field-order-drag-end', { field: { name: props.fieldOrderDraggingKey } as FormSectionFieldSchema });
}

function containerClass(node: NativeFormLayoutNode) {
  return [
    'native-container',
    `native-container--${nodeType(node) || 'node'}`,
    {
      'native-container--config-hidden': props.fieldConfigEditable && nodeType(node) === 'group' && node.visible === false,
      'native-container--field-drop-target': Boolean(
        props.fieldOrderEditable
        && props.fieldOrderDraggingKey
        && containerPolicyTitle(node),
      ),
    },
  ];
}

function nodeAttributes(node: NativeFormLayoutNode) {
  return node?.attributes && typeof node.attributes === 'object' ? node.attributes : {};
}

function nodeClassList(node: NativeFormLayoutNode) {
  return String(nodeAttributes(node).class || '').split(/\s+/).map((item) => item.trim()).filter(Boolean);
}

function nodeHasClass(node: NativeFormLayoutNode, className: string) {
  return nodeClassList(node).includes(className);
}

function nodeAction(node: NativeFormLayoutNode) {
  return node.action && typeof node.action === 'object' ? node.action as Record<string, unknown> : {};
}

function isSmartButtonNode(node: NativeFormLayoutNode) {
  return String(nodeAction(node).level || '').trim().toLowerCase() === 'smart' || nodeHasClass(node, 'oe_stat_button');
}

function isButtonBoxNode(node: NativeFormLayoutNode) {
  return nodeHasClass(node, 'oe_button_box') || (nodeType(node) === 'button' && isSmartButtonNode(node));
}

function isSmartActionGroup(node: NativeFormLayoutNode) {
  return isButtonBoxNode(node) || buttonChildren(node).some((child) => isSmartButtonNode(child));
}

function nativeActionsClass(node: NativeFormLayoutNode) {
  const smart = isSmartActionGroup(node);
  return ['native-actions', { 'native-actions--smart': smart }];
}

function nativeActionButtonClass(node: NativeFormLayoutNode) {
  return ['native-action-btn', { 'native-action-btn--smart': isSmartButtonNode(node) }];
}

function nativeActionState(node: NativeFormLayoutNode) {
  return props.nativeActionStateResolver?.(node as Record<string, unknown>) || {};
}

function nativeActionDisabled(node: NativeFormLayoutNode) {
  return nativeActionState(node).disabled === true;
}

function nativeActionTitle(node: NativeFormLayoutNode) {
  return String(nativeActionState(node).title || '').trim();
}

function widgetName(node: NativeFormLayoutNode) {
  const attrs = nodeAttributes(node);
  return String(node?.widget || node?.name || attrs.name || '').trim();
}

function widgetTitle(node: NativeFormLayoutNode) {
  const attrs = nodeAttributes(node);
  return String(node?.label || node?.string || attrs.title || widgetName(node)).trim();
}

function widgetClass(node: NativeFormLayoutNode) {
  const attrs = nodeAttributes(node);
  return String(attrs.bg_color || '').trim();
}

function buttonLabel(node: NativeFormLayoutNode) {
  const action = node.action && typeof node.action === 'object' ? node.action as Record<string, unknown> : {};
  const resolved = props.buttonLabelResolver?.(node);
  return String(resolved || node.displayLabel || action.displayLabel || node.label || node.string || node.name || '操作').trim();
}

function buttonIcon(node: NativeFormLayoutNode) {
  const actionIcon = String(nodeAction(node).icon || '').trim();
  const attrIcon = String(nodeAttributes(node).icon || '').trim();
  const raw = actionIcon || attrIcon;
  if (!raw) return '';
  return raw.startsWith('fa-') ? `fa ${raw}` : raw;
}

function emitNativeAction(node: NativeFormLayoutNode) {
  if (nativeActionDisabled(node)) return;
  const buttonType = String(node.buttonType || 'object');
  const rawAction = node.action && typeof node.action === 'object' ? node.action : {};
  const rawPayload = rawAction.payload && typeof rawAction.payload === 'object' && !Array.isArray(rawAction.payload)
    ? rawAction.payload as Record<string, unknown>
    : {};
  const action = {
    ...rawAction,
    name: rawAction.name || node.name || '',
    label: rawAction.label || buttonLabel(node),
    kind: rawAction.kind || (buttonType === 'action' ? 'open' : 'object'),
    buttonType,
    level: rawAction.level || 'body',
    selection: rawAction.selection || 'none',
    payload: {
      ...rawPayload,
      method: rawPayload.method || (buttonType === 'object' ? node.name || '' : ''),
      ref: rawPayload.ref || (buttonType === 'action' ? node.name || '' : ''),
      type: rawPayload.type || buttonType,
    },
  };
  if (props.nativeActionHandler) {
    void props.nativeActionHandler(action);
    return;
  }
  emit('native-action', action);
}

function moreKey(node: NativeFormLayoutNode) {
  return nodeKey(node, 0);
}

function isMoreOpen(node: NativeFormLayoutNode) {
  return Boolean(openMoreKeys.value[moreKey(node)]);
}

function toggleMore(node: NativeFormLayoutNode) {
  const key = moreKey(node);
  openMoreKeys.value = {
    ...openMoreKeys.value,
    [key]: !openMoreKeys.value[key],
  };
}

function closeMore(node: NativeFormLayoutNode) {
  const key = moreKey(node);
  if (!openMoreKeys.value[key]) return;
  openMoreKeys.value = {
    ...openMoreKeys.value,
    [key]: false,
  };
}
</script>

<style scoped>
.native-form-tree {
  display: grid;
  gap: 14px;
  grid-column: 1 / -1;
  min-width: 0;
}

.native-container {
  display: grid;
  gap: 12px;
  min-width: 0;
  position: relative;
}

.native-container--header {
  border-bottom: 1px solid var(--sc-app-border);
  padding-bottom: 12px;
}

.native-container--sheet {
  gap: 16px;
}

.native-container--group {
  border-top: 1px solid var(--sc-app-border);
  padding-top: 14px;
}

.native-container--field-drop-target.native-container--group,
.native-container--field-drop-target.native-container--page {
  outline: 1px dashed var(--sc-semantic-surface-interactive);
  outline-offset: 4px;
}

.native-container--config-hidden {
  border-top-style: dashed;
  opacity: 0.72;
  background: color-mix(in srgb, var(--sc-app-muted-bg) 64%, transparent);
}

.native-container--group > .native-container-head {
  border-left: 3px solid var(--sc-app-accent);
  padding-left: 10px;
}

.native-container--group > .native-container-head h3 {
  font-size: 15px;
  line-height: 1.35;
}

.native-container-head h3 {
  margin: 0;
  font-size: 14px;
  color: var(--sc-app-text-primary);
  font-weight: 600;
}

.native-container-head {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.native-container-drop-strip {
  min-height: 44px;
  display: grid;
  place-items: center;
  border: 1px dashed transparent;
  border-radius: 6px;
  margin-bottom: 8px;
  color: var(--sc-app-text-muted);
  font-size: 12px;
  pointer-events: auto;
}

.native-container--field-drop-target > .native-container-drop-strip {
  border-color: var(--sc-semantic-surface-interactive);
  background: var(--sc-app-panel-muted);
}

.native-container-title-editor {
  min-width: 140px;
  max-width: 260px;
  height: 30px;
  border: 1px solid var(--sc-app-border);
  border-radius: 5px;
  background: var(--sc-app-input-bg);
  color: var(--sc-app-text-primary);
  padding: 4px 8px;
  font-size: 14px;
  font-weight: 600;
}

.native-static-text {
  margin: 0;
  border-radius: 6px;
  border: 1px solid var(--sc-app-info-border);
  background: var(--sc-app-info-bg);
  color: var(--sc-app-info-text);
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.45;
  overflow-wrap: anywhere;
}

.native-ribbon {
  justify-self: end;
  max-width: 100%;
  border-radius: 4px;
  background: var(--sc-app-danger-text);
  color: var(--sc-semantic-text-on-interactive);
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.native-ribbon.text-bg-danger {
  background: var(--sc-app-danger-text);
}

.native-tabs {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  max-width: 100%;
  border-bottom: 1px solid var(--sc-app-border);
  background: var(--sc-app-muted-bg);
  border-radius: 8px 8px 0 0;
  padding: 6px 6px 0;
}

.native-tab {
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--sc-app-text-secondary);
  padding: 8px 10px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.native-tab--active {
  color: var(--sc-app-text-primary);
  border-bottom-color: var(--sc-semantic-surface-interactive);
  background: var(--sc-app-panel);
  font-weight: 600;
}

.native-tab-panel {
  display: grid;
  gap: 14px;
  min-height: 260px;
  min-width: 0;
  align-content: start;
}

.native-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.native-actions--smart {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(104px, max-content));
  gap: 1px;
  border: 1px solid var(--sc-app-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--sc-app-border);
  width: fit-content;
  max-width: 100%;
}

.native-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: calc(var(--sc-component-button-height-sm) * 1px);
  border: 1px solid var(--sc-app-border);
  background: transparent;
  color: var(--sc-app-text-primary);
  padding: 4px 9px;
  border-radius: var(--sc-component-button-radius);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0;
  cursor: pointer;
  min-width: 0;
  max-width: 100%;
  white-space: nowrap;
  transition: background-color 120ms ease, border-color 120ms ease, color 120ms ease, box-shadow 120ms ease;
}

.native-action-btn--smart {
  justify-content: flex-start;
  min-height: 60px;
  border: 0;
  border-radius: 0;
  padding: 12px 14px;
  color: var(--sc-app-text-primary);
  background: var(--sc-app-panel);
  font-weight: 600;
  font-size: 14px;
}

.native-action-more {
  position: relative;
  display: inline-flex;
  min-width: 0;
  width: 100%;
}

.native-action-btn--more {
  width: 100%;
  justify-content: center;
}

.native-action-more-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 12;
  min-width: 160px;
  max-width: min(280px, 80vw);
  display: grid;
  gap: 2px;
  padding: 6px;
  background: var(--sc-app-panel);
  border: 1px solid var(--sc-app-border-strong);
  border-radius: 6px;
  box-shadow: var(--sc-semantic-shadow-modal);
}

.native-action-more-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border: 0;
  background: transparent;
  color: var(--sc-app-text-primary);
  padding: 8px 10px;
  border-radius: 5px;
  font: inherit;
  text-align: left;
  cursor: pointer;
  min-width: 0;
}

.native-action-more-item:hover {
  background: var(--sc-app-hover-bg);
}

.native-action-icon {
  flex: 0 0 auto;
  width: 18px;
  text-align: center;
  color: var(--sc-semantic-surface-interactive);
}

.native-action-label {
  min-width: 0;
  overflow-wrap: anywhere;
  line-height: 1.25;
  font-weight: inherit;
}

.native-action-btn:hover {
  background: var(--sc-app-hover-bg);
}

.native-action-btn:focus-visible {
  border-color: var(--sc-semantic-surface-interactive);
  box-shadow: 0 0 0 3px var(--sc-app-focus-ring);
  outline: none;
}

.native-action-btn:disabled {
  cursor: not-allowed;
  opacity: var(--sc-base-opacity-disabled);
}

.native-action-btn--smart:hover {
  background: var(--sc-app-hover-bg);
  color: var(--sc-app-text-primary);
}

.native-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.native-title-favorite {
  border: 0;
  background: transparent;
  color: var(--sc-semantic-text-muted);
  font-size: 27px;
  line-height: 1;
  padding: 0 2px;
  cursor: pointer;
}

.native-title-favorite--active {
  color: var(--sc-app-warning-text);
}

.native-title-favorite:disabled {
  cursor: default;
  opacity: 0.65;
}

.native-title-input {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  background: transparent;
  color: var(--sc-app-text-primary);
  font-size: 27px;
  font-weight: 600;
  line-height: 1.25;
  padding: 2px 0;
  letter-spacing: 0;
}

.native-title-input:focus {
  outline: none;
  box-shadow: inset 0 -2px 0 var(--sc-semantic-surface-interactive);
}

.native-title-text {
  margin: 0;
  color: var(--sc-app-text-primary);
  font-size: 27px;
  font-weight: 600;
  line-height: 1.25;
  overflow-wrap: anywhere;
}
</style>
