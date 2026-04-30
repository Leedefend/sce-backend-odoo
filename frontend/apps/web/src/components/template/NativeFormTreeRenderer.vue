<template>
  <div class="native-form-tree">
    <template v-for="(node, index) in visibleNodes" :key="nodeKey(node, index)">
      <section v-if="isContainerNode(node)" :class="containerClass(node)">
        <header v-if="containerTitle(node)" class="native-container-head">
          <h3>{{ containerTitle(node) }}</h3>
        </header>
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
              :columns="columns"
              @field-change="emit('field-change', $event)"
              @native-action="emit('native-action', $event)"
            >
              <template #readonly="{ field }">
                <slot name="readonly" :field="field" />
              </template>
              <template #fallback="{ field }">
                <slot name="fallback" :field="field" />
              </template>
              <template #chatter="{ node: chatterNode }">
                <slot name="chatter" :node="chatterNode" />
              </template>
            </NativeFormTreeRenderer>
          </div>
        </template>

        <template v-else>
          <FormSection
            v-if="fieldSchemasForNodes(fieldChildren(node)).length"
            :title="fieldSectionTitle(node)"
            :columns="columns"
            :fields="fieldSchemasForNodes(fieldChildren(node))"
            tone="core"
            @field-change="emit('field-change', $event)"
          >
            <template #readonly="{ field }">
              <slot name="readonly" :field="field" />
            </template>
            <template #fallback="{ field }">
              <slot name="fallback" :field="field" />
            </template>
          </FormSection>
          <div v-if="buttonChildren(node).length" :class="nativeActionsClass(node)">
            <button
              v-for="(buttonNode, buttonIndex) in buttonChildren(node)"
              :key="nodeKey(buttonNode, buttonIndex)"
              type="button"
              :class="nativeActionButtonClass(buttonNode)"
              @click="emitNativeAction(buttonNode)"
            >
              <span v-if="buttonIcon(buttonNode)" :class="['native-action-icon', buttonIcon(buttonNode)]" aria-hidden="true" />
              <span class="native-action-label">{{ buttonLabel(buttonNode) }}</span>
            </button>
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
            :columns="columns"
            @field-change="emit('field-change', $event)"
            @native-action="emit('native-action', $event)"
          >
            <template #readonly="{ field }">
              <slot name="readonly" :field="field" />
            </template>
            <template #fallback="{ field }">
              <slot name="fallback" :field="field" />
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
        :columns="columns"
        :fields="fieldSchemasForNodes([node])"
        tone="core"
        @field-change="emit('field-change', $event)"
      >
        <template #readonly="{ field }">
          <slot name="readonly" :field="field" />
        </template>
        <template #fallback="{ field }">
          <slot name="fallback" :field="field" />
        </template>
      </FormSection>

      <div v-else-if="nodeType(node) === 'button'" :class="nativeActionsClass(node)">
        <button type="button" :class="nativeActionButtonClass(node)" @click="emitNativeAction(node)">
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
import type { FormSectionFieldChange, FormSectionFieldSchema } from './formSection.types';

defineOptions({ name: 'NativeFormTreeRenderer' });

export type NativeFormLayoutNode = {
  type?: string;
  name?: string;
  string?: string;
  label?: string;
  text?: string;
  widget?: string;
  attributes?: Record<string, unknown>;
  buttonType?: string;
  action?: Record<string, unknown> | null;
  children?: NativeFormLayoutNode[];
  pages?: NativeFormLayoutNode[];
  tabs?: NativeFormLayoutNode[];
  nodes?: NativeFormLayoutNode[];
  items?: NativeFormLayoutNode[];
};

const props = withDefaults(defineProps<{
  nodes: NativeFormLayoutNode[];
  fieldSchemasForNodes: (nodes: NativeFormLayoutNode[]) => FormSectionFieldSchema[];
  isNodeVisible?: (node: NativeFormLayoutNode) => boolean;
  columns?: 1 | 2;
}>(), {
  columns: 2,
  isNodeVisible: () => true,
});

const emit = defineEmits<{
  (event: 'field-change', payload: FormSectionFieldChange): void;
  (event: 'native-action', payload: Record<string, unknown>): void;
}>();

const activePageIndex = ref(0);
const visibleNodes = computed(() => (props.nodes || []).filter((node) => isNodeVisible(node)));

function isNodeVisible(node: NativeFormLayoutNode) {
  return props.isNodeVisible(node);
}

function nodeType(node: NativeFormLayoutNode) {
  return String(node?.type || '').trim().toLowerCase();
}

function nodeKey(node: NativeFormLayoutNode, index: number) {
  return `${nodeType(node) || 'node'}-${String(node?.name || node?.string || node?.label || index)}`;
}

function containerTitle(node: NativeFormLayoutNode) {
  return String(node?.string || node?.label || '').trim();
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
  return rawChildren(node).filter((child) => nodeType(child) === 'field' && isNodeVisible(child));
}

function buttonChildren(node: NativeFormLayoutNode) {
  return rawChildren(node).filter((child) => nodeType(child) === 'button' && isNodeVisible(child));
}

function widgetChildren(node: NativeFormLayoutNode) {
  return rawChildren(node).filter((child) => nodeType(child) === 'widget' && isNodeVisible(child));
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

function fieldSectionTitle(node: NativeFormLayoutNode) {
  const title = containerTitle(node);
  if (title) return title;
  return '';
}

function containerClass(node: NativeFormLayoutNode) {
  return ['native-container', `native-container--${nodeType(node) || 'node'}`];
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

function nativeActionsClass(node: NativeFormLayoutNode) {
  const smart = isButtonBoxNode(node) || buttonChildren(node).some((child) => isSmartButtonNode(child));
  return ['native-actions', { 'native-actions--smart': smart }];
}

function nativeActionButtonClass(node: NativeFormLayoutNode) {
  return ['native-action-btn', { 'native-action-btn--smart': isSmartButtonNode(node) }];
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
  return String(node.label || node.string || node.name || '操作').trim();
}

function buttonIcon(node: NativeFormLayoutNode) {
  const actionIcon = String(nodeAction(node).icon || '').trim();
  const attrIcon = String(nodeAttributes(node).icon || '').trim();
  const raw = actionIcon || attrIcon;
  if (!raw) return '';
  return raw.startsWith('fa-') ? `fa ${raw}` : raw;
}

function emitNativeAction(node: NativeFormLayoutNode) {
  const action = node.action && typeof node.action === 'object'
    ? node.action
    : {
      name: node.name || '',
      label: buttonLabel(node),
      kind: String(node.buttonType || 'object') === 'action' ? 'open' : 'object',
      level: 'body',
      selection: 'none',
      payload: {
        method: String(node.buttonType || 'object') === 'object' ? node.name || '' : '',
        ref: String(node.buttonType || 'object') === 'action' ? node.name || '' : '',
        type: node.buttonType || 'object',
      },
    };
  emit('native-action', action);
}
</script>

<style scoped>
.native-form-tree {
  display: grid;
  gap: 14px;
  grid-column: 1 / -1;
}

.native-container {
  display: grid;
  gap: 12px;
  min-width: 0;
}

.native-container--header {
  border-bottom: 1px solid #eef2f7;
  padding-bottom: 12px;
}

.native-container--sheet {
  gap: 16px;
}

.native-container--group {
  border-top: 1px solid #f1f3f6;
  padding-top: 12px;
}

.native-container-head h3 {
  margin: 0;
  font-size: 14px;
  color: #374151;
  font-weight: 600;
}

.native-static-text {
  margin: 0;
  border-radius: 6px;
  background: #eef6ff;
  color: #1e3a5f;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.45;
}

.native-ribbon {
  justify-self: end;
  border-radius: 4px;
  background: #991b1b;
  color: #fff;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
}

.native-ribbon.text-bg-danger {
  background: #991b1b;
}

.native-tabs {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  border-bottom: 1px solid #e5e7eb;
}

.native-tab {
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: #475569;
  padding: 8px 10px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.native-tab--active {
  color: #111827;
  border-bottom-color: #111827;
  font-weight: 600;
}

.native-tab-panel {
  display: grid;
  gap: 14px;
}

.native-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.native-actions--smart {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(132px, 1fr));
  gap: 0;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
  background: #ffffff;
}

.native-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #1f2937;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.native-action-btn--smart {
  justify-content: flex-start;
  min-height: 54px;
  border: 0;
  border-right: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 0;
  padding: 8px 10px;
  color: #334155;
  background: #ffffff;
  font-weight: 500;
}

.native-action-icon {
  flex: 0 0 auto;
  width: 18px;
  text-align: center;
  color: #64748b;
}

.native-action-label {
  min-width: 0;
  overflow-wrap: anywhere;
}

.native-action-btn:hover {
  border-color: #64748b;
  background: #f8fafc;
}

.native-action-btn--smart:hover {
  border-color: #e5e7eb;
  background: #f8fafc;
  color: #111827;
}
</style>
